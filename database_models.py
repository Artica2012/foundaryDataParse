# database_models.py

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base

# define global variables

Base = declarative_base()


# Database Models

class NPC(Base):
    __tablename__ = "npc_data"
    # Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(), unique=True)
    level = Column(Integer())
    creatureType = Column(String())
    alignment = Column(String())
    ac = Column(Integer())
    hp = Column(Integer())
    init = Column(String())
    fort = Column(Integer())
    reflex = Column(Integer())
    will = Column(Integer())
    dc = Column(Integer())
    macros = Column(String())