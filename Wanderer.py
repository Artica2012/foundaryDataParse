import logging

# imports
import aiohttp
import os

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database_models import PF2_Lookup, Base
from database_operations import USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE
from sqlalchemy.ext.asyncio import AsyncSession, async_session
from sqlalchemy.orm import sessionmaker



from dotenv import load_dotenv

from database_operations import get_asyncio_db_engine

engine = get_asyncio_db_engine(user=USERNAME, password=PASSWORD, host=HOSTNAME, port=PORT, db=DATABASE)
Session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

load_dotenv(verbose=True)

CLIENT_ID = os.getenv('CLIENT_ID')
API_KEY = os.getenv('API_KEY')

async def wander():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Wander = Wanderer(CLIENT_ID, API_KEY)
    for key in endpoints.keys():
        try:
            # logging.error(key)
            await Wander.wander(endpoints[key], query=None)
        except Exception:
            logging.error(f"ERROR: {key}")





GET_URL = "https://wanderersguide.app/api/"
endpoints = {
    "feat" : "feat",
    "item" : "item",
    "spell" : "spell",
    "class" : "class",
    "archetype" : "archetype",
    "ancestry" : "ancestry",
    "heritage": "heritage",
    "versatile heritage": "v-heritage",
    "background": "background",
    "condition": "condition",
    "trait": "trait"
}

class Wanderer:
    def __init__(self, client_id, api_key):
        self.client_id = client_id
        self.api_key = api_key
        self.category = None

    # async def o_auth(self, char_id):
    #     o_auth_url = f"wanderersguide.app/api/oauth2/authorize/{char_id}?response_type=code&client_id={self.client_id}"

    async def lookup(self, category, query=None, id=None, ):
        self.category = category
        # print(category, query, id)

        if id is None and query is not None:
            search_string = f"?name={query}"
        elif query is None and id is not None:
            search_string = f"?id={id}"
        else:
            search_string = "/all"

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": self.api_key
            }
            async with session.get(f"{GET_URL}{category}{search_string}", headers=headers, ssl=False) as response:
                # print(response.status)
                # print(response)
                if response.status == 200:
                    data:dict = await response.json()
                    return data
                    # print(data)
                else:
                    return None


    async def decode_json(self, data:dict):
        # print(data)
        output = {}
        try:
            for key in data.keys():
                # print(key)
                # print(data[key])

                try:
                    match self.category:
                        case "feat":
                            output =self.decode_feat(data[key])
                        case "item":
                            output = self.decode_item(data[key])
                        case "spell":
                            output = self.decode_spell(data[key])
                        case "class":
                            output = self.decode_class(data[key])
                        case "ancestry":
                            output = self.decode_ancestry(data[key])
                    # print(output)
                    await self.write(output)


                except TypeError:
                    print("\n")
        except AttributeError:
            for x in data:
                # print(x)
                match self.category:
                    case "archetype":
                        output = self.decode_archetype(x)
                    case "heritage":
                        output = self.decode_heritage(x)
                    case "v-heritage":
                        output = self.decode_heritage(x)
                    case "background":
                        output = self.decode_background(x)
                    case "condition":
                        output = self.decode_condition(x)
                    case "trait":
                        output = self.decode_trait(x)

                # print(output)
                await self.write(output)


    async def wander(self, category, query=None, id=None):
        output = await self.lookup(category, query, id)
        await self.decode_json(output)

    def decode_spell(self, d:dict):
        # print(d)
        tags = []
        i = d['Spell']
        description = i['description']
        name = i['name']
        trad = i['traditions']
        duration = i['duration']

        for item in d['Tags']:
            tags.append(item['name'])
        output = {
            "type": "spell",
            "name": name,
            "description": description,
            "trad": trad,
            'duration': duration,
            "tags": tags
        }
        return output

    def decode_feat(self, d:dict):
        tags = []
        for item in d['Tags']:
            tags.append(item['name'])

        i = d['Feat']
        description = i['description']
        name = i['name']

        output = {
            "type": "feat",
            "name": name,
            "description": description,
            "tags": tags
        }
        return output

    def decode_item(self, d:dict):
        tags = []
        for item in d['TagArray']:
            tags.append(item['name'])

        i = d['Item']
        description = i['description']
        name = i['name']
        item_type = i['itemType']
        price = i['price']
        level = i['level']

        output = {
            "type": "item",
            "name": name,
            "description": description,
            "tags": tags,
            "itemType": item_type,
            "price": price,
            "level": level
        }
        return output

    def decode_class(self, d:dict):

        i = d['Class']
        description = i['description']
        name = i['name']

        output = {
            "type": "class",
            "name": name,
            "description": description,

        }
        return output

    def decode_archetype(self, d:dict):
        name = d['name']
        description = d['description']

        output = {
            'type': 'archetype',
            'name': name,
            'description': description
        }
        return output

    def decode_ancestry(self, d:dict):
        i = d['Ancestry']
        description = i['description']
        name = i['name']
        hp = i['hitPoints']
        size = i['size'].title()
        speed = i['speed']

        output = {
            "type": "ancestry",
            "name": name,
            "description": description,
            'hp': hp,
            'size': size,
            'speed': speed

        }
        return output

    def decode_heritage(self, d:dict):
        name = d['name']
        description = d['description']

        output = {
            'type': 'heritage',
            'name': name,
            'description': description
        }
        return output

    def decode_background(self, d:dict):
        name = d['name']
        description = d['description']
        boosts = f"{d['boostOne']} {d['boostTwo']}"

        output = {
            'type': 'background',
            'name': name,
            'description': description,
            'boosts': boosts

        }
        return output

    def decode_condition(self, d:dict):
        name = d['name']
        description = d['description']

        output = {
            'type': 'condition',
            'name': name,
            'description': description
        }
        return output

    def decode_trait(self, d:dict):
        name = d['name']
        description = d['description']

        output = {
            'type': 'trait',
            'name': name,
            'description': description
        }
        return output

    async def write(self, output):
        try:
            async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            async with async_session() as session:
                async with session.begin():
                    new_entry = PF2_Lookup(
                        name=output["name"],
                        endpoint = output['type'],
                        data = output
                    )
                    session.add(new_entry)
                    await session.commit()
                    # print(output['name'])
        except IntegrityError as e:
            try:
                if os.environ['Overwrite'] == "True":
                    # print("Overwrite")
                    async with async_session() as session:
                        item_result = await session.execute(
                            select(PF2_Lookup).where(PF2_Lookup.name == output['name']))
                        item = item_result.scalars().one()

                        item.name = output['name']
                        item.endpoint = output['type']
                        item.data = output

                        await session.commit()
                        # print(output['name'])
            except Exception as e:
                logging.error(e)
