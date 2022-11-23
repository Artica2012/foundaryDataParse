#founary_importer.py

# Impoart foundary PF2e data into a PostgreSQL database

import asyncio
import json
import os
import aiohttp


file_list = os.listdir("Data")
for file in file_list:
    with open(f"Data\\{file}") as f:
        data = json.load(f)
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
        print(f"name {name}, ac {ac}, hp {hp}, init_string {init_string}, fort {fort}, reflex {reflex}, will {will}")