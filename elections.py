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
    Points = IntegerField()

class supporters(db.BaseModel):
    id = PrimaryKeyField()
    #GuildID = ForeignKeyField(guilds, db_column = 'GuildID')
    UserID = ForeignKeyField(db.members, db_column = 'UserID')
    Claimer = ForeignKeyField(claimers, db_column = 'Claimer')

db.db.create_tables([elections, claimers, supporters])
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
    #    await guild.system_channel.send(loc.get('admin_congrats', guildDB.locale).format_map({'new_admin_id': admin_member.id}))

@cogs.on_message_listener
async def on_message(message, reward):
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
    def __init__(self, bot):
        self.bot = bot

    elections = discord.SlashCommandGroup("elections", loc.get('elections_desc'))

    @elections.command(description = loc.get('elections_add_desc'))
    async def add(self, ctx, role: discord.Role, limit = 1):
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'elections_add_'
        try:
            if not (ctx.guild.me.guild_permissions.manage_roles and ctx.author == ctx.guild.owner):
                status = 'bot_denied'
            elif ctx.author == ctx.guild.owner:
                    try:
                        roleDB = db.roles.get(db.roles.RoleID == role.id)
                    except:
                        roleDB = db.roles.create(RoleID = role.id)
                    try:
                        elections.get(elections.RoleID == roleDB.id)
                        status += 'exists'
                    except:
                        elections.create(GuildID = guild.id, RoleID = roleDB.id, Limit = limit)
                        status += 'success'
            else:
                status = 'channel_denied'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'role_name': role.name, 'permission': loc.get('manage_roles', guild.locale)}))

    @elections.command(description = loc.get('elections_delete_desc'))
    async def delete(self, ctx, role: discord.Role):
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'elections_delete_'
        try:
            if not (ctx.guild.me.guild_permissions.manage_roles and ctx.author == ctx.guild.owner):
                status = 'bot_denied'
            elif ctx.author == ctx.guild.owner:
                    try:
                        roleDB = db.roles.get(db.roles.RoleID == role.id)
                        election = elections.get(elections.RoleID == roleDB.id)
                        election.delete().execute()
                        status += 'success'
                    except:
                        status += 'fail'
            else:
                status = 'channel_denied'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'role_name': role.name, 'permission': loc.get('manage_roles', guild.locale)}))


    @elections.command(description = loc.get('elections_claim_desc'))
    async def claim(self, ctx, role: discord.Role):
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'elections_claim_'

        try:
            if not (ctx.guild.me.guild_permissions.manage_roles):
                status = 'bot_denied'
            else:
                member = db.members.get(db.members.GuildID == guild.id, db.members.UserID == ctx.author.id)
                try:
                    roleDB = db.roles.get(db.roles.RoleID == role.id)
                    elect = elections.get(elections.GuildID == guild.id, elections.RoleID == roleDB.id)
                    try:
                        claimers.get(claimers.ElectID == elect.id, claimers.UserID == member.id)
                        status += 'exists'
                    except:
                        claimers.create(ElectID = elect.id, UserID = member.id, Points = 0)
                        status += 'success'
                except:
                    status += 'no_such_elections'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'permission': loc.get('manage_roles', guild.locale)}))

    @elections.command(description = loc.get('elections_unclaim_desc'))
    async def unclaim(self, ctx, role: discord.Role):
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'elections_unclaim_'

        try:
            if not (ctx.guild.me.guild_permissions.manage_roles):
                status = 'bot_denied'
            else:
                member = db.members.get(db.members.GuildID == guild.id, db.members.UserID == ctx.author.id)
                try:
                    roleDB = db.roles.get(db.roles.RoleID == role.id)
                    election = elections.get(elections.GuildID == guild.id, elections.RoleID == roleDB.id)
                    try:
                        claim = claimers.get(claimers.ElectID == election.id, claimers.UserID == member.id)
                        claim.delete().execute()
                        await elect(ctx.guild, election, guild)
                        status += 'success'
                    except:
                        traceback.print_exc()
                        status += 'fail'
                except:
                    status += 'no_such_elections'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'permission': loc.get('manage_roles', guild.locale)}))

    @elections.command(description = loc.get('elections_support_desc'))
    async def support(self, ctx, role: discord.Role, claimer: discord.Member):
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale), ephemeral = True)
        message = await response.original_response()
        status = 'elections_support_'

        try:
            if not (ctx.guild.me.guild_permissions.manage_roles):
                status = 'bot_denied'
            else:
                try:
                    author = db.members.get(db.members.GuildID == guild.id, db.members.UserID == ctx.author.id)
                    member = db.members.get(db.members.GuildID == guild.id, db.members.UserID == claimer.id)
                    roleDB = db.roles.get(db.roles.RoleID == role.id)
                    election = elections.get(elections.GuildID == guild.id, elections.RoleID == roleDB.id)
                    try:
                        claimerDB = claimers.get(claimers.ElectID == election.id, claimers.UserID == member.id)
                        try:
                            supporters.get(supporters.UserID == author.id, supporters.Claimer == claimerDB.id)
                            status += 'exists'
                        except:
                            supporters.create(UserID = author.id, Claimer = claimerDB.id)
                            claimerDB.Points += member.points
                            claimerDB.save()
                            await elect(ctx.guild, election, guild)
                            status += 'success'
                    except:
                        status = 'elections_not_candidate'
                except:
                   status = "author_not_found"
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'permission': loc.get('manage_roles', guild.locale), 'claimer': claimer}))

    @elections.command(description = loc.get('elections_unsupport_desc'))
    async def unsupport(self, ctx, role: discord.Role, claimer: discord.Member):
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale), ephemeral = True)
        message = await response.original_response()
        status = 'elections_unsupport_'

        try:
            if not (ctx.guild.me.guild_permissions.manage_roles):
                status = 'bot_denied'
            else:
                try:
                    author = db.members.get(db.members.GuildID == guild.id, db.members.UserID == ctx.author.id)
                    member = db.members.get(db.members.GuildID == guild.id, db.members.UserID == claimer.id)
                    roleDB = db.roles.get(db.roles.RoleID == role.id)
                    election = elections.get(elections.GuildID == guild.id, elections.RoleID == roleDB.id)
                    try:
                        claimerDB = claimers.get(claimers.ElectID == election.id, claimers.UserID == member.id)
                        try:
                            support = supporters.get(supporters.UserID == author.id, supporters.Claimer == claimerDB.id)
                            claimerDB.Points -= author.points
                            claimerDB.save()
                            support.delete().execute()
                            await elect(ctx.guild, election, guild)
                            status += 'success'
                        except:
                            status += 'fail'
                    except:
                        status = 'elections_not_candidate'
                except:
                   status = "author_not_found"
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'permission': loc.get('manage_roles', guild.locale), 'claimer': claimer}))