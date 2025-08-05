# db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

# For local development, you'll create a DATABASE_URL in your .env file
# For production, you'll set this in Render's environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# The engine is the entry point to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Each instance of SessionLocal will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that our ORM models will inherit from
Base = declarative_base()