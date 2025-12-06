#!/usr/bin/env python3
import boto3
import json

def create_step_function():
    """Create Step Functions state machine for document processing"""
    
    stepfunctions = boto3.client('stepfunctions', region_name='us-east-1')
    iam = boto3.client('iam', region_name='us-east-1')
    
    # Step Functions definition
    definition = {
        "Comment": "Document Processing Workflow",
        "StartAt": "ProcessDocument",
        "States": {
            "ProcessDocument": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "aws-idp-system-textract-processor-dev",
                    "Payload.$": "$"
                },
                "Next": "StoreResults"
            },
            "StoreResults": {
                "Type": "Task", 
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "aws-idp-system-data-store-dev",
                    "Payload.$": "$"
                },
                "End": True
            }
        }
    }
    
    # Create IAM role for Step Functions
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "states.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["lambda:InvokeFunction"],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        role_response = iam.create_role(
            RoleName='StepFunctionsExecutionRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        iam.put_role_policy(
            RoleName='StepFunctionsExecutionRole',
            PolicyName='LambdaInvokePolicy',
            PolicyDocument=json.dumps(role_policy)
        )
        
        role_arn = role_response['Role']['Arn']
        print(f"✅ Created IAM role: {role_arn}")
        
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::774305598371:role/StepFunctionsExecutionRole"
        print(f"✅ Using existing IAM role: {role_arn}")
    
    try:
        # Create state machine
        response = stepfunctions.create_state_machine(
            name='aws-idp-system-document-processing-dev',
            definition=json.dumps(definition),
            roleArn=role_arn
        )
        
        print(f"✅ Created Step Functions state machine:")
        print(f"   ARN: {response['stateMachineArn']}")
        return response['stateMachineArn']
        
    except Exception as e:
        print(f"❌ Error creating state machine: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Creating Step Functions state machine...")
    arn = create_step_function()
    
    if arn:
        print("\n✅ Step Functions created successfully!")
        print("Update your Flask app with this ARN:")
        print(f"STEP_FUNCTION_ARN = '{arn}'")
    else:
        print("\n❌ Failed to create Step Functions")