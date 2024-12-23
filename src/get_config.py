import os.path

from dotenv import load_dotenv

def get_config():
    """ Function to get DSN and token. Gets data from file 'config.env'."""

    dotenv_path = 'config.env'
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    database = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_USER_PASSWORD')
    DSN = f"postgresql://{user}:{password}@localhost:5432/{database}"
    token_bot = os.getenv('TG_TOKEN')
    return DSN, token_bot
