#
# cloudwatch
#
resource "aws_cloudwatch_log_group" "required_tags" {
  name              = "/aws/lambda/${aws_lambda_function.required_tags.function_name}"
  retention_in_days = 14
}

#
# event bridge
#
resource "aws_cloudwatch_event_rule" "required_tags_instances" {
  name        = "${var.name_prefix}-instances"
  description = "Rule to trigger Lambda on EC2 instance on state change to running"
  event_pattern = jsonencode({
    "source" : ["aws.ec2"],
    "detail-type" : ["EC2 Instance State-change Notification"],
    "detail" : {
      "state" : ["running"]
    }
  })
}

resource "aws_cloudwatch_event_rule" "required_tags_volumes" {
  name        = "${var.name_prefix}-volumes"
  description = "Rule to trigger Lambda on EC2 volume on state change to created"
  event_pattern = jsonencode({
    "source" : ["aws.ec2"],
    "detail-type" : ["EBS Volume Notification"],
    "detail" : {
      "event" : ["createVolume"]
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda_instances" {
  rule      = aws_cloudwatch_event_rule.required_tags_instances.name
  target_id = "EC2InstancesRequiredTagsFunction"
  arn       = aws_lambda_function.required_tags.arn
}

resource "aws_cloudwatch_event_target" "lambda_volumes" {
  rule      = aws_cloudwatch_event_rule.required_tags_volumes.name
  target_id = "EC2VolumesRequiredTagsFunction"
  arn       = aws_lambda_function.required_tags.arn
}

#
# lambda
#
locals {
  required_tags_keys_string   = join(",", var.required_tags.keys)
  required_tags_values_string = join(",", var.required_tags.values)
}

data "archive_file" "required_tags" {
  type        = "zip"
  source_file = "${path.module}/function/required_tags.py"
  output_path = "${path.module}/function/required_tags.zip"
}

resource "aws_lambda_function" "required_tags" {
  filename         = data.archive_file.required_tags.output_path
  function_name    = var.name_prefix
  role             = aws_iam_role.required_tags.arn
  handler          = "required_tags.lambda_handler"
  runtime          = "python3.10"
  source_code_hash = data.archive_file.required_tags.output_base64sha256
  timeout          = 20

  environment {
    variables = {
      "REQUIRED_TAGS_KEYS"   = local.required_tags_keys_string,
      "REQUIRED_TAGS_VALUES" = local.required_tags_values_string
    }
  }
}

resource "aws_lambda_permission" "event_bridge_instances" {
  statement_id  = "AllowExecutionFromEventBridgeEC2Instances"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.required_tags.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.required_tags_instances.arn
}

resource "aws_lambda_permission" "event_bridge_volumes" {
  statement_id  = "AllowExecutionFromEventBridgeEC2Volumes"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.required_tags.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.required_tags_volumes.arn
}
