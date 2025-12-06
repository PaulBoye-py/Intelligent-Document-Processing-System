from flask import Flask, render_template, request, jsonify
import json
import uuid
from datetime import datetime
import time
import random

app = Flask(__name__)

# Mock data storage (in-memory for demo)
mock_documents = []

@app.route('/')
def index():
    return render_template('enhanced-modern-index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        document_id = str(uuid.uuid4())
        
        # Simulate processing time
        time.sleep(2)
        
        # Mock extracted text based on file type
        if file.filename.lower().endswith('.pdf'):
            mock_text = "This is a sample PDF document. It contains important business information, financial data, and legal terms. The document has been processed using Amazon Textract OCR technology."
        elif file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            mock_text = "This is text extracted from an image document. The image contained printed text, handwritten notes, and various formatting elements that have been successfully recognized."
        else:
            mock_text = "Document processed successfully. Text extraction completed with high confidence scores."
        
        # Store mock document
        document = {
            'document_id': document_id,
            'filename': file.filename,
            'extracted_text': mock_text,
            'status': 'completed',
            'confidence_score': round(random.uniform(0.85, 0.98), 2),
            'upload_timestamp': datetime.utcnow().isoformat(),
            'word_count': len(mock_text.split()),
            'processing_time': round(random.uniform(1.5, 4.2), 1)
        }
        
        mock_documents.append(document)
        
        return jsonify({
            'status': 'completed',
            'document_id': document_id,
            'filename': file.filename,
            'text': mock_text[:500],
            'word_count': len(mock_text.split()),
            'confidence_score': document['confidence_score'],
            'processing_time': document['processing_time'],
            'message': 'Document processed successfully (Demo Mode)'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/status/<document_id>')
def get_status(document_id):
    try:
        # Find document in mock storage
        for doc in mock_documents:
            if doc['document_id'] == document_id:
                return jsonify(doc)
        
        return jsonify({'status': 'not_found'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/documents')
def documents():
    try:
        # Return last 20 documents
        return jsonify(mock_documents[-20:])
    except Exception as e:
        return jsonify([])

@app.route('/search', methods=['POST'])
def search_documents():
    try:
        query = request.json.get('query', '').lower()
        
        # Simple text search in mock documents
        results = []
        for doc in mock_documents:
            if (query in doc['filename'].lower() or 
                query in doc['extracted_text'].lower()):
                results.append({
                    '_source': doc,
                    '_score': random.uniform(0.5, 1.0)
                })
        
        return jsonify({
            'hits': results[:10],
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'hits': [], 'total': 0})

@app.route('/analytics')
def analytics():
    try:
        total_docs = len(mock_documents)
        
        if total_docs > 0:
            # Calculate analytics from mock data
            confidence_scores = [doc['confidence_score'] for doc in mock_documents]
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            processing_times = [doc.get('processing_time', 2.5) for doc in mock_documents]
            avg_processing_time = sum(processing_times) / len(processing_times)
            
            # Document types
            doc_types = {}
            for doc in mock_documents:
                ext = doc['filename'].split('.')[-1].lower()
                doc_types[ext] = doc_types.get(ext, 0) + 1
            
            return jsonify({
                'documents_by_type': {
                    'buckets': [{'key': k, 'doc_count': v} for k, v in doc_types.items()]
                },
                'confidence_distribution': {
                    'buckets': [{'key': round(avg_confidence, 2), 'doc_count': total_docs}]
                },
                'processing_time_avg': {
                    'value': round(avg_processing_time, 1)
                },
                'total_documents': total_docs,
                'avg_confidence': round(avg_confidence, 2)
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

if __name__ == '__main__':
    print("🚀 Starting AWS IDP Demo App...")
    print("📝 Note: Running in DEMO MODE (no AWS credentials required)")
    print("🌐 Open http://localhost:5000 in your browser")
    print("📁 You can upload PDF, JPG, PNG files to test the interface")
    app.run(debug=True, port=4000)