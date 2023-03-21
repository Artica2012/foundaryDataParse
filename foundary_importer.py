# founary_importer.py

# Import foundary PF2e data into a PostgreSQL database

import asyncio
import io
import json
import logging
import os
import shutil
from zipfile import ZipFile

import requests
from sqlalchemy import update, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database_models import NPC, Base
from database_operations import USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE
from database_operations import get_db_engine, get_asyncio_db_engine

DOWNLOAD_URL = "https://github.com/foundryvtt/pf2e/archive/refs/heads/master.zip"
error_list = []


def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


async def get_data(data_path):
    try:
        logging.warning("Beginning download")
        zip_data = requests.get(DOWNLOAD_URL)
        logging.info(zip_data.status_code)
        z = ZipFile(io.BytesIO(zip_data.content))
        # z.printdir()
        z.extractall(data_path)
        # logging.warning(os.listdir(data_path))
        logging.warning("Data Extracted")
        return True
    except Exception as e:
        logging.warning(e)
        return False


async def delete_data(data_path):
    logging.warning("Clearing out data")
    for root, dirs, files in os.walk(data_path):
        print(root, dirs, files)
        for f in files:
            print(root, f)
            os.unlink(os.path.join(root, f))

        for d in dirs:
            print(root, d)
            shutil.rmtree(os.path.join(root, d))
    logging.warning("Data Cleared")


async def import_data(file:str, async_session):
    return await import_bestiary(file, async_session)

async def import_bestiary(file: str, async_session):
    try:
        with open(f"{file}", encoding='utf8') as f:
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
                try:
                    async with async_session() as session:
                        async with session.begin():
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
                            await session.commit()
                            logging.info(f"{name} written")
                            return 1
                except IntegrityError as e:
                    if os.environ['Overwrite'] == "True":
                        async with async_session() as session:
                            npc_result = await session.execute(select(NPC).where(NPC.name == name))
                            npc = npc_result.scalars().one()

                            npc.name = name
                            npc.level = level
                            npc.creatureType = creatureType
                            npc.alignment = alignment
                            npc.ac = int(ac)
                            npc.hp = int(hp)
                            npc.init = init_string
                            npc.fort = int(fort)
                            npc.reflex = int(reflex)
                            npc.will = int(will)
                            npc.dc = int(dc)
                            npc.macros = ''.join(macro_list)

                        await session.commit()
                        logging.info(f"{name} overwritten")
                        return 2
                    else:
                        logging.info(f"Excepted {name}")
                        return 3
        return True
    except Exception:
        # logging.warning(e)
        error_list.append(file)
        return 4

async def EPF_import_bestiary(file, async_session):
    with open(f"{file}", encoding='utf8') as f:
        # logging.info(f'{file}')
        data = json.load(f)
        if data['type'] == 'npc':

            dc=0
            name = data['name']
            type = data["system"]["details"]["creatureType"]
            level = data['system']['details']['level']['value']
            ac = data['system']['attributes']['ac']['value']
            hp = data['system']['attributes']['hp']['max']
            init = data['system']['attributes']['perception']['value']

            str = (data["system"]['abilities']["str"]["mod"] * 2) + 10
            dex = (data["system"]['abilities']["dex"]["mod"] * 2) + 10
            con = (data["system"]['abilities']["con"]["mod"] * 2) + 10
            itl = (data["system"]['abilities']["int"]["mod"] * 2) + 10
            wis = (data["system"]['abilities']["wis"]["mod"] * 2) + 10
            cha = (data["system"]['abilities']["cha"]["mod"] * 2) + 10

            fort_prof = data['system']['saves']["fortitude"]["value"] - level - data["system"]['abilities']["con"]["mod"]
            reflex_prof = data['system']['saves']["reflex"]["value"] - level - data["system"]['abilities']["dex"]["mod"]
            will_prof = data['system']['saves']["will"]["value"] - level - data["system"]['abilities']["wis"]["mod"]
            perception_prof = data['system']['attributes']['perception']["value"] - level - data["system"]['abilities']["wis"]["mod"]


            for index in data['items']:
                if index['type'] == "spellcastingEntry":
                    dc = index['system']['spelldc']['dc']
                if index['type'] == "melee":


            resistance = {
                "resist":{},
                "weak": {},
                "immune": {}
            }
            for item in data['system']['attributes']['resistances']:
                resistance["resist"][item["type"]] = item["value"]
            for item in data['system']['attributes']['weaknesses']:
                resistance["weak"][item["type"]] = item["value"]
            for item in data['system']['attributes']['immunities']:
                resistance["immune"][item["type"]] = "immune"

        try:
            async with async_session() as session:
                async with session.begin():
                    new_entry = NPC(
                        name=name,
                        max_hp=hp,
                        type=type,
                        level=level,
                        ac_base=ac,
                        class_dc=dc,  # May need to get more granular with this
                        str=str,
                        dex=dex,
                        con=con,
                        itl=itl,
                        wis=wis,
                        cha=cha,
                        fort_prof=fort_prof,
                        reflex_prof=reflex_prof,
                        will_prof=will_prof,
                        perception_prof=perception_prof,





                    )
                    session.add(new_entry)
                    await session.commit()
                    logging.info(f"{name} written")
                    return 1
        except IntegrityError as e:
            pass




async def main():
    logging.basicConfig(level=logging.WARNING)
    logging.warning("Script Started")
    path = os.getcwd() + '/Data/'
    logging.warning(path)
    data_path = f"{path}pf2e-master/packs/data/"
    logging.warning(data_path)
    repeat = True

    while repeat:

        results = {
            "written": 0,
            "overwritten": 0,
            "excepted": 0,
            "error": 0
        }

        # Download the data and unzip
        if await get_data(path):
            # if True:

            engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=DATABASE)
            # Base.metadata.create_all(engine)
            Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

            # list_files(data_path)

            for file in os.listdir(data_path):
                # print(file)
                await asyncio.sleep(0)
                logging.warning(file)
                try:
                    if os.path.splitext(file)[1] == '.db':
                        logging.info(f"Its a directory: {file}")
                        d = f"{data_path}{file}"
                        for item in os.listdir(d):
                            await asyncio.sleep(0)
                            try:
                                path = os.path.join(d, item)
                                result = await import_data(path, Session)
                                if result == 1:
                                    results["written"] += 1
                                elif result == 2:
                                    results["overwritten"] += 1
                                elif result == 3:
                                    results["excepted"] += 1
                                elif result == 4:
                                    results["error"] += 1
                            except Exception as e:
                                logging.warning(f"{item}, {e}")
                    else:
                        try:
                            if os.path.splitext(file)[1] == '.json':
                                path = os.path.join('Data', file)
                                result = await import_data(path)
                                if result == 1:
                                    results["written"] += 1
                                elif result == 2:
                                    results["overwritten"] += 1
                                elif result == 3:
                                    results["excepted"] += 1
                                elif result == 4:
                                    results["error"] += 1
                        except Exception as e:
                            logging.warning(f"{file}, {e}")
                except Exception as e:
                    logging.warning(f"{file}, {e}")

            summary_string = (f"Database Update Summary\n"
                              f" Written: {results['written']}\n"
                              f" Overwritten: {results['overwritten']}\n"
                              f" Excepted: {results['excepted']}\n"
                              f" Error: {results['error']}\n\n")

            for item in error_list:
                summary_string = summary_string + f"\n   {item}"
            logging.warning(summary_string)
            await delete_data(f"{path}/pf2e-master")
            logging.warning("Completed Successfully")
        else:
            logging.warning("Unsuccessful. Aborting")

        await asyncio.sleep(86400)



asyncio.run(main())
