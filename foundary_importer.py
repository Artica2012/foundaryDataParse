#founary_importer.py

# Impoart foundary PF2e data into a PostgreSQL database

import asyncio
import logging
from dotenv import load_dotenv
import json
import os
import aiohttp
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database_models import NPC, Base
from database_operations import get_db_engine

load_dotenv(verbose=True)
if os.environ['PRODUCTION'] == 'True':
    USERNAME = os.getenv('Username')
    PASSWORD = os.getenv('Password')
    HOSTNAME = os.getenv('Hostname')
    PORT = os.getenv('PGPort')
else:
    USERNAME = os.getenv('BETA_Username')
    PASSWORD = os.getenv('BETA_Password')
    HOSTNAME = os.getenv('BETA_Hostname')
    PORT = os.getenv('BETA_PGPort')

GUILD = os.getenv('GUILD')
SERVER_DATA = os.getenv('SERVERDATA')
DATABASE = os.getenv("DATABASE")

def import_bestiary(file:str):

    engine = get_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=DATABASE)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    try:
        with open(f"Data\\{file}") as f:
            # logging.info(f'{file}')
            data = json.load(f)
            if data['type'] == 'npc':

                dc = 0
                name = data['name']
                level = data['system']['details']['level']['value']
                creatureType = data['system']['details']['creatureType']
                alignment = data['system']['details']['alignment']['value']
                ac = data['system']['attributes']['ac']['value']
                hp = data['system']['attributes']['hp']['max']
                init = data['system']['attributes']['perception']['value']
                init_string = f"1d20+{init}"
                fort = data['system']['saves']['fortitude']['value']
                reflex = data['system']['saves']['reflex']['value']
                will = data['system']['saves']['will']['value']


                # print(f"name {name}, ac {ac}, hp {hp}, init_string {init_string}, fort {fort}, reflex {reflex}, will {will}")
                # print(f"level {level}, type: {creatureType}, alignment {alignment}")

                macro_list = []
                for index in data['items']:
                    if index['type'] == "spellcastingEntry":
                        dc = index['system']['spelldc']['dc']
                    if index['type'] == "melee":
                        mac_name = index['name']
                        mac_atk = index['system']['bonus']['value']
                        macro_atk = f"1d20+{mac_atk}"
                        # print(f"{mac_name}, {mac_atk}, {macro_atk}")
                        dmg_list = list(index['system']['damageRolls'].keys())
                        mac_dmg = ''
                        for x, dmg in enumerate(dmg_list):
                            dmg_str = index['system']['damageRolls'][dmg]['damage']
                            if x > 0:
                                mac_dmg += f"+{dmg_str}"
                            else:
                                mac_dmg += dmg_str
                        # print(mac_dmg)
                        macro_output = f"{mac_name}; {macro_atk}; {mac_dmg}::"
                        macro_list.append(macro_output)
                # print(f"dc: {dc}")

                # Write to the database
                with Session() as session:
                    new_entry = NPC(
                        name=name,
                        level=level,
                        creatureType=creatureType,
                        alignment=alignment,
                        ac=int(ac),
                        hp=int(hp),
                        init=init_string,
                        fort=int(fort),
                        reflex=int(reflex),
                        will=int(will),
                        dc=int(dc),
                        macros=''.join(macro_list)
                    )
                    session.add(new_entry)
                    try:
                        session.commit()
                    except IntegrityError as e:
                        if os.environ['Overwrite']=="True":
                            with Session() as session:
                                session.execute(update(NPC)
                                                .where(NPC.name == name)
                                                .values(
                                    name=name,
                                    level=level,
                                    creatureType=creatureType,
                                    alignment=alignment,
                                    ac=int(ac),
                                    hp=int(hp),
                                    init=init_string,
                                    fort=int(fort),
                                    reflex=int(reflex),
                                    will=int(will),
                                    dc=int(dc),
                                    macros=''.join(macro_list)
                                ))
                                session.commit()
                            logging.info(f"{name} overwritten")
                        else:
                            logging.info(f"Excepted {name}")
        return True
    except Exception as e:
        logging.warning(e)
        return False






logging.basicConfig(level=logging.INFO)
logging.info("Script Started")

# file_list = os.listdir(directory)


for file in os.listdir('Data'):
    # d=os.path.join('Data', file)
    logging.info(file)
    if os.path.isdir(file):
        for item in os.listdir(file):
            import_bestiary(item)
    else:
        if os.path.splitext(file)[1] == '.json':
            import_bestiary(file)
