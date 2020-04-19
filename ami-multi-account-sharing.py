import boto3
import csv
import os


def lambda_handler(event, context):
    src_rgn = os.environ['SRC_REGION']

    with open('accounts.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for dest_id in csv_reader:

            listToStr = ''.join(map(str, dest_id['AccountIDs']))
            print(listToStr)

            src_rgn = os.environ['SRC_REGION']

            ec2 = boto3.resource('ec2', region_name=src_rgn, )

            # Access the image that needs to be copied
            ec2_client = boto3.client('ec2', region_name=src_rgn, )
            ami_filters = [
                {
                    'Name': 'state',
                    'Values': [
                        'available'
                    ]

                }
            ]

            amis = ec2_client.describe_images(Filters=ami_filters, Owners=['self'])

            images = [ami['ImageId'] for ami in amis['Images']]

            for ami_id in images:
                image = ec2.Image(ami_id)

                response = ec2_client.modify_image_attribute(
                    ImageId=ami_id,
                    LaunchPermission={
                        'Add': [
                            {
                                'UserId': listToStr,
                            },
                        ],
                    },
                )

            snapshots = ec2_client.describe_snapshots(OwnerIds=['self'])

            snapshots_list = [snapshot['SnapshotId'] for snapshot in snapshots['Snapshots']]

            for snap_id in snapshots_list:
                snap = ec2.Snapshot(snap_id)

                response = ec2_client.modify_snapshot_attribute(
                    Attribute='createVolumePermission',
                    OperationType='add',
                    SnapshotId=snap_id,
                    UserIds=[
                        listToStr,
                    ],
                )