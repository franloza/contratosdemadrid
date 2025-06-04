# src/config.py
import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../app/sources/contracts"))

DATABASE_NAME = "contracts.duckdb"