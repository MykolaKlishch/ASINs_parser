"""
Details:

Connecting to Your DB Instance Using IAM Authentication and
the AWS SDK for Python (Boto3)

https://docs.aws.amazon.com/AmazonRDS/latest
/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.Python.html#UsingWithRDS.
IAMDBAuth.Connecting.Python.AuthToken.Connect
"""


import psycopg2
import sys
import boto3

ENDPOINT = "database-1.cvkioejijss6.eu-central-1.rds.amazonaws.com"
PORT = "5432"
USR = input("USR: ").strip()
REGION = "eu-central-1"
DBNAME = "postgres"

# gets the credentials from .aws/credentials
session = boto3.Session(profile_name='default')
client = boto3.client('rds')

token = client.generate_db_auth_token(
    DBHostname=ENDPOINT, Port=PORT, DBUsername=USR, Region=REGION
)

try:
    conn = psycopg2.connect(host=ENDPOINT, port=PORT, database=DBNAME,
                            user=USR, password=token)
    cur = conn.cursor()
    cur.execute("""SELECT now()""")
    query_results = cur.fetchall()
    print(query_results)
except Exception as e:
    print("Database connection failed due to {}".format(e))
