import os
from dotenv import load_dotenv

load_dotenv()

CLIENT = os.getenv('BZ_OAUTH_CLIENT')
TOKEN = os.getenv('BZ_OAUTH_TOKEN')

