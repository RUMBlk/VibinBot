import discord
import traceback
from discord.ext import tasks, commands
from datetime import datetime as dt
from datetime import date
from database import *
import localisation as loc
import tabulate

#db
class points_ignore(BaseModel):
    id = PrimaryKeyField()
    Channel = ForeignKeyField(channels, db_column = 'Channel')

db.create_tables([points_ignore,])

on_message = []

def on_message_listener(func):
    on_message.append(func)

class events(commands.Cog):
    bot = discord.Bot()

    @commands.Cog.listener("on_ready")
    async def on_startup(self):
        for guild in self.bot.guilds:
            guild_db = None
            try:
                guild_db = guilds.get(guilds.GuildID == guild.id)
            except:
                guild_db = guilds.create(GuildID = guild.id)

            for member in guild.members:
                if member.bot is False:
                    try:
                        members.get(members.GuildID == guild_db.id, members.UserID == member.id)
                    except: 
                        members.create(GuildID = guild_db.id, UserID = member.id, msg_count = 0, points = 0)

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join(self, guild):
        try:
            guilds.get(guilds.GuildID == guild.id)
        except:
            guilds.create(GuildID = guild.id)


    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        channelDB = channels.get_or_none(ChannelID = message.channel.id)
        if message.author.bot is False and channelDB is None:
            guild = guilds.get(GuildID = message.guild.id)
            try:
                author = members.get(members.GuildID == guild.id, members.UserID == message.author.id)
            except:
                author = members.create(GuildID = guild.id, UserID = message.author.id, msg_count = 0, points = 0)
            reward = 0
            author.msg_count += 1
            ##The punctuation reward requires more conditions to prevent abusing
            #charset = '`!@#$%^&*()-+*/,.<>;:[]{}\\|\'\"'
            #for char in charset:
            #    reward += message.content.count(f'{char} ') * 10

            reward += int(round(len(message.content) * 0.1)) #Content reward
            reward += (len(message.attachments) + len(message.stickers) + len(message.embeds)) * 10 #quickly made formula for attachments, stickers and embeds reward

            author.points += reward
            author.save()

            for func in on_message:
                await func(message, reward)

class points(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot):
        self.bot = bot

    points_edit = discord.SlashCommandGroup("points_edit", loc.get('points_edit_desc'))

    @points_edit.command(description = loc.get('points_add_desc'))
    async def add(self, ctx, member: discord.Member, amount: int):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'points_edit_add_'
        try:
            if ctx.author == ctx.guild.owner:
                    try:
                        member = members.get(members.GuildID == guild.id, members.UserID == member.id)
                        member.points += amount
                        member.save()
                        status += 'success'
                    except: status += 'no_member'
            else:
                status = 'channel_denied'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale))

    @points_edit.command(description = loc.get('points_edit_ignore_desc'))
    async def ignore(self, ctx, channel: discord.TextChannel):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'points_edit_ignore_'
        try:
            channelDB = channels.get_or_create(ChannelID = channel.id)
            points_ignore.get_or_create(Channel = channelDB[0].id)
            status += 'success'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale))

    #points = discord.SlashCommandGroup("points", loc.get('points_desc'))

    @bot.slash_command(description = loc.get('leaderboard_desc'))
    async def leaderboard(self, ctx):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        leaderboard = []
        #embed = None
        ephemeral = True
        if ctx.guild.me.guild_permissions.send_messages: ephemeral = False
        response = await ctx.respond(content = loc.get('leaderboard_proc', locale), ephemeral = ephemeral)
        message = await response.original_response()
        status = 'leaderboard_'
        try:
            guild = guilds.get(guilds.GuildID == ctx.guild.id)
            membersDB = members.select().where(members.GuildID == guild.id).order_by(members.points.desc())
            server_value = 0
            i = 0
            for member in membersDB:
                i += 1
                UserID = ctx.guild.get_member(member.UserID)
                member_name = UserID.display_name
                if len(member_name) > 18: member_name = f'{member_name[:18]}...' 
                leaderboard.append([i, member_name, member.points])
                server_value += member.points
                if i == 10: break
            leaderboard = '```' + tabulate.tabulate(leaderboard, headers = [loc.get('leaderboard_embed_place', locale), loc.get('leaderboard_embed_members', locale), loc.get('leaderboard_embed_points', locale)], tablefmt = 'github') + '```'
            leaderboard += '```' + loc.get('leaderboard_embed_sum', locale).format_map({'server_value': server_value}) + '```'
            status = leaderboard

            #embed = await backend.leaderboard_embed(ctx, self.bot, leaderboard, locale)
            #if embed is not None: status += 'success'
            #else: status += 'empty'
        except:
            traceback.print_exc()
            status = 'exception'
            embed = None
        await message.edit(content = status, allowed_mentions = None)

class backend():
    def leaderboard_place(guild_db_id, member_id):
        leaderboard = leaderboard = members.select().where(members.GuildID == guild_db_id).order_by(members.points.desc())
        place = 0
        for member in leaderboard:
            place += 1
            if member.UserID == member_id: return place

    async def leaderboard_embed(ctx, bot, leaderboard, locale):
        embed = None
        place_field = ""
        user_field = ""
        points_field = ""
        server_value = 0
        i = 0
        for member in leaderboard:
            i += 1
            place_field += str(i) + "\n"
            UserID = await bot.fetch_user(member.UserID)
            user_field += UserID.display_name + "\n"
            points_field += str(member.points) + "\n"
            server_value += member.points
            if i == 10: break
        embed = discord.Embed(
            title = loc.get('leaderboard_embed_title', locale).format_map({'guild': ctx.guild.name}),
            timestamp = dt.now()
        )
        embed.add_field(name = loc.get('leaderboard_embed_place', locale), value = place_field)
        embed.add_field(name = loc.get('leaderboard_embed_members', locale), value = user_field)
        embed.add_field(name = loc.get('leaderboard_embed_points', locale), value = points_field)
        embed.add_field(name = loc.get('leaderboard_embed_sum', locale).format_map({'server_value': server_value}), value = '')
        if i == 0:
            return None
        else:
            return embed






