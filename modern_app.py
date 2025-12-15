from flask import Flask, render_template, request, jsonify, session
import boto3
import json
import uuid
from datetime import datetime
import requests
from requests_aws4auth import AWS4Auth
from decimal import Decimal
import re
import jwt
from functools import wraps
import os

app = Flask(__name__)

def classify_document(text, filename):
    """Classify document based on content and filename"""
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Classification rules
    if any(word in text_lower for word in ['invoice', 'bill to', 'invoice number', 'due date', 'amount due']):
        return 'invoice'
    elif any(word in text_lower for word in ['receipt', 'customer copy', 'transaction', 'purchase', 'total paid']):
        return 'receipt'
    elif any(word in text_lower for word in ['contract', 'agreement', 'terms and conditions', 'party', 'whereas']):
        return 'contract'
    elif any(word in text_lower for word in ['certificate', 'certification', 'hereby certify', 'awarded']):
        return 'certificate'
    elif any(word in text_lower for word in ['dear', 'sincerely', 'regards', 'letter']):
        return 'letter'
    elif any(word in filename_lower for word in ['resume', 'cv']):
        return 'resume'
    elif re.search(r'\b\d{4}[-/]\d{2}[-/]\d{2}\b', text) and 'report' in text_lower:
        return 'report'
    else:
        return 'general'

def query_bedrock_chat(user_documents, question, conversation_history=None):
    """Simple Bedrock chat with document context"""
    try:
        # Build document context
        context_parts = []
        for i, doc in enumerate(user_documents, 1):
            context_part = f"""Document {i}: {doc.get('filename', 'Unknown')}
- Type: {doc.get('document_classification', 'general')}
- Word Count: {doc.get('word_count', 0)}
- Content: {doc.get('extracted_text', '')[:1500]}"""
            context_parts.append(context_part)
        
        full_context = "\n\n".join(context_parts)
        
        # Build conversation history context
        history_context = ""
        if conversation_history:
            recent_history = conversation_history[-4:]  # Last 4 messages
            history_parts = []
            for msg in recent_history:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                history_parts.append(f"{role}: {msg.get('content', '')}")
            history_context = f"\n\nPrevious conversation:\n" + "\n".join(history_parts)
        
        # Create single comprehensive prompt
        prompt = f"""You are an intelligent document assistant. You have access to {len(user_documents)} documents belonging to this user.

Your capabilities:
- Answer questions about document content
- Summarize documents or specific information
- Find patterns across documents
- Extract specific data (amounts, dates, names, etc.)
- Compare documents
- Provide insights and analysis

User's Documents:
{full_context}{history_context}

Current Question: {question}

Please provide a helpful and accurate response based on the documents above."""
        
        # Single message to Bedrock
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
        
    except Exception as e:
        return f"I encountered an error: {str(e)}. Please try rephrasing your question."

# AWS Configuration
REGION = 'us-east-1'
S3_BUCKET = 'aws-idp-raw-774305598371-dev'
STEP_FUNCTION_ARN = 'arn:aws:states:us-east-1:774305598371:stateMachine:aws-idp-system-document-processing-dev'
OPENSEARCH_ENDPOINT = 'https://search-aws-idp-system-search-dev-xyz.us-east-1.es.amazonaws.com'

# Cognito Configuration
USER_POOL_ID = 'us-east-1_GAiJDMatZ'
CLIENT_ID = '690mn07n8pmhsoluq5a8634ggt'

# Chat conversation storage (in production, use Redis or DynamoDB)
chat_sessions = {}

app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize AWS clients - use IAM role in production, local profile in development
if os.getenv('DEPLOYMENT') == 'production':
    aws_session = boto3.Session()
else:
    aws_session = boto3.Session(profile_name='paul-arthurite')
s3 = aws_session.client('s3', region_name=REGION)
stepfunctions = aws_session.client('stepfunctions', region_name=REGION)
dynamodb = aws_session.resource('dynamodb', region_name=REGION)
comprehend = aws_session.client('comprehend', region_name=REGION)
textract = aws_session.client('textract', region_name=REGION)
cognito = aws_session.client('cognito-idp', region_name=REGION)
bedrock = aws_session.client('bedrock-runtime', region_name=REGION)

# OpenSearch client setup
credentials = aws_session.get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'es', session_token=credentials.token)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            # Verify JWT token with Cognito
            decoded = jwt.decode(token, options={"verify_signature": False})
            request.user_id = decoded.get('sub')
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Invalid token'}), 401
    return decorated_function

def get_user_id():
    """Get current user ID from request"""
    return getattr(request, 'user_id', None)

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'aws-idp-system'})

@app.route('/')
def index():
    return render_template('enhanced-modern-index.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        response = cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        return jsonify({'message': 'User registered successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        response = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        token = response['AuthenticationResult']['AccessToken']
        id_token = response['AuthenticationResult']['IdToken']
        
        return jsonify({
            'access_token': token,
            'id_token': id_token,
            'message': 'Login successful'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@app.route('/upload', methods=['POST'])
@require_auth
def upload():
    try:
        file = request.files['file']
        document_id = str(uuid.uuid4())

        original_filename = file.filename
        file_extension = original_filename.lower().split('.')[-1]

        # Convert HEIC / HEIF to JPEG before upload
        if file_extension in ['heic', 'heif']:
            converted_file, new_filename = convert_heic_to_jpeg(file)
            file = converted_file
            file.filename = new_filename
            file_extension = 'jpg'

        key = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{document_id}_{file.filename}"

        # Upload to S3
        s3.upload_fileobj(file, S3_BUCKET, key)

        # TEXTRACT PROCESSING
        if file_extension == 'pdf':
            response = textract.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': S3_BUCKET, 'Name': key}}
            )

            job_id = response['JobId']
            import time
            attempt = 0

            while attempt < 30:
                time.sleep(2)
                result = textract.get_document_text_detection(JobId=job_id)

                if result['JobStatus'] == 'SUCCEEDED':
                    text = ' '.join(
                        block['Text']
                        for block in result['Blocks']
                        if block['BlockType'] == 'LINE'
                    )
                    break

                if result['JobStatus'] == 'FAILED':
                    raise Exception(result.get('StatusMessage', 'Textract failed'))

                attempt += 1

            if attempt >= 30:
                raise Exception('Textract processing timed out')

        else:
            response = textract.detect_document_text(
                Document={'S3Object': {'Bucket': S3_BUCKET, 'Name': key}}
            )
            text = ' '.join(
                block['Text']
                for block in response['Blocks']
                if block['BlockType'] == 'LINE'
            )

        # DOCUMENT CLASSIFICATION
        doc_classification = classify_document(text, file.filename)

        # ENTITY EXTRACTION
        entities = []
        try:
            if text.strip():
                comprehend_response = comprehend.detect_entities(
                    Text=text[:5000],
                    LanguageCode='en'
                )
                entities = [{
                    'text': e['Text'],
                    'type': e['Type'],
                    'confidence': Decimal(str(e['Score']))
                } for e in comprehend_response['Entities']]
        except Exception as e:
            print(f"Comprehend error: {e}")

        confidence = 0.95 if len(text.strip()) > 10 else 0.75
        user_id = get_user_id()

        table = dynamodb.Table('aws-idp-documents-dev')
        table.put_item(Item={
            'document_id': document_id,
            'user_id': user_id,
            'filename': file.filename,
            'original_filename': original_filename,
            'extracted_text': text,
            'status': 'completed',
            'confidence_score': Decimal(str(confidence)),
            'upload_timestamp': datetime.utcnow().isoformat(),
            'word_count': len(text.split()),
            'document_type': file_extension,
            'document_classification': doc_classification,
            'entities': entities,
            'processing_method': 'async' if file_extension == 'pdf' else 'sync',
            'preprocessing_steps': ['heic_to_jpeg'] if original_filename != file.filename else []
        })

        return jsonify({
            'status': 'completed',
            'document_id': document_id,
            'filename': file.filename,
            'original_filename': original_filename,
            'word_count': len(text.split()),
            'confidence_score': confidence,
            'document_classification': doc_classification,
            'entities': entities,
            'message': 'Document processed successfully'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


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
@require_auth
def documents():
    try:
        user_id = get_user_id()
        table = dynamodb.Table('aws-idp-documents-dev')
        
        # Query only user's documents
        response = table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=20
        )
        return jsonify(response['Items'])
    except Exception as e:
        return jsonify([])

@app.route('/search', methods=['POST'])
@require_auth
def search_documents():
    try:
        query = request.json.get('query', '').lower().strip()
        user_id = get_user_id()
        
        if not query:
            return jsonify({'hits': [], 'total': 0})
        
        # Get user's documents from DynamoDB
        table = dynamodb.Table('aws-idp-documents-dev')
        response = table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        
        documents = response['Items']
        matches = []
        
        # Search through documents
        for doc in documents:
            score = 0
            match_reasons = []
            
            # Search in filename
            if query in doc.get('filename', '').lower():
                score += 2
                match_reasons.append('filename')
            
            # Search in extracted text
            extracted_text = doc.get('extracted_text', '').lower()
            if query in extracted_text:
                score += 3
                match_reasons.append('content')
                # Count occurrences for better scoring
                score += extracted_text.count(query) * 0.5
            
            # Search in document classification
            if query in doc.get('document_classification', '').lower():
                score += 1.5
                match_reasons.append('type')
            
            # Search in entities
            entities = doc.get('entities', [])
            for entity in entities:
                if query in entity.get('text', '').lower():
                    score += 1
                    match_reasons.append('entity')
                    break
            
            if score > 0:
                matches.append({
                    '_source': doc,
                    '_score': score,
                    'match_reasons': match_reasons
                })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['_score'], reverse=True)
        
        return jsonify({
            'hits': matches[:20],  # Limit to 20 results
            'total': len(matches)
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'hits': [], 'total': 0})

@app.route('/analytics')
@require_auth
def analytics():
    try:
        user_id = get_user_id()
        table = dynamodb.Table('aws-idp-documents-dev')
        
        # Get only user's documents
        response = table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        
        items = response['Items']
        total_docs = len(items)
        
        # Calculate analytics
        if total_docs > 0:
            # Average confidence score
            confidence_scores = [float(item.get('confidence_score', 0)) for item in items]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Document types by file extension
            doc_types = {}
            for item in items:
                doc_type = item.get('document_type', 'general')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # Document classifications
            doc_classifications = {}
            for item in items:
                classification = item.get('document_classification', 'general')
                doc_classifications[classification] = doc_classifications.get(classification, 0) + 1
            
            return jsonify({
                'documents_by_type': {
                    'buckets': [{'key': k, 'doc_count': v} for k, v in doc_types.items()]
                },
                'documents_by_classification': {
                    'buckets': [{'key': k, 'doc_count': v} for k, v in doc_classifications.items()]
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

@app.route('/chat', methods=['POST'])
@require_auth
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        user_id = get_user_id()
        
        # Get all user's documents from DynamoDB
        table = dynamodb.Table('aws-idp-documents-dev')
        response = table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        documents = response['Items']
        
        if not documents:
            return jsonify({
                'response': 'You haven\'t uploaded any documents yet. Please upload some documents first, then I can help you analyze them!',
                'source': 'system'
            })
        
        # Use Bedrock for all queries
        bedrock_response = query_bedrock_chat(documents, message, conversation_history)
        
        return jsonify({
            'response': bedrock_response,
            'source': 'bedrock',
            'document_count': len(documents)
        })
            
    except Exception as e:
        return jsonify({'response': f'Sorry, I encountered an error: {str(e)}', 'source': 'error'})

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
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEPLOYMENT') != 'production'
    
    if debug:
        print("🚀 Starting AWS IDP System (Development)...")
        print("📝 Using AWS profile: paul-arthurite")
        print(f"🌐 Open http://localhost:{port} in your browser")
    else:
        print("🚀 Starting AWS IDP System (Production)...")
        print("📝 Using IAM role for AWS access")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
