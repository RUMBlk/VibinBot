import os
from dotenv import load_dotenv, find_dotenv
from peewee import *

load_dotenv(find_dotenv())

db = PostgresqlDatabase(os.environ['DB_NAME'], user=os.environ['DB_USER'], password=os.environ['DB_PASS'], host=os.environ['DB_HOST'], port=os.environ['DB_PORT'])

class BaseModel(Model):
    class Meta:
        database = db

class guilds(BaseModel):
    id = PrimaryKeyField()
    GuildID = BigIntegerField()

class members(BaseModel):
    id = PrimaryKeyField()
    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    UserID = BigIntegerField()
    msg_count = IntegerField()
    points = IntegerField()

class roles(BaseModel):
    id = PrimaryKeyField()
    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    UserID = ForeignKeyField(members, db_column = 'UserID')
    RoleID = BigIntegerField()
    Group = CharField()
    Expires = DateTimeField(null = True)

class candidates(BaseModel):
    id = PrimaryKeyField()
    GuildID =  ForeignKeyField(guilds, db_column = 'GuildID')
    UserID =  ForeignKeyField(members, db_column = 'UserID')

#class votes(BaseModel):
#    id = PrimaryKeyField()
#    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
#    UserID = ForeignKeyField(members, db_column = 'UserID')
#    Supports = ForeignKeyField(candidates, db_column = 'UserID')

db.connect()
db.create_tables([guilds, members, roles, candidates])

