# founary_importer.py

# Import foundary PF2e data into a PostgreSQL database

import asyncio
import io
import logging
import os
import shutil
from zipfile import ZipFile

import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from Wanderer import wander

import EPF_Import_Functions
import database_models
from EPF_Import_Functions import EPF_import_bestiary, EPF_import_weapon, EPF_import_equipment, EPF_import_spells
from PF2_Import_Functions import import_bestiary
from database_models import Base
from database_operations import USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE
from database_operations import get_asyncio_db_engine

engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=DATABASE)

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
        # print(root, dirs, files)
        for f in files:
            # print(root, f)
            os.unlink(os.path.join(root, f))

        for d in dirs:
            # print(root, d)
            shutil.rmtree(os.path.join(root, d))
    logging.warning("Data Cleared")


async def import_data(file: str, ledger, async_session):
    ledger = await tally_results(await import_bestiary(file, async_session), ledger, "PF2_NPCs")
    ledger = await tally_results(await EPF_import_bestiary(file, async_session), ledger, "EPF_NPCs")
    ledger = await tally_results(await EPF_import_weapon(file, async_session), ledger, "EPF_Weapon")
    ledger = await tally_results(await EPF_import_equipment(file, async_session), ledger, "EPF_Equipment")
    ledger = await tally_results(await EPF_import_spells(file, async_session), ledger, "EPF_Spells")
    return ledger


async def tally_results(result: int, ledger: dict, category: str):
    # print(result)
    if result == 1:
        ledger[category]["written"] += 1
    elif result == 2:
        ledger[category]["overwritten"] += 1
    elif result == 3:
        ledger[category]["excepted"] += 1
    elif result == 4:
        ledger[category]["error"] += 1
        print("ERROR!!!!!!!!!!!!!!!!!!!!!!!")

    return ledger


async def foundary_import():
    logging.basicConfig(level=logging.WARNING)
    logging.warning("Script Started")
    repeat = True
    path = os.getcwd() + '/Data/'
    logging.warning(path)
    data_path = f"{path}pf2e-master/packs/"
    logging.warning(data_path)
    # while repeat:
    results = {
        "PF2_NPCs": {
            "written": 0,
            "overwritten": 0,
            "excepted": 0,
            "error": 0
        },
        "EPF_NPCs": {
            "written": 0,
            "overwritten": 0,
            "excepted": 0,
            "error": 0
        },
        "EPF_Weapon": {
            "written": 0,
            "overwritten": 0,
            "excepted": 0,
            "error": 0
        },
        "EPF_Equipment": {
            "written": 0,
            "overwritten": 0,
            "excepted": 0,
            "error": 0
        },
        "EPF_Spells": {
            "written": 0,
            "overwritten": 0,
            "excepted": 0,
            "error": 0
        }

    }

    # Download the data and unzip
    if await get_data(path):
    # if True:

        Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # list_files(data_path)

        for file in os.listdir(data_path):
            # print(file)
            await asyncio.sleep(0)
            logging.warning(file)
            try:
                if os.path.splitext(file)[1] != '.JSON':
                    logging.info(f"Its a directory: {file}")
                    d = f"{data_path}{file}"
                    for item in os.listdir(d):
                        await asyncio.sleep(0)
                        try:
                            file_path = os.path.join(d, item)
                            results = await import_data(file_path, results, Session)

                        except Exception as e:
                            logging.warning(f"{item}, {e}")
                else:
                    try:
                        if os.path.splitext(file)[1] == '.json':
                            file_path = os.path.join('Data', file)
                            print(file_path)
                            results = await import_data(file_path, results, Session)

                    except Exception as e:
                        logging.warning(f"{file}, {e}")
            except Exception as e:
                logging.warning(f"{file}, {e}")
        summary_string = f"Database Update Summary\n"
        for key in results.keys():
            result_string = (f"{key}\n"
                             f"  Written: {results[key]['written']}"
                             f"  Overwritten: {results[key]['overwritten']}"
                             f"  Excepted: {results[key]['excepted']}"
                             f"  Error: {results[key]['error']}\n")
            summary_string = summary_string + result_string

        for item in error_list:
            summary_string = summary_string + f"\n   {item}"
        logging.warning(summary_string)
        # await delete_data(f"{path}/pf2e-master")
        logging.warning("Completed Successfully")
        # print(database_models.excepted_spells)
        # print("\nResistances\n")
        # print(EPF_Import_Functions.resistances)
        # print("\nDamage Types\n")
        # print(EPF_Import_Functions.damages)

    else:
        logging.warning("Unsuccessful. Aborting")


async def main():
    while True:
        await foundary_import()
        await wander()
        await asyncio.sleep(86400)


asyncio.run(main())
