import boto3
from datetime import date
import os

# datetime object containing current date and time
now = date.today()

# Create CrossAccountole Role in src_account which will give permission to operations in the account
sts = boto3.client('sts')


def lambda_handler(event, context):
    src_id = os.environ['SRC_ACCOUNT_ID']
    dest_id = os.environ['DEST_ACCOUNT_ID']
    src_rgn = os.environ['SRC_REGION']
    dest_rgn = os.environ['DEST_REGION']
    replicate_lambda = os.environ['DEST_ACCOUNT_ROLE']

    ec2 = boto3.resource('ec2', region_name=src_rgn, )
    #
    # Access the image that needs to be copied
    ec2_client = boto3.client('ec2', region_name=src_rgn, )
    ami_filters = [
        {
            'Name': 'is-public',
            'Values': [
                'true'
            ]

        },
        {
            'Name': 'state',
            'Values': [
                'available'
            ]

        }
    ]

    amis = ec2_client.describe_images(Filters=ami_filters, Owners=['self'])

    images = [ami['ImageId'] for ami in amis['Images']]
    print("images: ", images)

    for ami_id in images:

        image = ec2.Image(ami_id)

        # We have to now share the snapshots associated with the AMI so it can be copied
        devices = image.block_device_mappings
        for device in devices:
            if 'Ebs' in device:
                snapshot_id = device["Ebs"]["SnapshotId"]
                snapshot = ec2.Snapshot(snapshot_id)
                snapshot.modify_attribute(
                    Attribute='createVolumePermission',
                    CreateVolumePermission={
                        'Add': [{'UserId': dest_id}]
                    },
                    OperationType='add',
                )
            print(ami_id)

        # Access destination account so we can now copy the image
        rolearn = 'arn:aws:iam::%s:role/%s' % (dest_id, replicate_lambda)
        print(rolearn)
        credentials = sts.assume_role(
            RoleArn=rolearn,
            RoleSessionName="RoleSession1"
        )
        creds = credentials['Credentials']
        print(creds)

        # Copy image to failover regions
        ec2fra = boto3.client('ec2', dest_rgn,
                              aws_access_key_id=creds['AccessKeyId'],
                              aws_secret_access_key=creds['SecretAccessKey'],
                              aws_session_token=creds['SessionToken']
                              )

        # Copy the shared AMI to dest region
        ec2fra.copy_image(
            Name=f'{now} Image Copy',
            SourceImageId=image.id,
            SourceRegion=src_rgn
        )