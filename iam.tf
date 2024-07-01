resource "aws_iam_policy" "required_tags" {
  name        = var.name_prefix
  description = "Policy to allow read and update of EC2 instance and volume tags."

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ec2:DescribeTags",
          "ec2:CreateTags",
          "ec2:DeleteTags"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "required_tags" {
  name = var.name_prefix
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com" # or any other service that requires this role
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "required_tags" {
  role       = aws_iam_role.required_tags.name
  policy_arn = aws_iam_policy.required_tags.arn
}
