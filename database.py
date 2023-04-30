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
    reports_channel = BigIntegerField(null = True)

class channels(BaseModel):
    id = PrimaryKeyField()
    ChannelID = BigIntegerField()
    shareCode = CharField(null = True)

class members(BaseModel):
    id = PrimaryKeyField()
    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    UserID = BigIntegerField()
    msg_count = IntegerField(default = 0)
    Points = IntegerField(default = 0)
    Timezone = CharField(default = '')

#class role_tags(BaseModel):
#    id = PrimaryKeyField()
#    GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
#    tag = CharField()
#    original = BigIntegerField(null = True)

class roles(BaseModel):
    id = PrimaryKeyField()
    #GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    RoleID = BigIntegerField()
    #tag = ForeignKeyField(role_tags, db_column = 'tag', null = True)
    #expires = DateField(null = True)

db.connect()
db.create_tables([internal, guilds, channels, members, roles])

