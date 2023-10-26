import json
import logging
import os
import re
from math import ceil

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database_models import EPF_NPC, EPF_Weapon, EPF_Equipment, EPF_Spells, excepted_spells

resistances = []
damages = []


async def EPF_import_bestiary(file, async_session):
    try:
        with open(f"{file}", encoding='utf8') as f:
            # logging.info(f'{file}')
            data = json.load(f)
            # print(data['name'])
            if "type" in data.keys() and data['type'] == 'npc':

                dc = 0
                attacks = {}
                name = data['name']
                # print(name)
                type = data["system"]["details"]["creatureType"]
                level = data['system']['details']['level']['value']
                ac = data['system']['attributes']['ac']['value']
                hp = data['system']['attributes']['hp']['max']
                init = data['system']['attributes']['perception']['value']

                str_mod = data["system"]['abilities']["str"]["mod"]
                str = (str_mod * 2) + 10
                dex_mod = data["system"]['abilities']["dex"]["mod"]
                dex = (dex_mod * 2) + 10
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
                spells = {}
                spell_dc = 0
                spell_mod = 0

                for index in data['items']:
                    if index['type'] == "spellcastingEntry":
                        dc = int(index['system']['spelldc']['dc'])
                        spell_dc = dc
                        spell_mod = int(index["system"]["spelldc"]["value"])
                        if index["system"]["tradition"] == "occult":
                            occult_prof = index['system']['spelldc']['value'] - level - cha_mod
                        elif index["system"]["tradition"] == "arcane":
                            arcane_prof = index['system']['spelldc']['value'] - level - itl_mod
                        elif index["system"]["tradition"] == "primal":
                            primal_prof = index['system']['spelldc']['value'] - level - cha_mod
                        elif index["system"]["tradition"] == "divine":
                            divine_prof = index['system']['spelldc']['value'] - level - wis_mod
                    elif index["type"] == "spell":
                        # print(index["name"])
                        if (index["system"]["spellType"]["value"] == "save" or index["system"]["spellType"]["value"] == "attack") and index["system"]["damage"]["value"] != {}:
                            spell_data = {}
                            spell_data["level"] = index["system"]["level"]["value"]
                            if "heightenedLevel" in index["system"]["location"].keys():
                                spell_data["cast_level"] = index["system"]["location"]["heightenedLevel"]
                            else:
                                if "cantrip" in index["system"]["traits"]["value"]:
                                    spell_data["cast_level"] = ceil(level/2)
                                else:
                                    spell_data["cast_level"] = index["system"]["level"]["value"]
                            spell_data["tradition"] = "NPC"
                            spell_data["ability"] = "cha"
                            spell_data["proficiency"] = spell_mod - level - cha_mod
                            spell_data["dc"] = spell_dc - level - cha_mod
                            spell_data["type"] = index["system"]["spellType"]["value"]
                            spell_data["save"] = index["system"]["save"]
                            damage = {}
                            try:
                                for key in index["system"]["damage"]["value"].keys():
                                    damage[key] = {
                                        "mod": index["system"]["damage"]["value"][key]["applyMod"],
                                        "value": index["system"]["damage"]["value"][key]["value"],
                                        "dmg_type": index["system"]["damage"]["value"][key]["type"]["value"]
                                    }
                                    if index["system"]["damage"]["value"][key]["type"]["value"] not in damages:
                                        damages.append(index["system"]["damage"]["value"][key]["type"]["value"])
                            except Exception:
                                try:
                                    damage["value"] = {
                                        "mod": index["system"]["damage"]["value"]["applyMod"],
                                        "value": index["system"]["damage"]["value"]["value"],
                                        "dmg_type": index["system"]["damage"]["value"]["type"]["value"]
                                    }
                                    if index["system"]["damage"]["value"][key]["type"]["value"] not in damages:
                                        damages.append(index["system"]["damage"]["value"][key]["type"]["value"])
                                except Exception:
                                    for key in index['system']['damage']['value'].keys():
                                        damage[key] = {
                                            "mod": False,
                                            "value": index["system"]["damage"]["value"][key]["value"],
                                            "dmg_type": index["system"]["damage"]["value"][key]["type"]["value"]
                                        }
                                        if index["system"]["damage"]["value"][key]["type"]["value"] not in damages:
                                            damages.append(index["system"]["damage"]["value"][key]["type"]["value"])
                            spell_data["damage"] = damage

                            if "heightening" in index["system"].keys():
                                try:
                                    if index["system"]["heightening"]["type"] == "fixed":
                                        heightening = {
                                            "type": index["system"]["heightening"]["type"],
                                            "interval": index["system"]["heightening"]["levels"],
                                        }
                                    else:
                                        heightening = {
                                            "type": index["system"]["heightening"]["type"],
                                            "interval": index["system"]["heightening"]["interval"],
                                            "damage": index["system"]["heightening"]["damage"]
                                        }
                                except KeyError:
                                    heightening = {
                                        "type": "",
                                        "interval": 0,
                                        "damage": ""
                                    }
                            else:
                                heightening = {
                                    "type": "",
                                    "interval": 0,
                                    "damage": ""
                                }
                            spell_data["heightening"] = heightening

                            spells[index["name"]] = spell_data

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
                                stealth_prof = index["system"]["mod"]["value"] - level - dex_mod
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
                            attack_data["pot"] = index["system"]["bonus"]["value"] - level - dex_mod
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
                                # print("Agile")
                                attack_data["attk_stat"] = "dex"
                                attack_data["pot"] = index["system"]["bonus"]["value"] - level - dex_mod

                        dmg_list = []
                        for key, value in index["system"]["damageRolls"].items():
                            dmg_list.append(value)
                        for x, item in enumerate(dmg_list):
                            try:
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
                                    if item["damageType"] not in damages:
                                        damages.append(item["damageType"])
                                else:
                                    bns_dmg = {
                                        "damage": item["damage"],
                                        "dmg_type": item["damageType"]
                                    }
                                    if item["damageType"] not in damages:
                                        damages.append(item["damageType"])
                                    attack_data["bonus"].append(bns_dmg)
                            except Exception:
                                pass
                        attacks[index["name"]] = attack_data


                resistance = {
                    "resist": {},
                    "weak": {},
                    "immune": {}
                }
                if "resistances" in data["system"]["attributes"].keys():
                    for item in data['system']['attributes']['resistances']:
                        if "exceptions" in item.keys():
                            item_name = item['type'].lower()
                            exceptions = item['exceptions']
                            value = item['value']

                            resistance['resist'][item_name] = {
                                "exceptions": exceptions,
                                'value': value
                            }
                        else:
                            resistance["resist"][item["type"].lower()] = item["value"]


                        if item["type"] not in resistances:
                            resistances.append(item["type"])
                if "weaknesses" in data["system"]["attributes"].keys():
                    for item in data['system']['attributes']['weaknesses']:
                        if "exceptions" in item.keys():
                            item_name = item['type'].lower()
                            exceptions = item['exceptions']
                            value = item['value']

                            resistance['weak'][item_name] = {
                                "exceptions": exceptions,
                                'value': value
                            }
                        else:
                            resistance["weak"][item["type"].lower()] = item["value"]



                        if item["type"] not in resistances:
                            resistances.append(item["type"])
                if "immunities" in data["system"]["attributes"].keys():
                    for item in data['system']['attributes']['immunities']:
                        if "exceptions" in item.keys():
                            item_name = item['type'].lower()
                            exceptions = item['exceptions']
                            value = 1

                            resistance['immune'][item_name] = {
                                "exceptions": exceptions,
                                'value': value
                            }
                        else:
                            resistance["immune"][item["type"].lower()] = "immune"

                        if item["type"] not in resistances:
                            resistances.append(item["type"])

                if 'initiative' in data['system']['attributes'].keys():
                    if data['system']['attributes']['initiative']['statistic'] != "perception":
                        init_skill = data['system']['attributes']['initiative']['statistic']
                        print(f"{name} - Init Skill: {init_skill}")
                        try:
                            resistance['other']['init-skill'] = init_skill
                        except KeyError:
                            resistance['other'] = {}
                            resistance['other']['init-skill'] = init_skill



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
                        # print(f"Overwriting {name}")
                        async with async_session() as session:
                            npc_result = await session.execute(select(EPF_NPC).where(EPF_NPC.name == name))
                            npc = npc_result.scalars().one()

                            npc.name = name
                            npc.max_hp = int(hp)
                            npc.type = type
                            npc.level = int(level)
                            npc.ac_base = int(ac)
                            npc.class_dc = int(dc)  # May need to get more granular with this
                            npc.str = int(str)
                            npc.dex = int(dex)
                            npc.con = int(con)
                            npc.itl = int(itl)
                            npc.wis = int(wis)
                            npc.cha = int(cha)
                            npc.fort_prof = fort_prof
                            npc.reflex_prof = reflex_prof
                            npc.will_prof = will_prof
                            npc.perception_prof = perception_prof
                            npc.arcane_prof = arcane_prof
                            npc.divine_prof = divine_prof
                            npc.occult_prof = occult_prof
                            npc.primal_prof = primal_prof
                            npc.acrobatics_prof = acrobatics_prof
                            npc.arcana_prof = arcana_prof
                            npc.athletics_prof = athletics_prof
                            npc.crafting_prof = crafting_prof
                            npc.deception_prof = deception_prof
                            npc.diplomacy_prof = diplomacy_prof
                            npc.intimidation_prof = intimidation_prof
                            npc.medicine_prof = medicine_prof
                            npc.nature_prof = nature_prof
                            npc.occultism_prof = occultism_prof
                            npc.performance_prof = performance_prof
                            npc.religion_prof = religion_prof
                            npc.society_prof = society_prof
                            npc.stealth_prof = stealth_prof
                            npc.survival_prof = survival_prof
                            npc.thievery_prof = thievery_prof
                            npc.resistance = resistance
                            npc.attacks = attacks
                            npc.spells = spells

                            await session.commit()
                        logging.info(f"{name} overwritten")
                        return 2
                    else:
                        logging.info(f"Excepted {name}")
                        return 3
            elif "type" in data.keys() and data['type'] == 'hazard':
                try:
                    name = data['name']
                    # print(name)
                    if data["system"]["details"]["isComplex"]:
                        type = "Complex Hazard"
                    else:
                        type = "Hazard"
                    level = data['system']['details']['level']['value']
                    ac = data['system']['attributes']['ac']['value']
                    hp = data['system']['attributes']['hp']['max']
                    if hp is None:
                        hp = 0

                    str_mod = 0
                    str = (str_mod * 2) + 10
                    dex_mod = 0
                    dex = (dex_mod * 2) + 10
                    con_mod = 0
                    con = (con_mod * 2) + 10
                    itl_mod = 0
                    itl = (itl_mod * 2) + 10
                    wis_mod = 0
                    wis = (wis_mod * 2) + 10
                    cha_mod = 0
                    cha = (cha_mod * 2) + 10

                    try:
                        fort_prof = data['system']['saves']["fortitude"]["value"] - level - con_mod
                    except TypeError:
                        fort_prof = 0

                    try:
                        reflex_prof = data['system']['saves']["reflex"]["value"] - level - dex_mod
                    except TypeError:
                        reflex_prof = 0

                    try:
                        will_prof = data['system']['saves']["will"]["value"] - level - wis_mod
                    except TypeError:
                        will_prof = 0


                    stealth_prof = data["system"]["attributes"]["stealth"]['value'] - level - dex_mod

                    resistance = {
                        "resist": {},
                        "weak": {},
                        "immune": {}
                    }
                    if "hardness" in data['system']['attributes'].keys():
                        resistance['resist']['all_damage'] = data['system']['attributes']['hardness']
                    if "resistances" in data["system"]["attributes"].keys():
                        for item in data['system']['attributes']['resistances']:
                            if "exceptions" in item.keys():
                                item_name = item['type'].lower()
                                exceptions = item['exceptions']
                                value = item['value']

                                resistance['resist'][item_name] = {
                                    "exceptions": exceptions,
                                    'value': value
                                }
                            else:
                                resistance["resist"][item["type"].lower()] = item["value"]

                            if item["type"] not in resistances:
                                resistances.append(item["type"])
                    if "weaknesses" in data["system"]["attributes"].keys():
                        for item in data['system']['attributes']['weaknesses']:
                            if "exceptions" in item.keys():
                                item_name = item['type'].lower()
                                exceptions = item['exceptions']
                                value = item['value']

                                resistance['weak'][item_name] = {
                                    "exceptions": exceptions,
                                    'value': value
                                }
                            else:
                                resistance["weak"][item["type"].lower()] = item["value"]

                            if item["type"] not in resistances:
                                resistances.append(item["type"])
                    if "immunities" in data["system"]["attributes"].keys():
                        for item in data['system']['attributes']['immunities']:
                            if "exceptions" in item.keys():
                                item_name = item['type'].lower()
                                exceptions = item['exceptions']
                                value = 1

                                resistance['immune'][item_name] = {
                                    "exceptions": exceptions,
                                    'value': value
                                }
                            else:
                                resistance["immune"][item["type"].lower()] = "immune"

                            if item["type"] not in resistances:
                                resistances.append(item["type"])
                    try:
                        async with async_session() as session:
                            async with session.begin():
                                new_entry = EPF_NPC(
                                    name=name,
                                    max_hp=int(hp),
                                    type=type,
                                    level=int(level),
                                    ac_base=int(ac),
                                    class_dc=int(level)+10,  # May need to get more granular with this
                                    str=int(str),
                                    dex=int(dex),
                                    con=int(con),
                                    itl=int(itl),
                                    wis=int(wis),
                                    cha=int(cha),
                                    fort_prof=fort_prof,
                                    reflex_prof=reflex_prof,
                                    will_prof=will_prof,
                                    perception_prof=0,
                                    arcane_prof=0,
                                    divine_prof=0,
                                    occult_prof=0,
                                    primal_prof=0,
                                    acrobatics_prof=0,
                                    arcana_prof=0,
                                    athletics_prof=0,
                                    crafting_prof=0,
                                    deception_prof=0,
                                    diplomacy_prof=0,
                                    intimidation_prof=0,
                                    medicine_prof=0,
                                    nature_prof=0,
                                    occultism_prof=0,
                                    performance_prof=0,
                                    religion_prof=0,
                                    society_prof=0,
                                    stealth_prof=stealth_prof,
                                    survival_prof=0,
                                    thievery_prof=0,
                                    resistance=resistance,
                                    attacks={},
                                    spells={}

                                )
                                session.add(new_entry)
                                await session.commit()
                                logging.info(f"{name} written")
                                return 1
                    except IntegrityError as e:

                        if os.environ['Overwrite'] == "True":
                            # print(f"Overwriting {name}")
                            async with async_session() as session:
                                npc_result = await session.execute(select(EPF_NPC).where(EPF_NPC.name == name))
                                npc = npc_result.scalars().one()

                                npc.name = name
                                npc.max_hp = int(hp)
                                npc.type = type
                                npc.level = int(level)
                                npc.ac_base = int(ac)
                                npc.class_dc = int(level)+10  # May need to get more granular with this
                                npc.str = int(str)
                                npc.dex = int(dex)
                                npc.con = int(con)
                                npc.itl = int(itl)
                                npc.wis = int(wis)
                                npc.cha = int(cha)
                                npc.fort_prof = fort_prof
                                npc.reflex_prof = reflex_prof
                                npc.will_prof = will_prof
                                npc.perception_prof = 0
                                npc.arcane_prof = 0
                                npc.divine_prof = 0
                                npc.occult_prof = 0
                                npc.primal_prof = 0
                                npc.acrobatics_prof = 0
                                npc.arcana_prof = 0
                                npc.athletics_prof = 0
                                npc.crafting_prof = 0
                                npc.deception_prof = 0
                                npc.diplomacy_prof = 0
                                npc.intimidation_prof = 0
                                npc.medicine_prof = 0
                                npc.nature_prof = 0
                                npc.occultism_prof = 0
                                npc.performance_prof = 0
                                npc.religion_prof = 0
                                npc.society_prof = 0
                                npc.stealth_prof = stealth_prof
                                npc.survival_prof = 0
                                npc.thievery_prof = 0
                                npc.resistance = resistance
                                npc.attacks = {}
                                npc.spells = {}

                                await session.commit()
                            logging.info(f"{name} overwritten")
                            return 2
                        else:
                            logging.info(f"Excepted {name}")
                            return 3
                except Exception as e:
                    print(data['name'])
                    print(e)
    except PermissionError:
        return None
    except Exception as e:
        # print(data['name'])
        logging.warning(e)
        return 4


async def EPF_import_weapon(file: str, async_session):
    try:
        with open(f"{file}", encoding='utf8') as f:
            # logging.info(f'{file}')
            data = json.load(f)
            if "type" in data.keys() and data['type'] == 'weapon':
                # print(data['name'])
                if data["system"]["potencyRune"]["value"] is None:
                    potency = 0
                else:
                    potency = data["system"]["potencyRune"]["value"]
                runes = ""
                for x in range(1, 6):
                    try:
                        if data["system"][f"propertyRune{x}"] is not None:
                            runes += f"{data['system'][f'propertyRune{x}'],}"
                    except KeyError:
                        pass

                # Write to the database
                try:
                    async with async_session() as session:
                        async with session.begin():
                            new_entry = EPF_Weapon(
                                name=data["name"],
                                level=data["system"]["level"]["value"],
                                base_item=data["system"]["baseItem"],
                                category=data["system"]["category"],
                                damage_type=data["system"]["damage"]["damageType"],
                                damage_dice=data["system"]["damage"]["dice"],
                                damage_die=data["system"]["damage"]["die"],
                                group=data["system"]["group"],
                                range=data["system"]["range"],
                                potency_rune=potency,
                                striking_rune=data["system"]["strikingRune"]["value"],
                                runes=runes,
                                traits=data["system"]["traits"]["value"],
                            )
                            session.add(new_entry)
                            await session.commit()
                            logging.info(f"{data['name']} written")
                            return 1
                except IntegrityError as e:
                    if os.environ['Overwrite'] == "True":
                        async with async_session() as session:
                            item_result = await session.execute(
                                select(EPF_Weapon).where(EPF_Weapon.name == data['name']))
                            item = item_result.scalars().one()

                            item.name = data["name"]
                            item.level = data["system"]["level"]["value"]
                            item.base_item = data["system"]["baseItem"]
                            item.category = data["system"]["category"]
                            item.damage_type = data["system"]["damage"]["damageType"]
                            item.damage_dice = data["system"]["damage"]["dice"]
                            item.damage_die = data["system"]["damage"]["die"]
                            item.group = data["system"]["group"]
                            item.range = data["system"]["range"]
                            item.potency_rune = potency
                            item.striking_rune = data["system"]["strikingRune"]["value"]
                            item.runes = runes
                            item.traits = data["system"]["traits"]["value"]

                            await session.commit()
                        logging.info(f"{data['name']} overwritten")
                        return 2
                    else:
                        logging.info(f"Excepted {data['name']}")
                        return 3
        return None
    except Exception as e:
        logging.warning(e)
        return 4


async def EPF_import_equipment(file: str, async_session):
    try:
        with open(f"{file}", encoding='utf8') as f:
            # logging.info(f'{file}')
            data = json.load(f)
            if "type" in data.keys() and data['type'] == 'equipment':
                if 'rules' in data['system'].keys():
                    if len(data['system']['rules']) > 0 and data['system']['rules'][0]['key'] == "FlatModifier":
                        # print(data['name'])
                        rules = {}
                        try:
                            for item in data['system']['rules']:

                                if item["key"] == "FlatModifier":
                                    if "predicate" not in item.keys():
                                        if type(item['selector']) == list:
                                            for i in item["selector"]:
                                                if "type" not in item.keys():
                                                    item_type = "item"
                                                else:
                                                    item_type = item["type"]
                                                rules[i] = {
                                                    "bonus": item['value'],
                                                    "mode": item_type
                                                }
                                        else:
                                            if "type" not in item.keys():
                                                item_type = "item"
                                            else:
                                                item_type = item["type"]
                                            rules[item['selector']] = {
                                                "bonus": item['value'],
                                                "mode": item_type
                                            }

                                elif item["key"] == "ActiveEffectLike":
                                    path: str = item["path"]
                                    new_path = path.split(".")
                                    # print(new_path)
                                    rules[new_path[2]] = {
                                        "bonus": item["value"],
                                        "mode": item["mode"]
                                    }

                        except Exception as e:
                            logging.warning(f"{data['name']}, {e}")
                            return 4

                        # Write to the database
                        try:
                            async with async_session() as session:
                                async with session.begin():
                                    new_entry = EPF_Equipment(
                                        name=data["name"],
                                        level=data["system"]["level"]["value"],
                                        data=rules
                                    )
                                    session.add(new_entry)
                                    await session.commit()
                                    logging.info(f"{data['name']} written")
                                    return 1
                        except IntegrityError as e:
                            if os.environ['Overwrite'] == "True":
                                async with async_session() as session:
                                    item_result = await session.execute(
                                        select(EPF_Equipment).where(EPF_Equipment.name == data['name']))
                                    item = item_result.scalars().one()

                                    item.name = data["name"]
                                    item.level = data["system"]["level"]["value"]
                                    item.data = rules

                                    await session.commit()
                                logging.info(f"{data['name']} overwritten")
                                return 2
                            else:
                                logging.info(f"Excepted {data['name']}")
                                return 3
        return None
    except Exception as e:
        logging.warning(e)
        return 4


async def EPF_import_spells(file: str, async_session):
    try:
        with open(f"{file}", encoding='utf8') as f:
            # logging.info(f'{file}')
            data = json.load(f)
            if "type" in data.keys() and data['type'] == 'spell':
                # print(data['name'])
                if data["system"]["spellType"]["value"] == "attack" or data["system"]["spellType"]["value"] == "save":
                    # print(data['system']['spellType']["value"])
                    if len(data["system"]["damage"]["value"].keys()) == 0:
                        return 3
                    else:
                        damage = {}
                        try:
                            for key in data["system"]["damage"]["value"].keys():
                                damage[key] = {
                                    "mod": data["system"]["damage"]["value"][key]["applyMod"],
                                    "value": data["system"]["damage"]["value"][key]["value"],
                                    "dmg_type": data["system"]["damage"]["value"][key]["type"]["value"]
                                }
                        except Exception:
                            try:
                                damage["value"] = {
                                    "mod": data["system"]["damage"]["value"]["applyMod"],
                                    "value": data["system"]["damage"]["value"]["value"],
                                    "dmg_type": data["system"]["damage"]["value"]["type"]["value"]
                                }
                            except Exception:
                                for key in data['system']['damage']['value'].keys():
                                    damage[key] = {
                                        "mod": False,
                                        "value": data["system"]["damage"]["value"][key]["value"],
                                        "dmg_type": data["system"]["damage"]["value"][key]["type"]["value"]
                                    }
                        if "heightening" in data["system"].keys():
                            try:
                                if data["system"]["heightening"]["type"] == "fixed":
                                    heightening = {
                                        "type": data["system"]["heightening"]["type"],
                                        "interval": data["system"]["heightening"]["levels"],
                                    }
                                else:
                                    heightening = {
                                        "type": data["system"]["heightening"]["type"],
                                        "interval": data["system"]["heightening"]["interval"],
                                        "damage": data["system"]["heightening"]["damage"]
                                    }
                            except KeyError:
                                heightening = {
                                    "type": "",
                                    "interval": 0,
                                    "damage": ""
                                }
                        else:
                            heightening = {
                                "type": "",
                                "interval": 0,
                                "damage": ""
                            }

                        try:
                            async with async_session() as session:
                                async with session.begin():
                                    new_entry = EPF_Spells(
                                        name=data["name"],
                                        level=data["system"]["level"]["value"],
                                        type=data["system"]["spellType"]["value"],
                                        save=data["system"]["save"],
                                        traditions=data["system"]["traditions"]["value"],
                                        school="",
                                        damage=damage,
                                        heightening=heightening

                                    )
                                    session.add(new_entry)
                                    await session.commit()
                                    logging.info(f"{data['name']} written")
                                    # print("written")
                                    return 1
                        except IntegrityError as e:
                            if os.environ['Overwrite'] == "True":
                                # print("Overwrite")
                                async with async_session() as session:
                                    item_result = await session.execute(
                                        select(EPF_Spells).where(EPF_Spells.name == data['name']))
                                    item = item_result.scalars().one()

                                    item.name = data["name"]
                                    item.level = data["system"]["level"]["value"]
                                    item.type = data["system"]["spellType"]["value"]
                                    item.save = data["system"]["save"]
                                    item.traditions = data["system"]["traditions"]["value"]
                                    item.school = ""
                                    item.damage = damage
                                    item.heightening = heightening

                                    await session.commit()

                                logging.info(f"{data['name']} overwritten")
                                # print("overwritten")
                                return 2
                            else:
                                logging.info(f"Excepted {data['name']}")
                                # print(data["name"])
                                # print("excepted")
                                return 3
        # print(data['name'])
        excepted_spells.append(data["name"])
        return None
    except PermissionError:
        return None
    except AttributeError:
        return None
    except Exception as e:
        logging.warning(e)
        # print("errored")
        return 4
