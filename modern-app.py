from flask import Flask, render_template, request, jsonify
import boto3
import json
import uuid
from datetime import datetime
import requests
from requests_aws4auth import AWS4Auth
from decimal import Decimal

app = Flask(__name__)

# AWS Configuration
REGION = 'us-east-1'
S3_BUCKET = 'aws-idp-raw-774305598371-dev'
STEP_FUNCTION_ARN = 'arn:aws:states:us-east-1:774305598371:stateMachine:aws-idp-system-document-processing-dev'
OPENSEARCH_ENDPOINT = 'https://search-aws-idp-system-search-dev-xyz.us-east-1.es.amazonaws.com'

# Initialize AWS clients
s3 = boto3.client('s3', region_name=REGION)
stepfunctions = boto3.client('stepfunctions', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
comprehend = boto3.client('comprehend', region_name=REGION)

# OpenSearch client setup
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'es', session_token=credentials.token)

@app.route('/')
def index():
    return render_template('enhanced-modern-index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        document_id = str(uuid.uuid4())
        key = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{document_id}_{file.filename}"
        
        # Upload to S3
        s3.upload_fileobj(file, S3_BUCKET, key)
        
        # Process with Textract directly (fallback without Step Functions)
        textract = boto3.client('textract', region_name=REGION)
        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': S3_BUCKET, 'Name': key}}
        )
        
        text = ' '.join([block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE'])
        
        # Store in DynamoDB
        table = dynamodb.Table('aws-idp-documents-dev')
        table.put_item(Item={
            'document_id': document_id,
            'filename': file.filename,
            'extracted_text': text,
            'status': 'completed',
            'confidence_score': Decimal('0.95'),
            'upload_timestamp': datetime.utcnow().isoformat(),
            'word_count': len(text.split())
        })
        
        return jsonify({
            'status': 'completed',
            'document_id': document_id,
            'filename': file.filename,
            'text': text[:500],
            'word_count': len(text.split()),
            'message': 'Document processed successfully'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/status/<document_id>')
def get_status(document_id):
    try:
        # Check DynamoDB for document status
        table = dynamodb.Table('aws-idp-documents-dev')
        response = table.get_item(Key={'document_id': document_id})
        
        if 'Item' in response:
            return jsonify(response['Item'])
        else:
            return jsonify({'status': 'not_found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/documents')
def documents():
    try:
        table = dynamodb.Table('aws-idp-documents-dev')
        response = table.scan(Limit=20)
        return jsonify(response['Items'])
    except Exception as e:
        return jsonify([])

@app.route('/search', methods=['POST'])
def search_documents():
    try:
        query = request.json.get('query', '')
        
        search_body = {
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['extracted_text', 'filename', 'entities.text']
                }
            },
            'size': 20
        }
        
        response = requests.post(
            f"{OPENSEARCH_ENDPOINT}/documents-general/_search",
            json=search_body,
            auth=awsauth,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'hits': data['hits']['hits'],
                'total': data['hits']['total']['value']
            })
        else:
            return jsonify({'error': 'Search failed', 'hits': [], 'total': 0})
        
    except Exception as e:
        return jsonify({'error': str(e), 'hits': [], 'total': 0})

@app.route('/analytics')
def analytics():
    try:
        # Get analytics from DynamoDB since OpenSearch may not be available
        table = dynamodb.Table('aws-idp-documents-dev')
        response = table.scan()
        
        items = response['Items']
        total_docs = len(items)
        
        # Calculate analytics
        if total_docs > 0:
            # Average confidence score
            confidence_scores = [float(item.get('confidence_score', 0)) for item in items]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Document types
            doc_types = {}
            for item in items:
                doc_type = item.get('document_type', 'general')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            return jsonify({
                'documents_by_type': {
                    'buckets': [{'key': k, 'doc_count': v} for k, v in doc_types.items()]
                },
                'confidence_distribution': {
                    'buckets': [{'key': avg_confidence, 'doc_count': total_docs}]
                },
                'processing_time_avg': {
                    'value': 2.5  # Mock processing time
                },
                'total_documents': total_docs,
                'avg_confidence': avg_confidence
            })
        else:
            return jsonify({
                'documents_by_type': {'buckets': []},
                'confidence_distribution': {'buckets': []},
                'processing_time_avg': {'value': 0},
                'total_documents': 0,
                'avg_confidence': 0
            })
        
    except Exception as e:
        return jsonify({'error': str(e), 'total_documents': 0})

@app.route('/human-review/<document_id>')
def human_review_status(document_id):
    try:
        # Check A2I human review status
        sagemaker = boto3.client('sagemaker', region_name=REGION)
        
        response = sagemaker.describe_human_loop(
            HumanLoopName=document_id
        )
        
        return jsonify({
            'status': response['HumanLoopStatus'],
            'creation_time': response['CreationTime'].isoformat(),
            'human_loop_name': response['HumanLoopName']
        })
        
    except Exception as e:
        return jsonify({'status': 'not_found', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)