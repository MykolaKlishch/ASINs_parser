# import psycopg2
# import time
from sqlalchemy import create_engine, MetaData

print("Type your credentials to connect to the Amazon RDS database instance:")

dialect = "postgresql"
driver = "psycopg2"
username = input("username: ").strip()
password = input("password: ").strip()
host = "asins-db-instance.cvkioejijss6.eu-central-1.rds.amazonaws.com"
port = "5432"
database = "postgres"

db_url = f"{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(db_url)

with engine.connect() as conn:
    query_results = conn.execute("""SELECT now()""")
    for query_result in query_results:
        print(query_result)

# print("Type your credentials to connect to the Amazon RDS database instance:")
#
# try:
#     conn = psycopg2.connect(
#         database="postgres",
#         user=input("username: ").strip(),
#         password=input("password: ").strip(),
#         host="asins-db-instance.cvkioejijss6.eu-central-1.rds.amazonaws.com",
#         port="5432"
#     )
# except Exception as e:
#     print("Database connection failed due to {}".format(e))
# else:
#     cur = conn.cursor()
#     cur.execute("""SELECT now()""")
#     query_results = cur.fetchall()
#     print(query_results)
