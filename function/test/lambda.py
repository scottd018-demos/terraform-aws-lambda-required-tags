import json
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # extract resource information from the event
    resource_id = event['detail']['resource-id']
    resource_type = event['detail']['resource-type']

    if resource_type == 'instance':
        # describe the instance to get its tags
        response = ec2.describe_instances(InstanceIds=[resource_id])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    elif resource_type == 'volume':
        # describe the volume to get its tags
        response = ec2.describe_volumes(VolumeIds=[resource_id])
        tags = response['Volumes'][0].get('Tags', [])
    else:
        print(f"Unsupported resource type: {resource_type}")
        return {
            'statusCode': 400,
            'body': json.dumps('Unsupported resource type')
        }

    # convert tags to a dictionary for easier access
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}

    # set the required tags
    required_tags = {
        'this': 'that'
    }

    # check for the required tag.  if both the 'red-hat-managed' tag and the 'red-hat-clustertype' tag are
    # not set, we can assume we are not dealing with a ROSA resource and can skip it.
    if tag_dict.get('red-hat-managed') == 'true' and tag_dict.get('red-hat-clustertype') == 'rosa':
        for key in required_tags:
            # if the tag key is already set, continue the loop
            if tag_dict.get(key) != None and tag_dict.get(key) != "":
                continue

            # add the new tag
            ec2.create_tags(
                Resources=[resource_id],
                Tags=[{'Key': key, 'Value': required_tags.get(key)}]
            )
            print(f"resource {resource_id} tagged successfully with {key}={required_tags.get(key)}")
    else:
        print(f"skipping non-ROSA {resource_id} of type {resource_type}...")

    return {
        'statusCode': 200,
        'body': json.dumps('function executed successfully!')
    }
