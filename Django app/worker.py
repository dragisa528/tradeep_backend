import boto3
import json

sqs_client = boto3.client('sqs', region_name='your_aws_region')
queue_url = 'your_sqs_queue_url'

while True:
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
    )
    if 'Messages' in response:
        for message in response['Messages']:
            json_data = message['Body']
            try:
                data = json.loads(json_data)
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
            except json.JSONDecodeError:
                print('Invalid JSON format')
    else:
        print('No messages in the queue')