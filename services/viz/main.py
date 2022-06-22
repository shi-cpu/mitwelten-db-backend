# generated by fastapi-codegen:
#   filename:  viz-schema.yml
#   timestamp: 2022-06-21T16:49:25+00:00

import sys
from typing import List
from datetime import datetime

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import conint, constr

import databases
from sqlalchemy.sql import select, insert, func, between # , and_, desc, all_
from asyncpg.exceptions import UniqueViolationError, StringDataRightTruncationError

from models import ApiResponse, DataNodeLabelGetResponse, Entry, PatchEntry, Node, Tag, ApiErrorResponse
from tables import entry, location, tag

sys.path.append('../../')
import credentials as crd

#
# Set up database
#

DATABASE_URL = f'postgresql://{crd.db.user}:{crd.db.password}@{crd.db.host}/{crd.db.database}'

origins = [
    'https://viz.mitwelten.org',
    'http://localhost',
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
        'name': 'datum',
        'description': 'Sensor / Capture Data',
    },
    {
        'name': 'file',
        'description': 'Files uploaded for / added to entries',
    },
]

app = FastAPI(
    title='Mitwelten Dashboard',
    description='This service provides REST endpoints to exchange data from [Mitwelten](https://mitwelten.org) for the purpose of visualisation and map plotting.',
    contact={'email': 'mitwelten.technik@fhnw.ch'},
    version='1.0.0',
    servers=[
        {'url': 'https://data.mitwelten.org', 'description': 'Production environment'},
        {'url': 'http://localhost:8000', 'description': 'Development environment'}
    ],
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


@app.get('/data/{node_label}', response_model=DataNodeLabelGetResponse, tags=['datum'])
def list_data(
    node_label: constr(regex=r'\d{4}-\d{4}'),
    time_from: Optional[datetime] = Query(None, alias='from', example='2022-06-22T18:00:00.000Z'),
    time_to: Optional[datetime] = Query(None, alias='to', example='2022-06-22T20:00:00.000Z'),
    limit: Optional[conint(ge=1, le=65536)] = 32768,
) -> DataNodeLabelGetResponse:
    '''
    List sensor / capture data in timestamp ascending order

    **Not Implemented**
    '''
    pass

@app.get('/entries', response_model=List[Entry], tags=['entry'])
async def list_entries(
    time_from: Optional[datetime] = Query(None, alias='from', example='2022-06-22T18:00:00.000Z'),
    time_to: Optional[datetime] = Query(None, alias='to', example='2022-06-22T20:00:00.000Z'),
) -> List[Entry]:
    '''
    ## List all entries

    The entry selection can optionally be delimited by supplying either bounded
    or unbounded ranges as a combination of `to` and `from` query parameters.

    ### Locations

    `locations` reside in a dedicated table, and are joined. The foreign key
    is omitted in the response.
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
    ## Add a new entry to the map

    ### Locations

    `locations` reside in a dedicated table, new `entry` records are created
    trying to find a `location` that is within a radius of ~1m. If such a
    record is found, the closest one is referenced in the new `entry` record.
    If no location is found, a new one is created, with `type` = 'user-created',
    and referenced in the new `entry` record.

    ### Timestamps

    The internal attribute `created_at` is used as `date` defined by the model.
    It is automatically set on creation of the record and can't be written to
    by the user.
    '''

    transaction = await database.transaction()

    try:
        point = f'point({float(body.location.lat)}, {float(body.location.lon)})'
        thresh_1m = 0.0000115
        # thresh_1m = 0.02
        location_query = f'''
        select location_id from {crd.db.schema}.locations
        where location <-> {point} < {thresh_1m}
        order by location <-> {point}
        limit 1
        '''
        result = await database.fetch_one(query=location_query)

        location_id = None
        if result == None:
            loc_insert_query = f'''
            insert into {crd.db.schema}.locations(location, type)
            values (point({body.location.lat},{body.location.lon}), 'user-added')
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

@app.get('/entry/{id}', response_model=Entry, tags=['entry'], responses={404: {"model": ApiErrorResponse}})
async def get_entry_by_id(id: int) -> Entry:
    '''
    Find entry by ID
    '''
    query = select(entry, entry.c.entry_id.label('id'), entry.c.created_at.label('date'), location.c.location).\
        select_from(entry.outerjoin(location)).where(entry.c.entry_id == id)
    result = await database.fetch_one(query=query)

    if result == None:
        return JSONResponse(status_code=404, content={'message':  'Entry not found'})
    else:
        return result

@app.patch('/entry/{id}', response_model=None, tags=['entry'])
async def update_entry(id: int, body: PatchEntry = ...) -> None:
    '''
    ## Updates an entry

    Patching not implemented for `tags`

    ### Locations

    The record is updated with the closest `location` in a radius of ~1m. If
    no `location` is found, a new one is created and referenced.
    '''
    update_data = body.dict(exclude_unset=True)

    transaction = await database.transaction()

    try:
        location_id = None
        if 'location' in update_data:
            point = f'point({float(body.location.lat)}, {float(body.location.lon)})'
            thresh_1m = 0.0000115
            location_query = f'''
            select location_id from {crd.db.schema}.locations
            where location <-> {point} < {thresh_1m}
            order by location <-> {point}
            limit 1
            '''
            result = await database.fetch_one(query=location_query)

            if result == None:
                loc_insert_query = f'''
                insert into {crd.db.schema}.locations(location, type)
                values (point({body.location.lat},{body.location.lon}), 'user-added')
                returning location_id
                '''
                print(loc_insert_query)
                location_id = await database.execute(loc_insert_query)
            else:
                location_id = result.location_id
            update_data['location_id'] = location_id
            del update_data['location']

        query = entry.update().where(entry.c.entry_id == id).\
            values({**update_data, entry.c.updated_at: func.current_timestamp()})

        result = await database.execute(query)

    except Exception as e:
        print(e)
        await transaction.rollback()
    else:
        await transaction.commit()
        return result


@app.delete('/entry/{id}', response_model=None, tags=['entry'])
async def delete_entry(id: int) -> None:
    '''
    ## Deletes an entry

    __potential for optimisation__: remove related records when record to be
    deleted is the last referring one.
    '''
    return await database.execute(entry.delete().where(entry.c.entry_id == id))


@app.post('/entry/{id}/tag', response_model=Entry, tags=['entry', 'tag'])
def add_tag_to_entry(id: int, body: Tag = None) -> Entry:
    '''
    Adds a tag for an entry

    **Not Implemented**
    '''
    pass


@app.post('/entry/{id}/file', response_model=ApiResponse, tags=['entry', 'file'])
def upload_file(id: int) -> ApiResponse:
    '''
    Uploads a file

    **Not Implemented**
    '''
    pass


@app.get('/nodes', response_model=List[Node], tags=['node'])
async def list_nodes(
    time_from: Optional[datetime] = Query(None, alias='from', example='2022-06-22T18:00:00.000Z'),
    time_to: Optional[datetime] = Query(None, alias='to', example='2022-06-22T20:00:00.000Z'),
) -> List[Node]:
    '''
    List all nodes

    This is a temporary, hacky, but working implementation. It becomes obvious
    that the database schema requires an abstraction of `deployment`.
    '''

    select_part = f'''
    select nl.node_id, node_label, n.type as node_type, n.description as node_description,
    nl.location_id, location, name as location_name, l.description as location_description, l.type as location_type
    from node_locations nl
    left join {crd.db.schema}.nodes n on n.node_id = nl.node_id
    left join {crd.db.schema}.locations l on l.location_id = nl.location_id
    '''
    query = ''
    values = {}

    if time_from and time_to:
        query = f'''
        with node_locations as (
            select distinct node_id, location_id from {crd.db.schema}.files_image
            where location_id is not null and time between :time_from and :time_to
            union
            select distinct node_id, location_id from {crd.db.schema}.files_audio
            where location_id is not null and (time + (duration || ' seconds')::interval) > :time_from and time < :time_to
        )'''
        values = { 'time_from': time_from, 'time_to': time_to }
    elif time_from:
        query = f'''
        with node_locations as (
            select distinct node_id, location_id from {crd.db.schema}.files_image
            where location_id is not null and time >= :time_from
            union
            select distinct node_id, location_id from {crd.db.schema}.files_audio
            where location_id is not null and (time + (duration || ' seconds')::interval) > :time_from
        )'''
        values = { 'time_from': time_from }
    elif time_to:
        query = f'''
        with node_locations as (
            select distinct node_id, location_id from {crd.db.schema}.files_image
            where location_id is not null and time < :time_to
            union
            select distinct node_id, location_id from {crd.db.schema}.files_audio
            where location_id is not null and (time + (duration || ' seconds')::interval) <= :time_to
        )'''
        values = { 'time_to': time_to }

    query += select_part
    result = await database.fetch_all(query=query, values=values)
    transform = []
    for record in result:
        transform.append({
            'id': record.node_id,
            'name': record.node_label,
            'description': record.node_description,
            'type': record.node_type,
            'location': {
                'id': record.location_id,
                'location': {
                    'lat': record.location[0],
                    'lon': record.location[1]
                },
                'type': record.location_type,
                'name': record.location_name,
                'description': record.location_description
            }
        })
    return transform


@app.put('/tag', response_model=None, tags=['tag'], responses={
        400: {"model": ApiErrorResponse},
        404: {"model": ApiErrorResponse},
        409: {"model": ApiErrorResponse}})
async def put_tag(body: Tag) -> None:
    '''
    Add a new tag or update an existing one
    '''

    try:
        if body.name:
            tagname = body.name.strip()
            if len(tagname) == 0:
                return JSONResponse(status_code=400, content={'message': 'Name is too short'})

            if body.id:
                check = await database.execute(tag.select().where(tag.c.tag_id == body.id))
                if check == None:
                    return JSONResponse(status_code=404, content={'message':  'Tag not found'})
                query = tag.update().where(tag.c.tag_id == body.id).\
                    values({tag.c.name: tagname, tag.c.updated_at: func.current_timestamp()})
                await database.execute(query=query)
                return body
            else:
                query = tag.insert().values(
                    name=tagname,
                    created_at=func.current_timestamp(),
                    updated_at=func.current_timestamp()
                ).returning(tag.c.tag_id, tag.c.name)
                result = await database.fetch_one(query=query)
                return { 'id': result.tag_id, 'name': result.name }
    except UniqueViolationError:
        return JSONResponse(status_code=409, content={'message':  'Tag with same name already exists'})
    except StringDataRightTruncationError as e:
        return JSONResponse(status_code=400, content={'message':  str(e)})


@app.get('/tag/{id}', response_model=Tag, tags=['tag'], responses={404: {"model": ApiErrorResponse}})
async def get_tag_by_id(id: int) -> Tag:
    '''
    Find tag by ID
    '''
    result = await database.fetch_one(tag.select().where(tag.c.tag_id == id))
    if result == None:
        return JSONResponse(status_code=404, content={'message':  'Tag not found'})
    else:
        return { 'id': result.tag_id, 'name': result.name }


@app.delete('/tag/{id}', response_model=None, tags=['tag'])
async def delete_tag(id: int) -> None:
    '''
    Deletes a tag
    '''
    return await database.execute(tag.delete().where(tag.c.tag_id == id))


@app.get('/tags', response_model=List[Tag], tags=['tag'])
async def list_tags(
    time_from: Optional[datetime] = Query(None, alias='from', example='2022-06-22T18:00:00.000Z'),
    time_to: Optional[datetime] = Query(None, alias='to', example='2022-06-22T20:00:00.000Z'),
) -> List[Tag]:
    '''
    List all tags
    '''

    query = select(tag.c.tag_id.label('id'), tag.c.name)

    if time_from and time_to:
        query = query.where(between(tag.c.created_at, time_from, time_to))
    elif time_from:
        query = query.where(tag.c.created_at >= time_from)
    elif time_to:
        query = query.where(tag.c.created_at < time_to)

    return await database.fetch_all(query)
