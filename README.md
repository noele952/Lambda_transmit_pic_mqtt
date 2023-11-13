# MQTT DynamoDB Picture Reassembly

Given the potential limitations of IoT devices, transmitting large files, such as high-resolution pictures, can pose challenges.

This system comprises two Lambda functions designed to reconstruct a photo transmitted by an IoT device via MQTT, specifically using AWS IoT Core. The photo data must be fragmented into a series of base64-encoded strings by the IoT device locally, then transmitted via a series of MQTT messages. The first Lambda function manages the reception and storage of these strings in a DynamoDB table, then triggering a second Lambda function which retrieves the pieces, validates their completeness, and reassembles them into a complete image. The final image is then saved to Amazon S3.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Overview

This system consists of two Lambda functions:

1. **Picture Pieces Storage Lambda:**

   - Creates a DynamoDB table
   - Receives and stores base64-encoded photo pieces in that DynamoDB table.
   - Triggers picture reassembly upon receiving an 'END' message.

2. **Picture Reassembly Lambda:**
   - Retrieves all pieces from the DynamoDB table.
   - Validates the completeness of the pieces.
   - Reassembles the pieces into a JPEG image.
   - Saves the assembled image to Amazon S3.
   - Cleans up the DynamoDB table after successful reassembly.

## Prerequisites

Ensure that you have the necessary AWS credentials set up to interact with DynamoDB, Lambda, MQTT via AWS IoT Core, and S3.

## Setup

1. **DynamoDB Table Creation:**

   - The first Lambda function creates a DynamoDB table to store picture pieces.
   - Ensure the Lambda function has appropriate IAM permissions to create DynamoDB tables.

2. **S3 Bucket Configuration:**

   - Configure an S3 bucket to save the assembled images.
   - Set the bucket name in the MY_BUCKET_NAME variable within the Lambda function's environment variables or code.

3. **Lambda Function for Reassembly:**
   - Deploy the second Lambda function for picture reassembly.
   - Set the ARN of the reassembly Lambda function in the `trigger_reassembly` function within the first Lambda function.

## Usage

Invoke the first Lambda function with an event containing the following parameters:

- `label`: DynamoDB table name (picture_name)
- `count`: Message count
- `data`: Picture piece data
- `machine_id`: Identifier for the source machine

## Environment Variables

### Picture Assembly Lambda

BUCKET_NAME = 'my_bucket'
PICTURE_NAME = 'my_picture'

Customize the `BUCKET_NAME` and `PICTURE_NAME` variable by either setting it as an Environment Variable in the Lambda console or directly modifying the code.

```plaintext
BUCKET_NAME=bucket_name
PICTURE_NAME=picture_name
```

### Picture Storage Lambda

REASSEMBLY_FUNCTION_ARN = 'reassembly_function_ARN'

Set the `REASSEMBLY_FUNCTION_ARN` variable to the ARN of the Lambda function responsible for picture reassembly. This allows you to easily update the function's ARN without modifying the code. You can set it as an Environment Variable in the Lambda console or directly modify the code.

```plaintext
REASSEMBLY_FUNCTION_ARN = your_arn
```

## Dependencies

- `boto3`: AWS SDK for Python
- `botocore`: Low-level, data-driven core of boto3
- `PIL`: Python Imaging Library (required for the second Lambda function)

  #### Python Image Library (PIL)

  PIL is not part of the standard Lambda runtime, it must be added as a layer. For simplicity, I recommend using [klayers](https://github.com/kennbroorg/klayers), or you can make your own if you prefer.

## Contributing

Feel free to contribute by reporting issues or submitting pull requests.

## License

This DynamoDB Picture Assembly System is licensed under the [MIT License](LICENSE).
