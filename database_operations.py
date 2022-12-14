# database_operations.py
import logging
import os

import sqlalchemy as db
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import select, inspect
# imports
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session

from database_models import NPC, Base

load_dotenv(verbose=True)
if os.environ['PRODUCTION'] == 'True':
    TOKEN = os.getenv('TOKEN')
    USERNAME = os.getenv('Username')
    PASSWORD = os.getenv('Password')
    HOSTNAME = os.getenv('Hostname')
    PORT = os.getenv('PGPort')
else:
    TOKEN = os.getenv('BETA_TOKEN')
    USERNAME = os.getenv('BETA_Username')
    PASSWORD = os.getenv('BETA_Password')
    HOSTNAME = os.getenv('BETA_Hostname')
    PORT = os.getenv('BETA_PGPort')

GUILD = os.getenv('GUILD')
SERVER_DATA = os.getenv('SERVERDATA')
DATABASE = os.getenv('DATABASE')


# Get the engine
def get_asyncio_db_engine(user, password, host, port, db):
    url = f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}'
    # print(url)
    # if not database_exists(url):
    #     create_database(url)
    engine = create_async_engine(url, echo=False, pool_size=20, max_overflow=-1)
    return engine


def get_db_engine(user, password, host, port, db):
    url = f'postgresql://{user}:{password}@{host}:{port}/{db}'
    # print(url)
    # if not database_exists(url):
    #     create_database(url)
    engine = create_engine(url, pool_size=10, echo=False)
    return engine