# generated by fastapi-codegen:
#   filename:  viz-schema.yml
#   timestamp: 2022-06-21T16:49:25+00:00

import sys
from typing import List
from datetime import datetime

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import conint, constr

import databases
from sqlalchemy.sql import select, insert, func, between # , and_, desc, all_


from models import ApiResponse, DataNodeLabelGetResponse, Entry, Node, Tag
from tables import entry, location

sys.path.append('../../')
import credentials as crd

#
# Set up database
#

DATABASE_URL = f'postgresql://{crd.db.user}:{crd.db.password}@{crd.db.host}/{crd.db.database}'

origins = [
    'http://localhost:4200',
    'http://localhost:8080',
]

database = databases.Database(DATABASE_URL)

#
# Set up FastAPI
#

tags_metadata = [
    {
        'name': 'entry',
        'description': 'Pins, added to the map',
    },
    {
        'name': 'node',
        'description': 'Deployed devices',
    },
    {
        'name': 'tag',
        'description': 'Tags',
    },
    {
        'name': 'data',
        'description': 'Sensor / Capture Data',
    },
]

app = FastAPI(
    title='Mitwelten Dashboard',
    description='This service provides REST endpoints to exchange data from [Mitwelten](https://mitwelten.org) for the purpose of visualisation and map plotting.',
    contact={'email': 'mitwelten.technik@fhnw.ch'},
    version='1.0.0',
    servers=[{'url': 'https://data.mitwelten.org/v1'}],
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
async def startup():
    await database.connect()

@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()


@app.get('/data/{node_label}', response_model=DataNodeLabelGetResponse, tags=['data'])
def list_data(
    node_label: constr(regex=r'\d{4}-\d{4}'),
    time_from: Optional[datetime] = Query(None, alias='timeFrom'),
    time_to: Optional[datetime] = Query(None, alias='timeTo'),
    limit: Optional[conint(ge=1, le=65536)] = 32768,
) -> DataNodeLabelGetResponse:
    '''
    List sensor / capture data in timestamp ascending order

    **Not Implemented**
    '''
    pass

@app.get('/entries', response_model=List[Entry], tags=['entry'])
async def list_entries(
    time_from: Optional[datetime] = Query(None, alias='from'),
    time_to: Optional[datetime] = Query(None, alias='to'),
) -> List[Entry]:
    '''
    List all entries
    '''

    query = select(entry, entry.c.entry_id.label('id'), entry.c.created_at.label('date'), location.c.location).\
        select_from(entry.outerjoin(location))

    if time_from and time_to:
        print('time_from and time_to', between(entry.c.created_at, time_from, time_to))
        query = query.where(between(entry.c.created_at, time_from, time_to))
    elif time_from:
        query = query.where(entry.c.created_at >= time_from)
    elif time_to:
        query = query.where(entry.c.created_at < time_to)

    return await database.fetch_all(query=query)


@app.post('/entry', response_model=Entry, tags=['entry'])
async def add_entry(body: Entry) -> None:
    '''
    Add a new entry to the map
    '''

    transaction = await database.transaction()

    try:
        point = f'point({float(body.location.lat)}, {float(body.location.lon)})'
        thresh_1m = 0.0000115
        # thresh_1m = 0.02
        location_query = f'''
        select location_id from dev.locations
        where location <-> {point} < {thresh_1m}
        order by location <-> {point}
        limit 1
        '''
        result = await database.fetch_one(query=location_query)

        location_id = None
        if result == None:
            loc_insert_query = f'''
            insert into {crd.db.schema}.locations(location, type)
            values (point({body.location.lat},{body.location.lon}), 'user added')
            returning location_id
            '''
            print(loc_insert_query)
            location_id = await database.execute(loc_insert_query)
        else:
            location_id = result.location_id

        query = entry.insert().values(
            name=body.name,
            description=body.description,
            type=body.type,
            location_id=location_id,
            created_at=func.now(),
            updated_at=func.now()
        ).returning(entry.c.entry_id, entry.c.created_at)
        result = await database.fetch_one(query)

    except:
        await transaction.rollback()
    else:
        await transaction.commit()
        return  { **body.dict(), 'id': result.entry_id, 'date': result.created_at }

@app.get('/entry/{id}', response_model=Entry, tags=['entry'])
def get_entry_by_id(id: int) -> Entry:
    '''
    Find entry by ID

    **Not Implemented**
    '''
    pass


@app.patch('/entry/{id}', response_model=None, tags=['entry'])
def update_entry(id: int, body: Entry = ...) -> None:
    '''
    Updates an entry

    **Not Implemented**
    '''
    pass


@app.delete('/entry/{id}', response_model=None, tags=['entry'])
def delete_entry(id: int) -> None:
    '''
    Deletes an entry

    **Not Implemented**
    '''
    pass


@app.post('/entry/{id}/addTag', response_model=Entry, tags=['entry'])
def add_tag_to_entry(id: int, body: Tag = None) -> Entry:
    '''
    Adds a tag for an entry

    **Not Implemented**
    '''
    pass


@app.post('/entry/{id}/uploadFile', response_model=ApiResponse, tags=['entry'])
def upload_file(id: int) -> ApiResponse:
    '''
    Uploads a file

    **Not Implemented**
    '''
    pass


@app.get('/nodes', response_model=List[Node], tags=['node'])
def list_nodes(
    time_from: Optional[datetime] = Query(None, alias='timeFrom'),
    time_to: Optional[datetime] = Query(None, alias='timeTo'),
) -> List[Node]:
    '''
    List all nodes

    **Not Implemented**
    '''
    pass


@app.put('/tag', response_model=None, tags=['tag'])
def put_tag(body: Tag) -> None:
    '''
    Add a new tag or update an existing one

    **Not Implemented**
    '''
    pass


@app.get('/tag/{id}', response_model=Tag, tags=['tag'])
def get_tag_by_id(id: int) -> Tag:
    '''
    Find tag by ID

    **Not Implemented**
    '''
    pass


@app.delete('/tag/{id}', response_model=None, tags=['tag'])
def delete_tag(id: int) -> None:
    '''
    Deletes a tag

    **Not Implemented**
    '''
    pass


@app.get('/tags', response_model=List[Tag], tags=['tag'])
def list_tags(
    time_from: Optional[datetime] = Query(None, alias='timeFrom'),
    time_to: Optional[datetime] = Query(None, alias='timeTo'),
) -> List[Tag]:
    '''
    List all tags

    **Not Implemented**
    '''
    pass
