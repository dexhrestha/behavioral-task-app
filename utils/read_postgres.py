from sqlalchemy import create_engine

# Database connection details
DB_HOST = "10.0.0.41"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "kestra"
DB_PASSWORD = "k3str4"

def create_connection():
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    return engine
