terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.54.1"
    }
  }
}
# Specify the AWS provider and region
provider "aws" {
  region = "eu-central-1" # Change this to your preferred region
}

# Read the .env file
data "local_file" "env_file" {
  filename = "${path.module}/.env"
}

# Extract the environment variables from the .env file
locals {
  env_vars = {
    for line in split("\n", data.local_file.env_file.content) :
    trimspace(element(split("=", line), 0)) => trimspace(element(split("=", line), 1))
    if length(split("=", line)) == 2 && trimspace(element(split("=", line), 0)) != ""
  }
  api_key    = local.env_vars["API_KEY"]
  api_secret = local.env_vars["API_SECRET"]
  bot_token  = local.env_vars["BOT_TOKEN"]
  chats_list = local.env_vars["CHATS_LIST"]
}

# Create an IAM role for the Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach the basic execution policy to the IAM role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Create a ZIP file for the Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir = "${path.module}/lambda_code" # Directory containing your Lambda code
  output_path = "${path.module}/lambda_function_payload.zip"
}

# Create a Lambda layer for the requests module
resource "aws_lambda_layer_version" "requests_layer" {
  filename   = "${path.module}/requests_layer.zip"
  layer_name = "requests_layer"
  compatible_runtimes = ["python3.11"]
}

# Create the Lambda function
resource "aws_lambda_function" "binance_lambda" {
  function_name = "binance_lambda_function"
  role          = aws_iam_role.lambda_role.arn
  handler = "lambda_function.lambda_handler" # Entry point for the Lambda function
  runtime = "python3.11"                    # Python 3.11 runtime

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = [aws_lambda_layer_version.requests_layer.arn]

  environment {
    variables = {
      API_KEY    = local.api_key
      API_SECRET = local.api_secret
      BOT_TOKEN  = local.bot_token
      CHATS_LIST = local.chats_list
    }
  }
}

# Create a CloudWatch Event Rule to trigger the Lambda every 5 minutes
resource "aws_cloudwatch_event_rule" "every_five_minutes" {
  name                = "every-five-minutes"
  schedule_expression = "rate(5 minutes)"
}

# Grant CloudWatch permission to invoke the Lambda function
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.binance_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_five_minutes.arn
}

# Connect the CloudWatch Event Rule to the Lambda function
resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule = aws_cloudwatch_event_rule.every_five_minutes.name
  target_id = "lambda_target"
  arn = aws_lambda_function.binance_lambda.arn
}
