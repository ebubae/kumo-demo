import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from mysql.connector import connect

load_dotenv()

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")

# Observability
MAXIM_API_KEY = os.environ.get("MAXIM_API_KEY")
MAXIM_REPO_ID = os.environ.get("MAXIM_REPO_ID")

DB_NAME = os.environ.get("DATABASE")
DB_USERNAME = os.environ.get("DATABASE_USERNAME")
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD")
DB_HOST = os.environ.get("DATABASE_HOST")
MYSQL_PORT = 3306

DB_CONFIG = {
    "user": DB_USERNAME,
    "password": DB_PASSWORD,
    "host": DB_HOST,
    "database": DB_NAME,
}

engine = create_engine(
    f"mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{MYSQL_PORT}/{DB_NAME}",
)

connection = connect(**DB_CONFIG)
