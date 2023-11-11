import boto3
import botocore.exceptions
from datetime import datetime, timedelta
import time
import json
import base64

REASSEMBLY_FUNCTION_ARN = 'reassembly_function_ARN'

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    tablename = event['label']
    count = event['count']
    data = event['data']
    machine_id = event['machine_id']
    
    # Creata a dynamodb table to hold the pieces of the picture
    create_dynamodb_table(tablename)
    
    # Check if the message is 'END' and trigger reassembly if needed
    if data == 'END':
        trigger_reassembly(tablename)
    # Save the message in DynamoDB
    else:    
        save_to_dynamodb(tablename, count, data)

    
def create_dynamodb_table(table_name):
    # Check if the table exists
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']

    if table_name not in existing_tables:
        # Create the DynamoDB table
        try:
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'count', 'KeyType': 'HASH'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'count', 'AttributeType': 'N'},
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5,
                }
            )
            # Wait for the table to be created
            table.meta.client.get_waiter(
                'table_exists').wait(TableName=table_name)

        except dynamodb.meta.client.exceptions.ResourceInUseException:
            print("exception in create_dynamodb_table")
            # Table is already being created, wait for it to exist
            dynamodb.meta.client.get_waiter(
                'table_exists').wait(TableName=table_name)
   

def save_to_dynamodb(table_name, count, data, ttl_minutes=30, retries=3, delay_seconds=5):
    for attempt in range(retries):
        try:
            # Save the message in DynamoDB with TTL
            print(f'Table name: {table_name}')
            print(f'Count: {count}')
            print(f'Data: {data}')
            decoded_data = base64.b64decode(data)
            print("Decoded data:", decoded_data)

            table = dynamodb.Table(table_name)

            # Calculate TTL timestamp (current time + TTL in seconds)
            ttl_timestamp = int(time.mktime((datetime.utcnow() + timedelta(minutes=ttl_minutes)).timetuple()))

            response = table.put_item(
                Item={
                    'count': count,
                    'data': decoded_data,
                    'ttl': ttl_timestamp
                }
            )
            print("Put item response:", response)
            print("Item inserted:", response.get('Attributes'))
            print("Success: Data saved to DynamoDB")

            break  # Break out of the retry loop if successful

        except botocore.exceptions.WaiterError as we:
            print(f"Waiter error: {we}")
            time.sleep(delay_seconds)
            print("Retrying...")

        except Exception as e:
            print(f"Error saving to DynamoDB (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay_seconds)
            print("Retrying...")

    else:
        print("Max retries reached. Unable to save to DynamoDB.")


def trigger_reassembly(table_name):
    # Trigger the Lambda function for reassembly
    lambda_client.invoke(
        FunctionName=f'{REASSEMBLY_FUNCTION_ARN}',
        InvocationType='Event',  # Asynchronous invocation
        Payload=json.dumps({'table_name': table_name})
    )
