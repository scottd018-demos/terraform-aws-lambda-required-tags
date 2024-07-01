# Summary

This repo is used to add tags to EC2 instances and EBS volumes upon their creation.  It was mainly created to 
handle a case in ROSA where tags are not formally adjustable after initial provisioning of a cluster, yet 
operational environments must be able to adapt to changes like requirements for new tags, however it could be 
adopted to other use cases as well.


## Architecture

The following simplistically shows how this Terraform module achieves enforcement of desired tagging:

![Architecture](images/architecture.png)

1. A user creates an EC2 instance
2. AWS Event Bridge rules are setup to send events when an EC2 instance is `Running` and when an EBS volume is `created`
3. An event is received by Lambda and a function (code in the `function/` directory) is executed.
4. The function performs logic to tag instances based on the `REQUIRED_TAGS_KEYS` and `REQUIRED_TAGS_VALUES` 
environment variables.
5. Logs are sent to a CloudWatch log group for review.
