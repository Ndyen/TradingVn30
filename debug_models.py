import sys
import os

try:
    print("Importing models...")
    from src.app.db.models import Base
    print("Models imported successfully.")
    print(f"Tables: {Base.metadata.tables.keys()}")
except Exception as e:
    print(f"Error importing models: {e}")
    import traceback
    traceback.print_exc()
