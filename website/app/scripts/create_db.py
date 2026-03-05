import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app
from app import db

def init_database():
    """Initialize the database by creating tables."""
    app = create_app()
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Tables created successfully")

def reset_database():
    """Delete all tables and recreate them."""
    app = create_app()
    with app.app_context():
        print("Deleting tables...")
        db.drop_all()
        print("Tables deleted")
        init_database()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag == "--reset":
            reset_database()
        else:
            print(f"Invalid flag: {flag}")
            print("Valid flag: --reset")
            print("No action was performed.")
    else:
        init_database()