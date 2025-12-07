# AWS Intelligent Document Processing System

A production-ready AWS-based intelligent document processing system that handles diverse document types including forms, invoices, medical records, contracts, and scanned documents. The system extracts text and structured data, enriches it with entity recognition, enables searchability, maintains audit trails, and incorporates AI-powered chat capabilities.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)
![AWS](https://img.shields.io/badge/AWS-Multiple%20Services-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Features

### Core Capabilities

- **Multi-format Document Processing**: Supports PDF, PNG, JPG, JPEG, and other image formats
- **Intelligent Text Extraction**: Uses AWS Textract for accurate OCR and text detection
- **Document Classification**: Automatically categorizes documents (invoices, receipts, contracts, certificates, letters, resumes, reports)
- **Entity Recognition**: Extracts entities (names, dates, locations, organizations) using AWS Comprehend
- **AI-Powered Chat**: Query your documents using natural language via Amazon Bedrock (Claude 3 Sonnet)
- **User Authentication**: Secure user management with AWS Cognito
- **Search Functionality**: Full-text search across all uploaded documents
- **Analytics Dashboard**: Visual insights into document processing metrics
- **Document Storage**: Persistent storage with AWS S3 and DynamoDB

### Technical Features

- Asynchronous PDF processing for large documents
- Synchronous processing for images
- RESTful API architecture
- Session-based authentication with JWT tokens
- Per-user document isolation and security
- Confidence scoring for extraction accuracy
- Comprehensive audit trails

## 🏗️ Architecture

### AWS Services Used

- **Amazon S3**: Raw document storage
- **Amazon Textract**: OCR and document text extraction
- **Amazon Comprehend**: Natural language processing and entity extraction
- **Amazon DynamoDB**: Document metadata and user data storage
- **Amazon Bedrock**: AI-powered document chat (Claude 3 Sonnet)
- **Amazon Cognito**: User authentication and management
- **AWS EC2**: Application hosting
- **AWS IAM**: Security and access management

### System Flow

```
User Upload → S3 Storage → Textract Processing → 
Entity Extraction (Comprehend) → DynamoDB Storage → 
Search Indexing → AI Chat (Bedrock)
```

## 📋 Prerequisites

- AWS Account with appropriate permissions
- Python 3.11+
- Git
- AWS CLI configured (for local development)
- EC2 instance (t3.small or larger recommended for deployment)

## 🚀 Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/PaulBoye-py/Intelligent-Document-Processing-System.git
cd Intelligent-Document-Processing-System
git checkout paul-v2
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure AWS Credentials

```bash
# Configure AWS CLI with your credentials
aws configure --profile paul-arthurite

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 5. Set Environment Variables

```bash
export DEPLOYMENT=development
export SECRET_KEY=your-secret-key-here
export AWS_DEFAULT_REGION=us-east-1
```

### 6. Run the Application

```bash
python modern_app.py
```

Visit `http://localhost:8080` in your browser.

## 🌐 AWS EC2 Deployment (Production)

### Step 1: Launch EC2 Instance

1. **Go to EC2 Console** and launch a new instance:
   - **AMI**: Amazon Linux 2023 or Ubuntu 22.04
   - **Instance Type**: t3.small (minimum) or t3.medium (recommended)
   - **Key Pair**: Create or select existing
   - **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (app)
   - **Storage**: 20 GB gp3

2. **Create IAM Role** for EC2:
   - Go to IAM → Roles → Create Role
   - Select EC2 as trusted entity
   - Attach policies:
     - `AmazonS3FullAccess`
     - `AmazonDynamoDBFullAccess`
     - `AmazonTextractFullAccess`
     - `ComprehendFullAccess`
     - `AmazonBedrockFullAccess`
     - Custom policy for Cognito (see below)
   - Name: `EC2-IDP-ExecutionRole`

3. **Attach IAM Role** to your EC2 instance:
   - EC2 Console → Select Instance → Actions → Security → Modify IAM Role
   - Select `EC2-IDP-ExecutionRole`

**Cognito Custom Policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminSetUserPassword",
        "cognito-idp:AdminInitiateAuth"
      ],
      "Resource": "arn:aws:cognito-idp:us-east-1:774305598371:userpool/us-east-1_GAiJDMatZ"
    }
  ]
}
```

### Step 2: SSH into EC2 and Setup

```bash
# SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Update system
sudo yum update -y

# Install Python 3.11 and dependencies
sudo yum install python3.11 python3.11-pip git nginx -y

# Clone repository
cd /home/ec2-user
git clone https://github.com/PaulBoye-py/Intelligent-Document-Processing-System.git
cd Intelligent-Document-Processing-System
git checkout paul-v2

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Create Systemd Service

```bash
sudo nano /etc/systemd/system/idp-app.service
```

Paste this configuration:

```ini
[Unit]
Description=IDP System Gunicorn Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/Intelligent-Document-Processing-System
Environment="PATH=/home/ec2-user/Intelligent-Document-Processing-System/venv/bin"
Environment="DEPLOYMENT=production"
Environment="AWS_DEFAULT_REGION=us-east-1"
Environment="SECRET_KEY=FpEjMYYC5ilS/ApNTrqOCvdX4e8s4NvECFiJ6QQm"
ExecStart=/home/ec2-user/Intelligent-Document-Processing-System/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 300 modern_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Step 4: Configure Nginx (Optional)

```bash
sudo nano /etc/nginx/nginx.conf
```

Add server block:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 5: Start Services

```bash
# Start application
sudo systemctl daemon-reload
sudo systemctl start idp-app
sudo systemctl enable idp-app

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status idp-app
```

### Step 6: Verify Deployment

```bash
# Test health endpoint
curl http://your-ec2-public-ip/health

# Or visit in browser
http://your-ec2-public-ip
```

## 📝 API Documentation

### Authentication Endpoints

#### Register User

```http
POST /register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

#### Login

```http
POST /login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response:
{
  "access_token": "jwt_token_here",
  "id_token": "id_token_here",
  "message": "Login successful"
}
```

### Document Processing Endpoints

#### Upload Document

```http
POST /upload
Authorization: Bearer {access_token}
Content-Type: multipart/form-data

file: [binary file data]

Response:
{
  "status": "completed",
  "document_id": "uuid",
  "filename": "document.pdf",
  "text": "extracted text...",
  "word_count": 1500,
  "confidence_score": 0.95,
  "document_classification": "invoice",
  "entities": [...]
}
```

#### Get Document Status

```http
GET /status/{document_id}

Response:
{
  "document_id": "uuid",
  "status": "completed",
  "filename": "document.pdf",
  ...
}
```

#### List Documents

```http
GET /documents
Authorization: Bearer {access_token}

Response:
[
  {
    "document_id": "uuid",
    "filename": "document.pdf",
    "upload_timestamp": "2024-12-07T10:30:00",
    ...
  }
]
```

#### Search Documents

```http
POST /search
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "invoice amount"
}

Response:
{
  "hits": [...],
  "total": 5
}
```

### AI Chat Endpoint

#### Chat with Documents

```http
POST /chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "What is the total amount in the latest invoice?",
  "history": [...]
}

Response:
{
  "response": "Based on your latest invoice...",
  "source": "bedrock",
  "document_count": 10
}
```

### Analytics Endpoint

#### Get Analytics

```http
GET /analytics
Authorization: Bearer {access_token}

Response:
{
  "total_documents": 50,
  "avg_confidence": 0.92,
  "documents_by_type": {...},
  "documents_by_classification": {...}
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEPLOYMENT` | Deployment environment | `development` | Yes |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` | Yes |
| `SECRET_KEY` | Flask secret key | - | Yes |
| `PORT` | Application port | `8080` | No |
| `USER_POOL_ID` | Cognito User Pool ID | - | Yes |
| `CLIENT_ID` | Cognito App Client ID | - | Yes |

### AWS Resources Configuration

Update these in `modern_app.py`:

```python
REGION = 'us-east-1'
S3_BUCKET = 'aws-idp-raw-774305598371-dev'
STEP_FUNCTION_ARN = 'arn:aws:states:us-east-1:774305598371:stateMachine:...'
USER_POOL_ID = 'us-east-1_GAiJDMatZ'
CLIENT_ID = '690mn07n8pmhsoluq5a8634ggt'
```

## 🛠️ Management Commands

### Application Management

```bash
# View logs
sudo journalctl -u idp-app -f

# Restart application
sudo systemctl restart idp-app

# Stop application
sudo systemctl stop idp-app

# Check status
sudo systemctl status idp-app
```

### Update Deployment

```bash
cd /home/ec2-user/Intelligent-Document-Processing-System
git pull origin paul-v2
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart idp-app
```

## 🔒 Security Considerations

### Current Setup (Development/Demo)

⚠️ **Note**: The current EC2 deployment uses `AdminAccess` IAM policy for simplicity. This is **NOT recommended for production**.

### Production Security Recommendations

1. **Replace AdminAccess with Least Privilege Policy**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::aws-idp-raw-774305598371-dev",
        "arn:aws:s3:::aws-idp-raw-774305598371-dev/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:774305598371:table/aws-idp-documents-dev"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "comprehend:DetectEntities"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    }
  ]
}
```

2. **Use AWS Secrets Manager**: Store sensitive data like SECRET_KEY

```bash
# Store secret
aws secretsmanager create-secret --name idp-secret-key --secret-string "your-secret-key"

# Retrieve in application
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='idp-secret-key')
SECRET_KEY = response['SecretString']
```

3. **Enable HTTPS**: Use AWS Certificate Manager + Application Load Balancer or Let's Encrypt

4. **Implement Rate Limiting**: Add Flask-Limiter for API protection

5. **Enable CloudWatch Logging**: Monitor application behavior

6. **Regular Security Audits**: Use AWS Security Hub and GuardDuty

7. **Rotate Credentials**: Regularly rotate SECRET_KEY and database credentials

8. **Network Security**: Use VPC, Security Groups, and NACLs properly

## 📊 Monitoring and Logging

### Application Logs

```bash
# Real-time logs
sudo journalctl -u idp-app -f

# Last 100 lines
sudo journalctl -u idp-app -n 100

# Logs from specific time
sudo journalctl -u idp-app --since "1 hour ago"
```

### AWS CloudWatch (Recommended)

Set up CloudWatch agent for centralized logging:

```bash
sudo yum install amazon-cloudwatch-agent -y
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8080/health

# Register user
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

## 🐛 Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status idp-app

# View detailed logs
sudo journalctl -u idp-app -n 50 --no-pager

# Test manually
cd /home/ec2-user/Intelligent-Document-Processing-System
source venv/bin/activate
export DEPLOYMENT=production
gunicorn --bind 0.0.0.0:8080 modern_app:app
```

### AWS Permission Errors

- Verify IAM role is attached to EC2 instance
- Check CloudWatch logs for specific permission errors
- Ensure all AWS service quotas are sufficient

### Document Processing Fails

- Check S3 bucket permissions
- Verify Textract service limits
- Check DynamoDB table exists and is accessible
- Review CloudWatch logs for Textract job status

### Chat Not Working

- Verify Bedrock model access in your region
- Check if Claude 3 Sonnet is enabled in AWS Console
- Ensure IAM role has bedrock:InvokeModel permission

## 📈 Performance Optimization

### Recommended Settings

- **Gunicorn Workers**: `(2 × CPU cores) + 1`
- **Instance Type**: t3.medium for production
- **Auto Scaling**: Use Auto Scaling Groups for high traffic
- **Caching**: Implement Redis for session storage
- **CDN**: Use CloudFront for static assets

### Database Optimization

- Use DynamoDB on-demand pricing for variable workload
- Implement proper indexes for frequent queries
- Consider DynamoDB Streams for audit logging

## 💰 Cost Estimation

**Monthly Costs** (Approximate):

- EC2 t3.small: $15
- EC2 t3.medium: $30
- S3 Storage: $1-5 (depends on usage)
- DynamoDB: $2-10 (on-demand)
- Textract: $1.50 per 1,000 pages
- Comprehend: $0.0001 per unit
- Bedrock: $3-15 per million tokens
- Data Transfer: Variable

**Total Estimate**: $50-100/month for moderate usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Paul Boye** - [PaulBoye-py](https://github.com/PaulBoye-py)

## 🙏 Acknowledgments

- AWS for providing robust cloud services
- Anthropic for Claude AI capabilities
- Flask community for excellent web framework
- Open source contributors

## 📞 Support

For issues, questions, or contributions:

- Open an issue on GitHub
- Contact: [Your Email]
- Documentation: [Your Docs URL]

## 🗺️ Roadmap

- [ ] Add support for more document types
- [ ] Implement document comparison features
- [ ] Add batch processing capabilities
- [ ] Create Docker containerization
- [ ] Add comprehensive unit tests
- [ ] Implement CI/CD pipeline
- [ ] Add multi-language support
- [ ] Create mobile app
- [ ] Add document versioning
- [ ] Implement advanced analytics

## 📚 Additional Resources

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [AWS Comprehend Documentation](https://docs.aws.amazon.com/comprehend/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

**Built with ❤️ using AWS Services**
