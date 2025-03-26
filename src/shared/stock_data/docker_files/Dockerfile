# Use the base AWS Lambda Python 3.12 image
FROM public.ecr.aws/lambda/python:3.12.2024.01.05.15

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY lambda_function.py .

# Set the Lambda handler
CMD [ "lambda_function.lambda_handler" ]
