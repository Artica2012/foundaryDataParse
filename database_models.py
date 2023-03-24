# database_models.py

from sqlalchemy import Column, JSON, Boolean, BigInteger
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

class EPF_NPC(Base):
    __tablename__ = "EPF_npcs"

    # The original tracker table
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(), nullable=False, unique=True)
    max_hp = Column(Integer(), default=1)

    # General
    type = Column(String(), nullable=False)
    level = Column(Integer(), nullable=False)
    ac_base = Column(Integer(), nullable=False)
    class_dc = Column(Integer(), nullable=False)

    # Stats
    str = Column(Integer(), nullable=False)
    dex = Column(Integer(), nullable=False)
    con = Column(Integer(), nullable=False)
    itl = Column(Integer(), nullable=False)
    wis = Column(Integer(), nullable=False)
    cha = Column(Integer(), nullable=False)

    # Saves
    fort_prof = Column(Integer(), nullable=False)
    will_prof = Column(Integer(), nullable=False)
    reflex_prof = Column(Integer(), nullable=False)

    # Proficiencies
    perception_prof = Column(Integer(), nullable=False)

    arcane_prof = Column(Integer(), nullable=False)
    divine_prof = Column(Integer(), nullable=False)
    occult_prof = Column(Integer(), nullable=False)
    primal_prof = Column(Integer(), nullable=False)

    acrobatics_prof = Column(Integer(), nullable=False)
    arcana_prof = Column(Integer(), nullable=False)
    athletics_prof = Column(Integer(), nullable=False)
    crafting_prof = Column(Integer(), nullable=False)
    deception_prof = Column(Integer(), nullable=False)
    diplomacy_prof = Column(Integer(), nullable=False)
    intimidation_prof = Column(Integer(), nullable=False)
    medicine_prof = Column(Integer(), nullable=False)
    nature_prof = Column(Integer(), nullable=False)
    occultism_prof = Column(Integer(), nullable=False)
    performance_prof = Column(Integer(), nullable=False)
    religion_prof = Column(Integer(), nullable=False)
    society_prof = Column(Integer(), nullable=False)
    stealth_prof = Column(Integer(), nullable=False)
    survival_prof = Column(Integer(), nullable=False)
    thievery_prof = Column(Integer(), nullable=False)

    # Plan to save parsable lists here

    # Calculated stats
    resistance = Column(JSON())
    attacks = Column(JSON())
    spells = Column(JSON())

class EPF_Weapon(Base):
    __tablename__ = "EPF_item_data"
    # Columns
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(), unique=True)
    level = Column(Integer())
    base_item = Column(String(), unique=False)
    category = Column(String(), unique=False)
    damage_type = Column(String(), unique=False)
    damage_dice = Column(Integer())
    damage_die = Column(String(), unique=False)
    group = Column(String(), unique=False)
    range = Column(Integer())
    potency_rune = Column(Integer())
    striking_rune = Column(String(), unique=False)
    runes = Column(String())
    traits = Column(JSON())



