from sqlalchemy import LargeBinary, create_engine, MetaData, Table, Column, Integer, String

# Define your database credentials
server = 'facesystemlock.database.windows.net'
database = 'facesystemlock'
username = 'superadmin'
password = 'LKWW8mLOO&amp;qzV0La4NqYzsGmF'

# Define the connection string
connection_string = f'mssql+pymssql://{username}:{password}@{server}:1433/{database}'

# Create an SQLAlchemy engine
print("Creating SQLAlchemy engine...")
engine = create_engine(connection_string)

# Test the connection and create the table
try:
    with engine.connect() as connection:
        print("Connection to Azure SQL Database was successful!")
except Exception as e:
    print(f"An error occurred: {e}")
