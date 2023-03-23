# founary_importer.py

# Import foundary PF2e data into a PostgreSQL database

import asyncio
import io
import json
import logging
import os
import re
import shutil
from zipfile import ZipFile

import requests
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database_models import NPC, Base, EPF_NPC
from database_operations import USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE
from database_operations import get_asyncio_db_engine

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


async def import_data(file: str, async_session):
    pf2_result = await import_bestiary(file, async_session)
    epf_result = await EPF_import_bestiary(file, async_session)
    return epf_result


async def import_bestiary(file: str, async_session):
    try:
        with open(f"{file}", encoding='utf8') as f:
            # logging.info(f'{file}')
            data = json.load(f)
            if "type" in data.keys() and data['type'] == 'npc':

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
    # try:
    with open(f"{file}", encoding='utf8') as f:
        # logging.info(f'{file}')
        data = json.load(f)
        if "type" in data.keys() and data['type'] == 'npc':

            dc = 0
            attacks = {}
            spells = []
            name = data['name']
            print(name)
            type = data["system"]["details"]["creatureType"]
            level = data['system']['details']['level']['value']
            ac = data['system']['attributes']['ac']['value']
            hp = data['system']['attributes']['hp']['max']
            init = data['system']['attributes']['perception']['value']

            str_mod = data["system"]['abilities']["str"]["mod"]
            str = (str_mod * 2) + 10
            dex_mod = data["system"]['abilities']["dex"]["mod"]
            dex = ( dex_mod* 2) + 10
            con_mod = data["system"]['abilities']["con"]["mod"]
            con = (con_mod * 2) + 10
            itl_mod = data["system"]['abilities']["int"]["mod"]
            itl = (itl_mod * 2) + 10
            wis_mod = data["system"]['abilities']["wis"]["mod"]
            wis = (wis_mod * 2) + 10
            cha_mod = data["system"]['abilities']["cha"]["mod"]
            cha = (cha_mod * 2) + 10

            fort_prof = data['system']['saves']["fortitude"]["value"] - level - con_mod
            reflex_prof = data['system']['saves']["reflex"]["value"] - level - dex_mod
            will_prof = data['system']['saves']["will"]["value"] - level - wis_mod
            perception_prof = data['system']['attributes']['perception']["value"] - level - wis_mod

            arcane_prof = 0
            divine_prof = 0
            occult_prof = 0
            primal_prof = 0
            acrobatics_prof = 0
            arcana_prof = 0
            athletics_prof = 0
            crafting_prof = 0
            deception_prof = 0
            diplomacy_prof = 0
            intimidation_prof = 0
            medicine_prof = 0
            nature_prof = 0
            occultism_prof = 0
            performance_prof = 0
            religion_prof = 0
            society_prof = 0
            stealth_prof = 0
            survival_prof = 0
            thievery_prof = 0
            for index in data['items']:
                if index['type'] == "spellcastingEntry":
                    dc = index['system']['spelldc']['dc']
                    if index["system"]["tradition"] == "occult":
                        occult_prof = index['system']['spelldc']['value'] - level - cha_mod
                    elif index["system"]["tradition"] == "arcane":
                        arcane_prof = index['system']['spelldc']['value'] - level - itl_mod
                    elif index["system"]["tradition"] == "primal":
                        primal_prof = index['system']['spelldc']['value'] - level - cha_mod
                    elif index["system"]["tradition"] == "divine":
                        divine_prof = index['system']['spelldc']['value'] - level - wis_mod
                elif index["type"] == "lore":
                    match index["name"]:
                        case "Acrobatics":
                            acrobatics_prof = index["system"]["mod"]["value"] - level - dex_mod
                        case "Arcana":
                            arcane_prof = index["system"]["mod"]["value"] - level - itl_mod
                        case "Athletics":
                            athletics_prof = index["system"]["mod"]["value"] - level - str_mod
                        case "Crafting":
                            athletics_prof = index["system"]["mod"]["value"] - level - itl_mod
                        case "Deception":
                            deception_prof = index["system"]["mod"]["value"] - level - cha_mod
                        case "Diplomacy":
                            diplomacy_prof = index["system"]["mod"]["value"] - level - cha_mod
                        case "Intimidation":
                            intimidation_prof = index["system"]["mod"]["value"] - level - cha_mod
                        case "Medicine":
                            medicine_prof = index["system"]["mod"]["value"] - level - wis_mod
                        case "Nature":
                            nature_prof = index["system"]["mod"]["value"] - level - wis_mod
                        case "Occultism":
                            occultism_prof = index["system"]["mod"]["value"] - level - itl_mod
                        case "Performance":
                            performance_prof = index["system"]["mod"]["value"] - level - cha_mod
                        case "Religion":
                            religion_prof = index["system"]["mod"]["value"] - level - wis_mod
                        case "Society":
                            society_prof = index["system"]["mod"]["value"] - level - itl_mod
                        case "Stealth":
                            stealth = index["system"]["mod"]["value"] - level - dex_mod
                        case "Survival":
                            survival_prof = index["system"]["mod"]["value"] - level - wis_mod
                        case "Thievery":
                            thievery_prof = index["system"]["mod"]["value"] - level - dex_mod
                elif index['type'] == "melee":
                    # print(index["name"])
                    attack_data = {}
                    attack_data["bonus"] = []
                    attack_data["runes"] = []
                    attack_data["display"] = index["name"]
                    attack_data["prof"] = "NPC"
                    attack_data["name"] = None
                    if index["system"]["weaponType"]["value"] == "ranged":
                        attack_data["attk_stat"] = "dex"
                    else:
                        attack_data["attk_stat"] = "str"
                    attack_data["pot"] = index["system"]["bonus"]["value"] - level - str_mod
                    attack_data["traits"] = index["system"]["traits"]["value"]
                    attack_data["crit"] = "*2"

                    for item in index["system"]["traits"]["value"]:
                        if "deadly" in item:
                            string = item.split("-")
                            attack_data["crit"] = f"*2 + {string[1]}"
                        if "agile" in item and dex_mod > str_mod:
                            print("Agile")
                            attack_data["attk_stat"] = "dex"
                            attack_data["pot"] = index["system"]["bonus"]["value"] - level - dex_mod

                    dmg_list = []
                    for key, value in index["system"]["damageRolls"].items():
                        dmg_list.append(value)
                    for x, item in enumerate(dmg_list):
                        if x == 0:
                            dmg_split = re.split("d|\+|-", item["damage"])
                            # print(data)
                            try:
                                attack_data["die"] = dmg_split[1]
                            except IndexError:
                                attack_data["die"] = 1
                            attack_data["die_num"] = dmg_split[0]
                            try:
                                attack_data["stat"] = dmg_split[2]
                            except IndexError:
                                attack_data["stat"] = 0
                            attack_data["dmg_type"] = item["damageType"]
                        else:
                            bns_dmg = {
                                "damage": item["damage"],
                                "dmg_type": item["damageType"]
                            }
                            attack_data["bonus"].append(bns_dmg)
                    attacks[index["name"]] = attack_data
                elif index["type"] == "spell":
                    try:
                        spells.append({
                            "name": index["name"],
                            "level": index["level"]["value"]
                        })
                    except Exception:
                        pass



            resistance = {
                "resist": {},
                "weak": {},
                "immune": {}
            }
            if "resistances" in data["system"]["attributes"].keys():
                for item in data['system']['attributes']['resistances']:
                    resistance["resist"][item["type"]] = item["value"]
            if "weaknesses" in data["system"]["attributes"].keys():
                for item in data['system']['attributes']['weaknesses']:
                    resistance["weak"][item["type"]] = item["value"]
            if "immunities" in data["system"]["attributes"].keys():
                for item in data['system']['attributes']['immunities']:
                    resistance["immune"][item["type"]] = "immune"

            try:
                async with async_session() as session:
                    async with session.begin():
                        new_entry = EPF_NPC(
                            name=name,
                            max_hp=int(hp),
                            type=type,
                            level=int(level),
                            ac_base=int(ac),
                            class_dc=int(dc),  # May need to get more granular with this
                            str=int(str),
                            dex=int(dex),
                            con=int(con),
                            itl=int(itl),
                            wis=int(wis),
                            cha=int(cha),
                            fort_prof=fort_prof,
                            reflex_prof=reflex_prof,
                            will_prof=will_prof,
                            perception_prof=perception_prof,
                            arcane_prof=arcane_prof,
                            divine_prof=divine_prof,
                            occult_prof=occult_prof,
                            primal_prof=primal_prof,
                            acrobatics_prof=acrobatics_prof,
                            arcana_prof=arcana_prof,
                            athletics_prof=athletics_prof,
                            crafting_prof=crafting_prof,
                            deception_prof=deception_prof,
                            diplomacy_prof=diplomacy_prof,
                            intimidation_prof=intimidation_prof,
                            medicine_prof=medicine_prof,
                            nature_prof=nature_prof,
                            occultism_prof=occultism_prof,
                            performance_prof=performance_prof,
                            religion_prof=religion_prof,
                            society_prof=society_prof,
                            stealth_prof=stealth_prof,
                            survival_prof=survival_prof,
                            thievery_prof=thievery_prof,
                            resistance=resistance,
                            attacks=attacks,
                            spells=spells

                        )
                        session.add(new_entry)
                        await session.commit()
                        logging.info(f"{name} written")
                        return 1
            except IntegrityError as e:
                if os.environ['Overwrite'] == "True":
                    async with async_session() as session:
                        npc_result = await session.execute(select(EPF_NPC).where(EPF_NPC.name == name))
                        npc = npc_result.scalars().one()

                        npc.name = name,
                        npc.max_hp = int(hp),
                        npc.type = type,
                        npc.level = int(level),
                        npc.ac_base = int(ac),
                        npc.class_dc = int(dc),  # May need to get more granular with this
                        npc.str = int(str),
                        npc.dex = int(dex),
                        npc.con = int(con),
                        npc.itl = int(itl),
                        npc.wis = int(wis),
                        npc.cha = int(cha),
                        npc.fort_prof = fort_prof,
                        npc.reflex_prof = reflex_prof,
                        npc.will_prof = will_prof,
                        npc.perception_prof = perception_prof,
                        npc.arcane_prof = arcane_prof,
                        npc.divine_prof = divine_prof,
                        npc.occult_prof = occult_prof,
                        npc.primal_prof = primal_prof,
                        npc.acrobatics_prof = acrobatics_prof,
                        npc.arcana_prof = arcana_prof,
                        npc.athletics_prof = athletics_prof,
                        npc.crafting_prof = crafting_prof,
                        npc.deception_prof = deception_prof,
                        npc.diplomacy_prof = diplomacy_prof,
                        npc.intimidation_prof = intimidation_prof,
                        npc.medicine_prof = medicine_prof,
                        npc.nature_prof = nature_prof,
                        npc.occultism_prof = occultism_prof,
                        npc.performance_prof = performance_prof,
                        npc.religion_prof = religion_prof,
                        npc.society_prof = society_prof,
                        npc.stealth_prof = stealth_prof,
                        npc.survival_prof = survival_prof,
                        npc.thievery_prof = thievery_prof,
                        npc.resistance = resistance,
                        npc.attacks = attacks,
                        npc.spells = spells
                    await session.commit()
                    logging.info(f"{name} overwritten")
                    print(attacks)
                    return 2
                else:
                    logging.info(f"Excepted {name}")
                    return 3
    # except Exception:
    #     # logging.warning(e)
    #     error_list.append(file)
    #     return 4



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
        # if await get_data(path):
        if True:

            engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=DATABASE)
            Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            # list_files(data_path)

            for file in os.listdir(data_path):
                # print(file)
                await asyncio.sleep(0)
                logging.warning(file)
                # try:
                if os.path.splitext(file)[1] == '.db':
                    logging.info(f"Its a directory: {file}")
                    d = f"{data_path}{file}"
                    for item in os.listdir(d):
                        await asyncio.sleep(0)
                        # try:
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
                        # except Exception as e:
                        #     logging.warning(f"{item}, {e}")
                else:
                    # try:
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
                    # except Exception as e:
                    #     logging.warning(f"{file}, {e}")
                # except Exception as e:
                #     logging.warning(f"{file}, {e}")

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
            await engine.dispose()
        else:
            logging.warning("Unsuccessful. Aborting")

        await asyncio.sleep(86400)


asyncio.run(main())
