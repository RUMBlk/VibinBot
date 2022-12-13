import os
from dotenv import load_dotenv, find_dotenv
from peewee import *
from datetime import date

load_dotenv(find_dotenv())

db = None

if os.getenv('DEBUG') is None: db = PostgresqlDatabase(os.environ['DB_NAME'], user=os.environ['DB_USER'], password=os.environ['DB_PASS'], host=os.environ['DB_HOST'], port=os.environ['DB_PORT'])
else: db = SqliteDatabase('tmp/debug.db')

class BaseModel(Model):
    class Meta:
        database = db

class internal(BaseModel):
    id = PrimaryKeyField()
    last_reset = DateField(default = date(1970, 1, 1))

class guilds(BaseModel):
    id = PrimaryKeyField()
    GuildID = BigIntegerField()
    locale = CharField(default = "en_US")

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
    original = BigIntegerField(null = True)

class roles(BaseModel):
    id = PrimaryKeyField()
    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    RoleID = BigIntegerField()
    tag = ForeignKeyField(role_tags, db_column = 'tag', null = True)
    expires = DateField(null = True)

class candidates(BaseModel):
    id = PrimaryKeyField()
    GuildID =  ForeignKeyField(guilds, db_column = 'GuildID')
    UserID =  ForeignKeyField(members, db_column = 'UserID')

class votes(BaseModel):
    id = PrimaryKeyField()
    UserID = ForeignKeyField(members, db_column = 'UserID')
    candidate = ForeignKeyField(candidates, db_column = 'candidate')

db.connect()
db.create_tables([internal, guilds, members, role_tags, roles, candidates, votes])

