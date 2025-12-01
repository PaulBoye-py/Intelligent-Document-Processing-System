# AWS Intelligent Document Processing System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AWS Intelligent Document Processing System            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client    │───▶│   Amazon S3  │───▶│  AWS Lambda     │───▶│ Step Functions  │
│ Application │    │  (Raw Docs)  │    │ (Preprocessing) │    │ (Orchestration) │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                                                │                        │
                                                ▼                        ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  OpenSearch │◀───│  DynamoDB    │◀───│   Amazon        │◀───│   Amazon        │
│  (Search)   │    │  (Results)   │    │   Comprehend    │    │   Textract      │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                                                │                        │
                                                ▼                        ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Amazon A2I │    │   Amazon S3  │    │  AWS Lambda     │    │  AWS Lambda     │
│ (Human      │    │ (Processed)  │    │ (Comprehend     │    │ (Textract       │
│  Review)    │    │              │    │  Processor)     │    │  Processor)     │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                                                │                        │
                                                ▼                        ▼
                   ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
                   │   Amazon S3  │    │  AWS Lambda     │    │   DynamoDB      │
                   │  (Archive)   │    │ (Search         │    │  (Metadata)     │
                   │              │    │  Indexer)       │    │                 │
                   └──────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Responsibilities

### Document Processing Pipeline
1. **S3 Raw Bucket**: Document ingestion and storage
2. **Lambda Preprocessing**: OpenCV image enhancement
3. **Amazon Textract**: Text, table, and form extraction
4. **Amazon Comprehend**: Entity recognition and classification
5. **Step Functions**: Workflow orchestration and error handling
6. **Amazon A2I**: Human review for low-confidence results
7. **DynamoDB**: Structured data storage with fast access
8. **OpenSearch**: Full-text search and analytics
9. **S3 Archive**: Long-term document storage

### Data Flow Overview
- Documents uploaded to S3 trigger Step Functions workflow
- Preprocessing enhances image quality using OpenCV
- Textract extracts text, tables, and forms with confidence scores
- Comprehend performs entity recognition and document classification
- Quality checks route low-confidence results to human review
- Final results stored in DynamoDB and indexed in OpenSearch
- Original documents archived with lifecycle policies