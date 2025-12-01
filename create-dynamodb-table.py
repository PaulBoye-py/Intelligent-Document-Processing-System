#!/usr/bin/env python3
import boto3

def create_dynamodb_table():
    """Create DynamoDB table for document metadata"""
    
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    try:
        response = dynamodb.create_table(
            TableName='aws-idp-system-document-metadata-dev',
            KeySchema=[
                {
                    'AttributeName': 'document_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'document_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✅ Created DynamoDB table: {response['TableDescription']['TableName']}")
        print(f"   Status: {response['TableDescription']['TableStatus']}")
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print("✅ DynamoDB table already exists")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating DynamoDB table...")
    success = create_dynamodb_table()
    
    if success:
        print("\n✅ DynamoDB table ready!")
        print("You can now run your Flask app.")
    else:
        print("\n❌ Failed to create DynamoDB table")