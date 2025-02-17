from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Union, Literal

from pydantic import BaseModel, Field, constr

s3_file_url_regex = r'^https:\/\/minio\.campusderkuenste\.ch\/ixdm-mitwelten\/viz_app\/.+$'

class Tag(BaseModel):
    '''
    Annotation
    '''
    id: Optional[int] = None
    name: Optional[constr(regex=r'\w+')] = None


class File(BaseModel):
    '''
    File uploaded through front end to S3, associated to an entry
    '''
    id: Optional[int] = None
    type: str = Field(title='MIME type', example='application/pdf')
    name: str = Field(title='File name')
    link: constr(strip_whitespace=True, regex=s3_file_url_regex) = Field(
        title='Link to S3 object',
        description='Constrained to mitwelten bucket at https://mitwelten-frontend.s3.amazonaws.com'
    )


class Type(Enum):
    '''
    Node type enumeration as defined in the database
    '''
    env = 'env'
    cam = 'cam'
    pax = 'pax'
    audiomoth = 'audiomoth'
    appliance = 'appliance'
    air = 'air'
    audio = 'Audio'
    accesspoint = 'Access Point'
    humitemp = 'HumiTemp'
    humitempmoisture = 'HumiTempMoisture'
    moisture = 'Moisture'
    optical = 'Optical'
    photo = 'Photo'


class Comment(BaseModel):
    '''
    User-created comment in form of a __marker__ or __range label__
    '''
    id: Optional[int] = None
    comment: str = Field(..., example='We have observed this as well.')
    timeStart: datetime = Field(
        ...,
        example='2022-03-06T12:23:42.777Z',
        description='Point in time the comment is referring to. If `timeEnd` is given, `timeStart` indicates the beginning of a range.'
    )
    timeEnd: Optional[datetime] = Field(None, example='2022-03-06T12:42:23.777Z', description='End of the time range the comment is referring to')
    author: Optional[str] = None


class Point(BaseModel):
    '''
    Coordinate in WGS84 format
    '''
    lat: float = Field(..., example=47.53484943172696, title="Latitude (WGS84)")
    lon: float = Field(..., example=7.612519197679952, title="Longitude (WGS84)")


class EnvDatum(BaseModel):
    '''
    Datum of a measurement by an environmental sensor
    '''
    type: Literal['env', 'HumiTemp', 'HumiTempMoisture', 'Moisture']
    time: Optional[datetime] = None
    nodeLabel: Optional[constr(regex=r'\d{4}-\d{4}')] = None
    voltage: Optional[float] = Field(None, example=4.8)
    voltageUnit: Optional[str] = Field(None, example='V')
    temperature: Optional[float] = Field(None, example=7.82)
    temperatureUnit: Optional[str] = Field('°C', example='°C')
    humidity: Optional[float] = Field(None, example=93.78)
    humidityUnit: Optional[str] = Field('%', example='%')
    moisture: Optional[float] = Field(None, example=2.6)
    moistureUnit: Optional[str] = Field('g/m³', example='g/m³')


class PaxDatum(BaseModel):
    '''
    Datum of a measurement by a PAX sensor
    '''
    type: Literal['pax', 'Pax']
    time: Optional[datetime] = None
    nodeLabel: Optional[constr(regex=r'\d{4}-\d{4}')] = None
    voltage: Optional[float] = Field(None, example=4.8)
    voltageUnit: Optional[str] = Field('V', example='V')
    pax: Optional[int] = Field(None, example=17)
    paxUnit: Optional[str] = Field(None, example='')


class DatumResponse(BaseModel):
    '''
    Response containing one of a selection of sensor data types
    '''
    __root__: Union[List[PaxDatum], List[EnvDatum]] = Field(..., discriminator='type')


class ApiResponse(BaseModel):
    code: Optional[int] = None
    type: Optional[str] = None
    message: Optional[str] = None


class ApiErrorResponse(BaseModel):
    detail: Optional[str] = None


class EntryIdFilePostRequest(BaseModel):
    additionalMetadata: Optional[str] = Field(
        None, description='Additional data to pass to server'
    )
    file: Optional[bytes] = Field(None, description='File to upload')


class Entry(BaseModel):
    '''
    A user generated "pin" on the map to which `files`, `tags` and `comments` can be associated
    '''
    id: Optional[int] = None
    date: Optional[datetime] = Field(None, example='2022-12-31T23:59:59.999Z', description='Date of creation')
    name: str = Field(
        ..., example='Interesting Observation', description='Title of this entry'
    )
    description: Optional[str] = Field(
        None,
        example='I discovered an correlation between air humidity level and visitor count',
        description='Details for this entry'
    )
    location: Point
    type: Optional[str] = Field(None, example='A walk in the park')
    tags: Optional[List[Tag]] = None
    comments: Optional[List[Comment]] = None
    files: Optional[List[File]] = None

class PatchEntry(Entry):
    '''
    This is a copy of `Entry` with all fields optional
    for patching existing records.
    '''
    name: Optional[str] = Field(
        None, example='Interesting Observation', description='Title of this entry'
    )
    location: Optional[Point]

class Location(BaseModel):
    '''
    A location record, describing metadata of a coordinate
    '''
    id: Optional[int] = None
    location: Point
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Datum(BaseModel):
    __root__: Union[EnvDatum, PaxDatum]


class Node(BaseModel):
    '''
    A device deployed in the field, collecting and/or processing data
    '''
    id: Optional[int] = None
    name: constr(regex=r'\d{4}-\d{4}') = Field(
        ...,
        example='2323-4242',
        description='Identifyer, a.k.a _Node ID_, _Node Label_, or _Label_'
    )
    location: Point
    location_description: Optional[str] = None
    type: Type = Field(..., example='Audio', description='Desription of function')
    platform: Optional[str] = Field(None, example='Audiomoth', description='Hardware platform')
    description: Optional[str] = Field(
        None,
        example='Environmental sensor to record humidity, temperature and athmospheric pressure',
    )
