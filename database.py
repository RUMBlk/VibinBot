import os
from dotenv import load_dotenv, find_dotenv
from peewee import *

load_dotenv(find_dotenv())

db = None

if os.getenv('DEBUG') is None: db = PostgresqlDatabase(os.environ['DB_NAME'], user=os.environ['DB_USER'], password=os.environ['DB_PASS'], host=os.environ['DB_HOST'], port=os.environ['DB_PORT'])
else: db = SqliteDatabase('tmp/debug.db')

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

class role_tags(BaseModel):
    id = PrimaryKeyField()
    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    tag = CharField()
    offset = BigIntegerField(null = True)

class roles(BaseModel):
    id = PrimaryKeyField()
    RoleID = BigIntegerField()
    tag = ForeignKeyField(role_tags, db_column = 'tag', null = True)
    expires = DateTimeField(null = True)

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
db.create_tables([guilds, members, role_tags, roles, candidates])

