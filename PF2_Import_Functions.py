import json
import logging
import os

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database_models import NPC



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
        return None
    except Exception:
        # logging.warning(e)
        return 4