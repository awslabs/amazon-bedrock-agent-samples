import boto3
import os

session = boto3.session.Session()
region = session.region_name

data_source_bucket_name = os.environ["DATA_SOURCE_BUCKET_NAME"]
aurora_serverless_db_cluster_arn = os.environ["AURORA_SERVERLESS_DB_CLUSTER_ARN"]
secret_arn = os.environ["SECRET_ARN"]
database_name = "video_games_sales"

s3_client = boto3.client("s3")
s3_client.upload_file(
    "resources/database/video_games_sales_no_headers.csv",
    data_source_bucket_name,
    "video_games_sales_no_headers.csv",
)

client = boto3.client("rds-data")

query1 = """ CREATE TABLE video_games_sales_units (
    title TEXT,
    console TEXT,
    genre TEXT,
    publisher TEXT,
    developer TEXT,
    critic_score NUMERIC(3,1),
    total_sales NUMERIC(4,2),
    na_sales NUMERIC(4,2),
    jp_sales NUMERIC(4,2),
    pal_sales NUMERIC(4,2),
    other_sales NUMERIC(4,2),
    release_date DATE
); """

response = client.execute_statement(
    resourceArn=aurora_serverless_db_cluster_arn,
    secretArn=secret_arn,
    sql=query1,
    database=database_name,
)

print("Query: " + query1)
print("Query response: " + str(response))

query2 = "CREATE EXTENSION aws_s3 CASCADE;"

response = client.execute_statement(
    resourceArn=aurora_serverless_db_cluster_arn,
    secretArn=secret_arn,
    sql=query2,
    database=database_name,
)

print("-----------------------------------------")
print("Query: " + query2)
print("Query response: " + str(response))

query3 = f""" 
SELECT aws_s3.table_import_from_s3(
   'video_games_sales_units',
   'title,console,genre,publisher,developer,critic_score,total_sales,na_sales,jp_sales,pal_sales,other_sales,release_date',
   'DELIMITER ''|''', 
   aws_commons.create_s3_uri('{data_source_bucket_name}', 'video_games_sales_no_headers.csv', '{region}')
); """

response = client.execute_statement(
    resourceArn=aurora_serverless_db_cluster_arn,
    secretArn=secret_arn,
    sql=query3,
    database=database_name,
)

print("-----------------------------------------")
print("Query: " + query3)
print("Query response: " + str(response))

print("-----------------------------------------")
print("Database created successfully!")
