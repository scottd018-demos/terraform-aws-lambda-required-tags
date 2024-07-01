import json
import boto3
import os

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')

    # print the event and context for debugging purposes
    print(f"Event: {event}")
    print(f"Context: {context}")
    
    # extract resource information from the event
    # NOTE: the top condition is used for testing only, the bottom is for real events
    if 'test_resource_id' in event and 'test_resource_type' in event:
        print("executing test workflow due to existence of 'test_resource_id' and 'test_resource_type' event keys...")
        resource_id = event['test_resource_id']
        resource_type = event['test_resource_type']
    else:
        print("retrieving 'resource-id' and 'resource-type' from event detail...")
        if event['detail-type'] == 'EC2 Instance State-change Notification':
            resource_type = 'instance'
            resource_id = event['detail']['instance-id']
        elif event['detail-type'] == 'EBS Volume Notification':
            resource_type = 'volume'
            resource_arn = event['resources'][0]
            resource_id = resource_arn.split('/')[-1]
        else:
            print(f"unsupported event type: {event['detail-type']}")
            return {
                'statusCode': 400,
                'body': json.dumps('Unsupported event type')
            }

    print(f"detected '{resource_type}' resource type with id '{resource_id}'...")

    # confirm we are working with a proper resource type and extract its tags
    if resource_type == 'instance':
        # describe the instance to get its tags
        response = ec2.describe_instances(InstanceIds=[resource_id])
        tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    elif resource_type == 'volume':
        # describe the volume to get its tags
        response = ec2.describe_volumes(VolumeIds=[resource_id])
        tags = response['Volumes'][0].get('Tags', [])
    else:
        print(f"unsupported resource type: {resource_type}")
        return {
            'statusCode': 400,
            'body': json.dumps('unsupported resource type')
        }

    # convert the string list environment variables into a dict of required tags
    required_tags_keys = os.getenv("REQUIRED_TAGS_KEYS")
    if required_tags_keys == "":
        print(f"missing required tags keys from REQUIRED_TAGS_KEYS environment variable")
        return {
            'statusCode': 400,
            'body': json.dumps('missing required tags keys')
        }
    required_tags_values = os.getenv("REQUIRED_TAGS_VALUES")
    if required_tags_values == "":
        print(f"missing required tags values from REQUIRED_TAGS_VALUES environment variable")
        return {
            'statusCode': 400,
            'body': json.dumps('missing required tags values')
        }

    required_tags_keys_list = required_tags_keys.split(',')
    required_tags_values_list = required_tags_values.split(',')

    # double check that we have identical length of keys and values
    if len(required_tags_keys_list) != len(required_tags_values_list):
        print(f"REQUIRED_TAGS_KEYS and REQUIRED_TAGS_VALUES must have an equal number of elements")
        return {
            'statusCode': 400,
            'body': json.dumps('unbalanced keys and values elements')
        }
    
    required_tags = {}
    print(f"convert keys '{required_tags_keys_list}' and values '{required_tags_values_list}' to a tag map...")

    for i in range(len(required_tags_keys_list)):
        required_tags[required_tags_keys_list[i]] = required_tags_values_list[i]

    # convert tags to a dictionary for easier access
    tag_dict = {tag['Key']: tag['Value'] for tag in tags}
    print(f"found existing tags on resource: {tag_dict}...")

    # check for the required tag.  if both the 'red-hat-managed' tag and the 'red-hat-clustertype' tag are
    # not set, we can assume we are not dealing with a ROSA resource and can skip it.
    if tag_dict.get('red-hat-managed') == 'true' and tag_dict.get('red-hat-clustertype') == 'rosa':
        print(f"adding required tags: {required_tags}...")

        for key in required_tags:
            # if the tag key is already set, continue the loop
            if tag_dict.get(key) != None and tag_dict.get(key) != "":
                continue

            # add the new tag
            ec2.create_tags(
                Resources=[resource_id],
                Tags=[{'Key': key, 'Value': required_tags.get(key)}]
            )
            print(f"resource '{resource_id}' tagged successfully with '{key}={required_tags.get(key)}'...")
    else:
        print(f"skipping non-ROSA resource type '{resource_type}' with id '{resource_id}'...")

    return {
        'statusCode': 200,
        'body': json.dumps('function executed successfully!')
    }
