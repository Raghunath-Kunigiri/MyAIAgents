import boto3
import os
from botocore.exceptions import ClientError

# --- Configuration ---
# You can change these names to whatever you like.
KEY_PAIR_NAME = 'Boto3KeyPair'
KEY_PAIR_FILE = f'{KEY_PAIR_NAME}.pem'
SECURITY_GROUP_NAME = 'Boto3SecurityGroup'
INSTANCE_NAME = 'Boto3Instance'

# EC2 instance details
INSTANCE_TYPE = 't2.micro'
AWS_REGION = 'us-east-1' # Replace with your desired AWS region if different.

# --- Boto3 Clients ---
ec2_client = boto3.client('ec2', region_name=AWS_REGION)
ec2_resource = boto3.resource('ec2', region_name=AWS_REGION)
ssm_client = boto3.client('ssm', region_name=AWS_REGION)

def get_latest_al2023_ami_id():
    """
    Finds the latest Amazon Linux 2023 (kernel 6.1) AMI ID for the specified region
    by using the AWS SSM Parameter Store, which is the recommended method.
    """
    print("Finding the latest Amazon Linux 2023 AMI ID from SSM Parameter Store...")
    try:
        # This is the stable path for the latest Amazon Linux 2023 with kernel 6.1
        parameter = ssm_client.get_parameter(
            Name='/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64'
        )
        ami_id = parameter['Parameter']['Value']
        print(f"Found AMI ID: {ami_id}")
        return ami_id
    except ssm_client.exceptions.ParameterNotFound:
        print("Error: Could not find the SSM Parameter for Amazon Linux 2023 in this region.")
        raise Exception("Could not find a suitable Amazon Linux 2023 AMI via SSM.")


def create_ec2_instance():
    """
    Creates a key pair, a security group, and launches an EC2 instance.
    """
    try:
        # --- Dynamically get the AMI ID ---
        ami_id = get_latest_al2023_ami_id()

        # --- Step 1: Create a new EC2 Key Pair (if it doesn't already exist) ---
        print(f"Checking for key pair: {KEY_PAIR_NAME}...")
        try:
            ec2_client.create_key_pair(KeyName=KEY_PAIR_NAME)
            # Save the private key to a .pem file
            with open(KEY_PAIR_FILE, 'w') as f:
                f.write(key_pair['KeyMaterial'])
            # Set permissions for the key file (important for SSH)
            os.chmod(KEY_PAIR_FILE, 0o400)
            print(f"Successfully created and saved key pair to '{KEY_PAIR_FILE}'.")
            print("IMPORTANT: Set file permissions to read-only for your user if on Windows.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                print(f"Key pair '{KEY_PAIR_NAME}' already exists. Skipping creation.")
            else:
                raise e

        # --- Step 2: Create a new Security Group (if it doesn't already exist) ---
        print(f"Checking for security group: {SECURITY_GROUP_NAME}...")
        try:
            security_group = ec2_client.create_security_group(
                GroupName=SECURITY_GROUP_NAME,
                Description='Security group created by Boto3 script for SSH access'
            )
            sg_id = security_group['GroupId']
            print(f"Successfully created security group with ID: {sg_id}")

            # --- Step 3: Add an Inbound Rule for SSH ---
            print("Adding inbound SSH rule to security group...")
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}] # Allows SSH from any IP
                    }
                ]
            )
            print("Successfully added SSH rule.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
                print(f"Security group '{SECURITY_GROUP_NAME}' already exists. Using existing group.")
                # Get the ID of the existing security group
                response = ec2_client.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
                sg_id = response['SecurityGroups'][0]['GroupId']
                print(f"Found existing security group with ID: {sg_id}")
            else:
                raise e

        # --- Step 4: Launch the EC2 Instance ---
        print(f"Launching EC2 instance '{INSTANCE_NAME}'...")
        instances = ec2_resource.create_instances(
            ImageId=ami_id,
            InstanceType=INSTANCE_TYPE,
            KeyName=KEY_PAIR_NAME,
            SecurityGroupIds=[sg_id],
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': INSTANCE_NAME
                        },
                    ]
                },
            ]
        )
        instance = instances[0]
        print(f"Instance '{INSTANCE_NAME}' launch initiated. Waiting for it to be running...")

        # Wait for the instance to enter the 'running' state
        instance.wait_until_running()
        instance.reload() # Reload instance attributes to get the public IP

        print("\n--- SUCCESS ---")
        print(f"Instance ID: {instance.id}")
        print(f"Public IP Address: {instance.public_ip_address}")
        print("\nTo connect to your instance, use the following command:")
        print(f'ssh -i "{KEY_PAIR_FILE}" ec2-user@{instance.public_ip_address}')

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your AWS credentials and permissions, and ensure resources with these names don't already exist.")

if __name__ == '__main__':
    create_ec2_instance()
