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
            guild_db = guilds.get_or_create(GuildID = guild.id)[0]

            for member in guild.members:
                if member.bot is False:
                    members.get_or_create(GuildID = guild_db.id, UserID = member.id)

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
        if message.author.bot is False:
            guild = guilds.get(GuildID = message.guild.id)
            author = members.get_or_create(GuildID = guild.id, UserID = message.author.id)[0]
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
                await func([self.bot, message, reward])

class society(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get('society')
    def __init__(self, bot):
        self.bot = bot

    society = discord.SlashCommandGroup("society", locale_class.get('desc'))

    @society.command(description = locale_class.get('add').get('desc'))
    async def add(self, ctx, member: discord.Member, amount: int):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        if ctx.author != ctx.guild.owner: answer = locale.get('bot_denied').format_map({'permission': locale.get('owner')})
        else:
            member = members.get_or_create(GuildID = guildDB.id, UserID = member.id)[0]
            member.points += amount
            member.save()
            answer = locale.get('success')
        await ctx.respond(content=answer)

    @society.command(description = locale_class.get('ignore').get('desc'))
    async def ignore(self, ctx, channel: discord.TextChannel):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('ignore')
        if ctx.author != ctx.guild.owner: answer = locale.get('bot_denied').format_map({'permission': locale.get('owner')})
        else:
            channelDB = channels.get_or_create(ChannelID = channel.id)
            points_ignore.get_or_create(Channel = channelDB[0].id)
            answer=locale_func.get('success')
        await ctx.respond(content = answer)

    #points = discord.SlashCommandGroup("points", locale().get('points_desc'))

    @society.command(description = locale_class.get('leaderboard').get('desc'))
    async def leaderboard(self, ctx):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('society').get('leaderboard')
        leaderboard = []
        #embed = None
        ephemeral = True
        if ctx.channel.permissions_for(ctx.guild.me).send_messages: ephemeral = False
        response = await ctx.respond(content = locale_func.get('processing'), ephemeral = ephemeral)
        message = await response.original_response()

        membersDB = members.select().where(members.GuildID == guildDB.id).order_by(members.points.desc())
        server_value = 0
        i = 0
        for member in membersDB:
            i += 1
            try:
                UserID = ctx.guild.get_member(member.UserID)
                if UserID is None: UserID = await ctx.guild.fetch_member(member.UserID)
                member_name = UserID.display_name
                if len(member_name) > 18: member_name = f'{member_name[:18]}...' 
            except:
                member_name = member.UserID
            leaderboard.append([i, member_name, member.points])
            server_value += member.points
            if i == 10: break
        leaderboard = '```' + tabulate.tabulate(leaderboard, headers = [locale_func.get('embed').get('place'), locale_func.get('embed').get('members'), locale_func.get('embed').get('points')], tablefmt = 'github') + '```'
        leaderboard += '```' + locale_func.get('embed').get('sum').format_map({'server_value': server_value}) + '```'

        #embed = await backend.leaderboard_embed(ctx, self.bot, leaderboard, locale)
        #if embed is not None: status += 'success'
        #else: status += 'empty'
        await message.edit(content = leaderboard, allowed_mentions = None)

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
            title = locale().get('leaderboard_embed_title', locale).format_map({'guild': ctx.guild.name}),
            timestamp = dt.now()
        )
        embed.add_field(name = locale().get('leaderboard_embed_place', locale), value = place_field)
        embed.add_field(name = locale().get('leaderboard_embed_members', locale), value = user_field)
        embed.add_field(name = locale().get('leaderboard_embed_points', locale), value = points_field)
        embed.add_field(name = locale().get('leaderboard_embed_sum', locale).format_map({'server_value': server_value}), value = '')
        if i == 0:
            return None
        else:
            return embed






