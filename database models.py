# database_models.py

import os
import logging

import sqlalchemy as db
from dotenv import load_dotenv
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer, BigInteger
from sqlalchemy import String, Boolean
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# define global variables


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

Base = declarative_base()


# Database Models

# Global Class
class Global(Base):
    __tablename__ = "global_manager"
    # ID Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger())
    gm = Column(String())
    # Feature Flags
    explode = Column(Boolean(), default=False)
    aliases = Column(Boolean(), default=False)
    block = Column(Boolean(), default=False)
    system = Column(String(), default=None, nullable=True)
    # Initiative Tracker
    initiative = Column(Integer())
    round = Column(Integer(), default=0)
    saved_order = Column(String(), default='')
    tracker = Column(BigInteger(), nullable=True)
    tracker_channel = Column(BigInteger(), nullable=True, unique=True)
    gm_tracker = Column(BigInteger(), nullable=True)
    gm_tracker_channel = Column(BigInteger(), nullable=True, unique=True)
    rp_channel = Column(BigInteger(), nullable=True, unique=True)
    # Timekeeper Functionality
    timekeeping = Column(Boolean(), default=False)
    time = Column(BigInteger(), default=6, nullable=False)
    time_second = Column(Integer(), nullable=True)
    time_minute = Column(Integer(), nullable=True)
    time_hour = Column(Integer(), nullable=True)
    time_day = Column(Integer(), nullable=True)
    time_month = Column(Integer(), nullable=True)
    time_year = Column(Integer(), nullable=True)