# AWS Intelligent Document Processing (IDP) System

## 🚀 Overview

Production-ready AWS Intelligent Document Processing system that handles diverse document types including forms, invoices, medical records, contracts, and scanned documents. The system extracts text and structured data, enriches it with entity recognition, enables searchability, maintains audit trails, and incorporates human review for edge cases.

## ✨ Features

- **Multi-format Support**: PDF, JPG, PNG, TIFF document processing
- **Advanced OCR**: Amazon Textract for text, tables, and forms extraction
- **Entity Recognition**: Amazon Comprehend for intelligent data extraction
- **Search & Analytics**: OpenSearch integration with real-time analytics
- **Human Review**: Amazon A2I for quality assurance
- **Step Functions**: Orchestrated workflow with error handling
- **Modern Web UI**: React-style interface with real-time updates

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Web UI    │───▶│   Amazon S3  │───▶│ Step Functions  │
│   (Flask)   │    │   (Storage)  │    │ (Orchestration) │
└─────────────┘    └──────────────┘    └─────────────────┘
                                                │
                                                ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ OpenSearch  │◀───│  DynamoDB    │◀───│   Textract +    │
│ (Analytics) │    │  (Storage)   │    │   Comprehend    │
└─────────────┘    └──────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.9+
- AWS account with required services enabled

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd aws-intelligent-document-processing
```

2. **Install dependencies**
```bash
cd web-ui
pip install -r requirements.txt
```

3. **Configure AWS resources**
```bash
# Create DynamoDB table
python create-dynamodb-table.py

# Create Step Functions (optional)
python create-step-function.py
```

4. **Update configuration**
Edit `web-ui/modern-app.py` with your AWS resource ARNs:
```python
S3_BUCKET = 'your-s3-bucket-name'
STEP_FUNCTION_ARN = 'your-step-function-arn'
OPENSEARCH_ENDPOINT = 'your-opensearch-endpoint'
```

5. **Run the application**
```bash
python modern-app.py
```

Visit `http://localhost:5000` to access the web interface.

## 📁 Project Structure

```
├── web-ui/                     # Flask web application
│   ├── templates/              # HTML templates
│   ├── modern-app.py          # Main Flask application
│   └── requirements.txt       # Python dependencies
├── lambda/                    # AWS Lambda functions
│   ├── preprocessing/         # Image preprocessing
│   ├── textract-processor/    # Text extraction
│   ├── comprehend-processor/  # Entity recognition
│   └── data-store/           # Data storage
├── step-functions/           # Step Functions workflows
├── config/                   # Configuration files
├── architecture/            # Architecture diagrams
└── tests/                  # Test files
```

## 🔧 Configuration

### AWS Services Required
- **Amazon S3**: Document storage
- **Amazon Textract**: OCR and document analysis
- **Amazon Comprehend**: Entity recognition
- **DynamoDB**: Metadata storage
- **Step Functions**: Workflow orchestration
- **OpenSearch**: Search and analytics (optional)
- **Amazon A2I**: Human review (optional)

### Environment Variables
```bash
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name
DYNAMODB_TABLE=aws-idp-documents-dev
```

## 📊 Features

### Document Processing
- **Upload**: Drag & drop interface for multiple file types
- **Processing**: Real-time status updates during processing
- **Results**: Extracted text, confidence scores, and metadata
- **History**: Browse and search processed documents

### Analytics Dashboard
- **Document Metrics**: Total documents, processing times
- **Confidence Tracking**: Average confidence scores
- **Search**: Full-text search across all documents
- **Filtering**: Filter by document type, date, status

### Advanced Features
- **Step Functions Integration**: Orchestrated processing pipeline
- **Human Review**: A2I integration for quality assurance
- **Error Handling**: Comprehensive retry logic and error recovery
- **Scalability**: Auto-scaling Lambda functions and DynamoDB

## 🧪 Testing

```bash
# Run unit tests
cd tests
pip install -r requirements.txt
pytest test_document_processing.py -v

# Integration tests
python integration_test.py --environment dev
```

## 📈 Performance

- **Throughput**: 10+ documents/minute
- **Latency**: <6 seconds per document
- **Accuracy**: 95%+ confidence scores
- **Scalability**: Handles concurrent processing

## 💰 Cost Optimization

- S3 lifecycle policies for automatic archiving
- Lambda provisioned concurrency for predictable workloads
- DynamoDB on-demand pricing
- Textract preprocessing to reduce API costs

## 🔒 Security

- All data encrypted at rest and in transit
- IAM roles follow least-privilege principle
- VPC endpoints for private communication
- CloudTrail logging for audit trails

## 🚀 Deployment

### Manual Deployment
```bash
# Deploy infrastructure
aws cloudformation deploy --template-file architecture/cloudformation/main-infrastructure.yaml

# Deploy Lambda functions
./deployment/deploy.sh dev us-east-1
```

### CI/CD Pipeline
- GitHub Actions workflow included
- Automated testing and deployment
- Blue-green deployment strategy

## 📚 Documentation

- [Architecture Overview](architecture/diagrams/system-architecture.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](deployment/README.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Create an issue in this repository
- Check the [troubleshooting guide](docs/troubleshooting.md)
- Review AWS service documentation

## 🏷️ Tags

`aws` `document-processing` `ocr` `textract` `comprehend` `step-functions` `flask` `python` `machine-learning` `serverless`