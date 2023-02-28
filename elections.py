import discord
import traceback
from discord.ext import tasks, commands
import localisation as loc
from peewee import *
import database as db
import cogs

#Database
class elections(db.BaseModel):
    id = PrimaryKeyField()
    GuildID = ForeignKeyField(db.guilds, db_column = 'GuildID')
    RoleID = ForeignKeyField(db.guilds, db_column = 'RoleID')
    Limit = IntegerField(default = 1)

class claimers(db.BaseModel):
    id = PrimaryKeyField()
    ElectID = ForeignKeyField(elections, db_column = 'ElectID')
    UserID =  ForeignKeyField(db.members, db_column = 'UserID')
    Points = IntegerField(default = 0)

class supporters(db.BaseModel):
    id = PrimaryKeyField()
    #GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    UserID = ForeignKeyField(db.members, db_column = 'UserID')
    Claimer = ForeignKeyField(claimers, db_column = 'Claimer')

db.db.create_tables([elections, claimers, supporters])
#Db shortcuts
def get_election_group(guildDB, role):
    roleDB = db.roles.get_or_none(db.roles.RoleID == role.id)
    electionDB = elections.get_or_none(elections.GuildID == guildDB.id, elections.RoleID == roleDB.id)
    return {'roleDB': roleDB, 'electionDB': electionDB}

def get_claimer_group(guildDB, role, memberDB):
    db_group = get_election_group(guildDB, role)
    db_group['claimerDB'] = claimers.get_or_none(claimers.ElectID == db_group.electionDB.id, claimers.UserID == memberDB.id)
    return db_group

def get_support_group(guildDB, role, memberDB, authorDB):
    db_group = get_claimer_group(guildDB, role, memberDB)
    db_group['supportDB'] = supporters.get_or_none(supporters.UserID == authorDB.id, supporters.Claimer == db_group.claimerDB.id)
    return db_group
#Database end

async def elect(guild, election, guildDB = None):
    if guildDB is None: guildDB = db.guilds.get(db.guilds.GuildID == message.guild.id)
    claims = claimers.select().where(claimers.ElectID == election.id).order_by(claimers.Points.desc())
    role = guild.get_role(db.roles.get(db.roles.id == election.RoleID).RoleID)
    winners = []

    i = 0
    for claim in claims:
        member = db.members.get(db.members.id == claim.UserID)
        if (i < election.Limit):
           winners.append(guild.get_member(member.UserID))
           i += 1
        else: break
    for member in role.members:
        if member not in winners: await member.remove_roles(role)
    for winner in winners: await winner.add_roles(role)
    #if guild.system_channel:
    #    await guild.system_channel.send(locale().get('admin_congrats', guildDB.locale).format_map({'new_admin_id': admin_member.id}))

@cogs.on_message_listener
async def on_message(args):
    message = args[1]
    reward = args[2]
    try:
        guild = db.guilds.get(db.guilds.GuildID == message.guild.id)
        member = db.members.get(db.members.GuildID == guild.id, db.members.UserID == message.author.id)
        supports = supporters.select().where(supporters.UserID == member.id)
        planned_elections = []
        for support in supports:
            claimer = claimers.get(claimers.id == support.Claimer)
            election = elections.get(elections.id == claimer.ElectID)
            if str(election.GuildID) == str(guild.id):
                claimer.Points += reward
                claimer.save()
                if election not in planned_elections: planned_elections.append(election)
        for election in planned_elections:
            await elect(message.guild, election, guild)
    except: traceback.print_exc()

#Discord Cog
class electionsCog(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get('elections')
    def __init__(self, bot):
        self.bot = bot

    elections = discord.SlashCommandGroup("elections", locale_class.get('desc'))

    @elections.command(description = locale_class.get('add').get('desc'))
    async def add(self, ctx, role: discord.Role, limit = 1):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('elections').get('add')
        if not (ctx.guild.me.guild_permissions.manage_roles): answer = locale('bot_denied')
        elif ctx.author != ctx.guild.owner: answer = locale_func.get('user_denied')
        else:
            roleDB = db.roles.get_or_create(RoleID = role.id)[0]
            electionsDB = elections.get_or_create(GuildID = guildDB.id, RoleID = roleDB.id)
            if electionsDB[1] is True: answer = locale_func.get('success')
            else: answer = locale_func.get('exists')
            
        await ctx.respond(content = answer.format_map({'role_name': role.name, 'permission': locale.get('manage_roles')}))

    @elections.command(description = locale_class.get('delete').get('desc'))
    async def delete(self, ctx, role: discord.Role):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('elections')
        locale_func = locale_class.get('delete')
        if not (ctx.guild.me.guild_permissions.manage_roles): answer = locale('bot_denied')
        elif ctx.author != ctx.guild.owner: answer = locale('user_denied')
        else:
            with get_election_group(guildDB, role) as db_group:
                if db_group.electionDB is None: answer = locale_class.get('no_such_elections')
                else:
                    roleDB = db.roles.get(db.roles.RoleID == role.id)
                    election = elections.get(elections.RoleID == roleDB.id)
                    election.delete_instance()
                    answer = locale_func.get('success')
        await ctx.respond(content = answer.format_map({'role_name': role.name, 'permission': locale.get('manage_roles')}))


    @elections.command(description = locale_class.get('claim').get('desc'))
    async def claim(self, ctx, role: discord.Role):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('elections')
        locale_func = locale_class.get('claim')
        if not (ctx.guild.me.guild_permissions.manage_roles): answer = locale('bot_denied')
        else:
            memberDB = db.members.get_or_create(GuildID = guildDB.id, UserID = ctx.author.id)[0]
            with get_election_group(guildDB, role) as db_group:
                if db_group.electionDB is None: answer = locale_class.get('no_such_elections')
                else:
                    claimersDB = claimers.get_or_create(ElectID = db_group.electionDB.id, UserID = memberDB.id)
                    if claimersDB[1] is True: answer = locale_func.get('success')
                    else: answer = locale_func.get('exists')
        await ctx.respond(content = answer.format_map({'permission': locale.get('manage_roles')}))

    @elections.command(description = locale_class.get('unclaim').get('desc'))
    async def unclaim(self, ctx, role: discord.Role):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('elections')
        locale_func = locale_class.get('unclaim')
        if not (ctx.guild.me.guild_permissions.manage_roles): answer = locale('bot_denied')
        else:
            memberDB = db.members.get_or_create(GuildID = guildDB.id, UserID = ctx.author.id)[0]
            with get_election_group(guildDB, role) as db_group:
                if db_group.electionDB is None: locale_class.get('no_such_elections')
                elif db_group.claimerDB is None: answer = locale_func.get('not_candidate')
                else:
                    claimDB = claimers.get_or_none(claimers.ElectID == db_group.electionDB.id, claimers.UserID == memberDB.id)
                    delete_supports=supporters.delete().where(supporters.Claimer==claimDB.id)
                    delete_supports.execute()
                    claimDB.delete_instance()
                    await elect(ctx.guild, db_group.electionDB, guildDB)
                    answer = locale_func.get('success')
        await ctx.respond(content=answer.format_map({'permission': locale.get('manage_roles')}))

    @elections.command(description = locale_class.get('support').get('desc'))
    async def support(self, ctx, role: discord.Role, claimer: discord.Member):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('elections')
        locale_func = locale_class.get('support')
        if not (ctx.guild.me.guild_permissions.manage_roles): answer = locale('bot_denied')
        else:
            authorDB = db.members.get_or_create(GuildID = guildDB.id, UserID = ctx.author.id)[0]
            memberDB = db.members.get_or_none(db.members.GuildID == guildDB.id, db.members.UserID == claimer.id)
            if memberDB is None: answer = locale_class.get('not_candidate')
            else:
                with get_support_group(guildDB, role, memberDB, authorDB) as db_group:
                    if db_group.electionDB is None: answer = locale_class.get('no_such_elections')
                    elif db_group.claimerDB is None: answer = locale_class.get('not_candidate')
                    elif db_group.supportDB is not None: locale_func.get("exists")
                    else:
                        db_group.claimerDB.Points += memberDB.points
                        db.branch.claimerDB.save()
                        await elect(ctx.guild, db_group.electionDB, guildDB)
                        answer = locale_func.get('success')
        await ctx.respond(content=answer.format_map({'permission': locale.get('manage_roles'), 'claimer': claimer}))

    @elections.command(description = locale_class.get('unsupport').get('desc'))
    async def unsupport(self, ctx, role: discord.Role, claimer: discord.Member):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_class = locale.get('elections')
        locale_func = locale_class.get('unsupport')
        if not (ctx.guild.me.guild_permissions.manage_roles): answer = locale('bot_denied')
        else:
            authorDB = db.members.get_or_create(GuildID = guildDB.id, UserID = ctx.author.id)[0]
            memberDB = db.members.get_or_none(db.members.GuildID == guildDB.id, db.members.UserID == claimer.id)
            if memberDB is None: answer = locale_class.get('not_candidate')
            else:
                with get_support_group(guildDB, role, memberDB, authorDB) as db_group:
                    if db_group.electionDB is None: answer = locale_class.get('no_such_elections')
                    elif db_group.claimerDB is None: answer = locale_class.get('not_candidate')
                    elif db_group.supportDB is None: locale_class.get("not_supporter")
                    else:
                        db_group.claimerDB.Points -= authorDB.points
                        db_group.claimerDB.save()
                        db_group.supportDB.delete_instance()
                        await elect(ctx.guild, db_group.electionDB, guildDB)
                        answer = locale_func.get('success')
        await ctx.respond(content=answer.format_map({'permission': locale.get('manage_roles'), 'claimer': claimer}))