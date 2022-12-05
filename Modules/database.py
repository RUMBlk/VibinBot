import atexit
from peewee import *

db = SqliteDatabase('tmp/session/VibinBot.db', pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta:
        database = db

class guilds(BaseModel):
    id = AutoField()
    GuildID = BigIntegerField()

class members(BaseModel):
    id = AutoField()
    GuildID = ForeignKeyField(guilds, to_field = 'GuildID')
    UserID = BigIntegerField()
    msg_count = IntegerField()
    points = IntegerField()

class roles(BaseModel):
    id = AutoField()
    GuildID = ForeignKeyField(guilds, to_field = 'GuildID')
    UserID = ForeignKeyField(members, to_field = 'UserID')
    RoleID = BigIntegerField()
    Group = CharField()
    ExpiresAt = DateTimeField(null = True)

class candidates(BaseModel):
    id = AutoField()
    GuildID =  ForeignKeyField(guilds, to_field = 'GuildID')
    UserID =  ForeignKeyField(members, to_field = 'UserID')

class votes(BaseModel):
    id = AutoField()
    GuildID = BigIntegerField()
    UserID = BigIntegerField()
    Supports = BigIntegerField()

db.connect()
db.create_tables([guilds, members, roles, votes])

