import boto3
import os

ec2 = boto3.client('ec2', 'us-east-1')
amis = ec2.describe_images(Owners=[    'self'
])

num = int(os.environ["AMI_TO_KEEP"])


def lambda_handler(event, context):
    dates = sorted([ami['CreationDate'] for ami in amis['Images']])[-num:]
    for ami in amis['Images']:
        create_date = ami['CreationDate']
        ami_id = ami['ImageId']
        if create_date not in dates:
            print(f'deleting {ami_id}')
            ec2.deregister_image(ImageId=ami_id)