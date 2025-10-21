import os
from dotenv import load_dotenv


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
PASSWORD_USER_DB = os.getenv("PASSWORD_USER_DB")
ALGORITHM = "HS256"