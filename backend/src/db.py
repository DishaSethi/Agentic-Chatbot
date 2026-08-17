import os
import psycopg2
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Get the Neon DB URL from the environment
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file!")

def get_db_connection():
    """Helper function to get a fresh database connection."""
    return psycopg2.connect(DATABASE_URL)