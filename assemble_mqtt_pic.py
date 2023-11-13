# set env variable PICTURE_NAME, BUCKET_NAME
####### Requires PIL lambda layer
import boto3
import json
import base64
from io import BytesIO
from PIL import Image
import time

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Extract the table name from the event payload
    table_name = event['table_name']
    # Retrieve all pieces from DynamoDB
    pieces = retrieve_pieces_from_dynamodb(table_name)
    print(pieces)
    # Validate if all pieces are present
    if validate_pieces(pieces):
        # Reassemble the pieces into a JPEG file
        assembled_image = reassemble_image(pieces)
        print(assembled_image)
        # Save the assembled image to S3
        save_to_s3(assembled_image)

        # Clean up DynamoDB table
        clean_up_dynamodb(table_name)
    else:
        print("Error: Incomplete pieces. Reassembly aborted.")


def retrieve_pieces_from_dynamodb(table_name):
    # Retrieve all pieces from DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    response = table.scan()
    return response['Items']


def validate_pieces(pieces):
    # Validate if all pieces are present
    count_set = set(piece['count'] for piece in pieces)
    expected_counts = set(range(len(pieces)))
    return count_set == expected_counts


def reassemble_image(pieces):
    # Sort pieces based on count, excluding the piece with 'END'
    sorted_pieces = sorted([piece for piece in pieces if piece['data'] != 'END'], key=lambda x: x['count'])
    # Create a BytesIO object to accumulate binary data
    image_data_io = BytesIO()
    # Write binary data from each piece to the BytesIO object
    for piece in sorted_pieces:
        image_data_io.write(piece['data'].value)
    # Move the cursor to the beginning of the BytesIO object
    image_data_io.seek(0)
    # Create an image from the binary data
    image = Image.open(image_data_io)
    return image


def save_to_s3(image):
    # Save the assembled image to S3
    current_time = int(time.time())
    key = f'{PICTURE_NAME}_{current_time}.jpeg'
    with BytesIO() as output:
        image.save(output, format='JPEG')
        output.seek(0)
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=output)


def clean_up_dynamodb(table_name):
    # Delete the DynamoDB table
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.delete()