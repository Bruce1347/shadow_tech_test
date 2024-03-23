import os

TESTING = os.environ.get("TESTING", "false") == "true"
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
