from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/db") 

# Conditionally create the engine based on the database type
if DATABASE_URL.startswith("sqlite"):
    # Use check_same_thread only for SQLite
    engine = create_engine( 
        DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True
    )
else:
    # Do not use check_same_thread for PostgreSQL or other DBs
    engine = create_engine(
        DATABASE_URL, pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

