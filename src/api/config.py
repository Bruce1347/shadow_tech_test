import os

TESTING = os.environ.get("TESTING", "false") == "true"
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "")
APP_TZ = os.environ.get("APP_TZ", "Europe/Paris")

JWT_TOKEN_EXPIRE_TIME = os.environ.get("JWT_TOKEN_EXPIRATION_TIME", 60)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", None)

# Default to HMAC & SHA 256
JWT_HASH_ALGORITHM = os.environ.get("JWT_HASH_ALGORITHM", "HS256")
