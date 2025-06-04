import duckdb
import os
from src.etl.config import DATA_DIR, OUTPUT_DIR, DATABASE_NAME # Import constants from new location

CSV_FILES_PATH = os.path.join(DATA_DIR, "*.csv") # Use DATA_DIR
DATABASE_PATH = os.path.join(OUTPUT_DIR, DATABASE_NAME) # Use OUTPUT_DIR and DATABASE_NAME

def create_raw_contracts_model():
    """
    Creates a DuckDB database and a view 'raw_contracts' that reads from CSV files.
    The CSV files are expected to be in the 'data' directory relative to the project root.
    The DuckDB database will be created in the 'output' directory.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True) # Use OUTPUT_DIR
        
        # Connect to DuckDB. If the file doesn't exist, it will be created.
        con = duckdb.connect(database=DATABASE_PATH, read_only=False)
        
        # SQL to create a view from CSV files
        # read_csv_auto will infer columns and types, and handle multiple files via glob pattern
        view_sql = """
            CREATE OR REPLACE VIEW raw_contracts AS 
            SELECT 
                *
            FROM read_csv_auto('{0}', filename = true, sample_size=100000, types={1})
        """.format(CSV_FILES_PATH, "{'Referencia': 'VARCHAR'}")
        
        con.execute(view_sql)
        print(f"Successfully created/replaced view 'raw_contracts' in '{DATABASE_PATH}' pointing to '{CSV_FILES_PATH}'")
        
        # Verify by fetching a small sample (optional)
        count = con.execute("SELECT COUNT(*) FROM raw_contracts").fetchone()[0]
        if count > 0:
            print(f"View 'raw_contracts' contains {count} rows")
        else:
            print("View 'raw_contracts' is empty or no CSV files found.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'con' in locals() and con:
            con.close()

if __name__ == "__main__":
    print(f"Current working directory: {os.getcwd()}")
    print(f"Attempting to read CSVs from: {os.path.abspath(CSV_FILES_PATH)}")
    print(f"Attempting to create database at: {os.path.abspath(DATABASE_PATH)}")
    create_raw_contracts_model() 