"""
This script forcefully drops all tables from the database and recreates them
based on the current models.

This is a destructive operation and should only be used in development.
"""
import os
import sys

# Add the parent directory to the path to allow imports from `app`
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app.models import user, lesson, level # Import all models here

def reset_database():
    print("--- WARNING: Dropping all tables and recreating database ---")
    try:
        Base.metadata.drop_all(bind=engine)
        print("Tables dropped.")
        Base.metadata.create_all(bind=engine)
        print("Tables recreated successfully.")
        print("--- Database has been reset ---")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    reset_database()
