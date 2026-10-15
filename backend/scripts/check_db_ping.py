import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ConfigurationError

backend_dir = Path(__file__).resolve().parents[1]
load_dotenv(backend_dir / '.env')

uri = os.getenv('MONGODB_URI')
if not uri:
    print("ERROR: MONGODB_URI environment variable is missing in backend/.env")
    sys.exit(1)

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    # Ping the admin database
    res = client.admin.command('ping')
    db_name = client.get_default_database().name if client.get_default_database() is not None else 'candidate_comm'
    db = client[db_name or 'candidate_comm']
    cols = db.list_collection_names()
    print(f"SUCCESS: Successfully pinged MongoDB Atlas. Database: '{db.name}', Collections: {len(cols)}")
    sys.exit(0)
except Exception as e:
    # Print error class and message, but never print the URI
    err_msg = str(e)
    # Redact any accidental URI string if present
    if '@' in err_msg:
        err_msg = err_msg.split('@')[-1]
    print(f"FAILED: MongoDB Atlas ping failed: {type(e).__name__}: {err_msg}")
    sys.exit(1)
