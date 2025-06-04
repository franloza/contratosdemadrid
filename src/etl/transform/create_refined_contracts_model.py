import duckdb
import os
from src.etl.config import OUTPUT_DIR, DATABASE_NAME

SQL_FILENAME = "refined_contracts.sql"

DATABASE_PATH = os.path.join(OUTPUT_DIR, DATABASE_NAME)

def main():
    try:
        script_dir = os.path.dirname(__file__)
        actual_sql_file_path = os.path.join(script_dir, SQL_FILENAME)
        with open(actual_sql_file_path, 'r') as f:
            full_sql_statement = f.read()
    except FileNotFoundError:
        print(f"Error: SQL file not found at {actual_sql_file_path}")
        return
    except Exception as e:
        print(f"Error reading SQL file: {e}")
        return

    if not full_sql_statement.strip():
        print(f"Error: SQL file {actual_sql_file_path} is empty.")
        return

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        con = duckdb.connect(database=DATABASE_PATH, read_only=False)
        print(f"Successfully connected to local DuckDB database at {DATABASE_PATH}.")

        print(f"Executing full SQL from {actual_sql_file_path} to create/replace view contracts.main.refined_contracts...")
        con.execute(full_sql_statement)
        print(f"View contracts.main.refined_contracts created/updated successfully in {DATABASE_PATH}.")

        con.close()
        print("Process completed.")

    except duckdb.IOException as e:
        if "Could not set lock on file" in str(e):
            print(f"A DuckDB IO error occurred, likely due to a conflicting file lock: {e}")
            print("Please ensure no other processes are using the database file and try again.")
        else:
            print(f"A DuckDB IO error occurred: {e}")
    except duckdb.Error as e:
        print(f"DuckDB database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 