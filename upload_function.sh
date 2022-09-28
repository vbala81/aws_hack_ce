#!/bin/sh
zip -r lambda_function.zip lambda_function.py rds_config.py pymysql/ PyMySQL-1.0.2.dist-info/
aws lambda update-function-code --function-name CircularEconomyLambda --zip-file fileb://lambda_function.zip
aws s3 cp lambda_function.zip s3://hackathon-ce-bucket/
rm lambda_function.zip