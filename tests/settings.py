import os

TEST_DATABASE_URL = os.environ.get("DATABASE_URI", "mongodb://root:mongoadmin@localhost:27017")
