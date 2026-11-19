
import os
import pymysql
from dotenv import load_dotenv

# Load database settings from .env
load_dotenv()

# Connect to the MySQL database
connection = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

# Test the database connection
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print("Database connected successfully!")
    print("Number of users:", count)

connection.close()
