import discord
import traceback
from discord.ext import tasks, commands
from datetime import datetime as dt
from datetime import date
from peewee import *
import database as db
import localisation as loc
import tabulate

#db
class points_ignore(db.BaseModel):
    id = PrimaryKeyField()
    Channel = ForeignKeyField(db.channels, db_column = 'Channel')

db.db.create_tables([points_ignore,])

on_message = []

#func
def on_message_listener(func):
    on_message.append(func)

async def memberToName(ctx, member):
    try:
        UserID = ctx.guild.get_member(member.UserID)
        if UserID is None: UserID = await ctx.guild.fetch_member(member.UserID)
        member_name = UserID.display_name
        if len(member_name) > 18: member_name = f'{member_name[:18]}...' 
    except:
        member_name = member.UserID
    return member_name

async def form_leaderboard(ctx, dbToName, table):
    leaderboard = []
    summ = 0
    i = 0
    for member in table:
        i += 1
        member_name = await dbToName(ctx, member)
        leaderboard.append([i, member_name, member.Points])
        summ += member.Points
        if i == 10: break
    return leaderboard, summ

class society(commands.Cog):
    bot = discord.Bot()
    locale_class = loc.locale().get('society')
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        if message.author.bot is False:
            guild = db.guilds.get_or_create(GuildID = message.guild.id)[0]
            author = db.members.get_or_create(GuildID = guild.id, UserID = message.author.id)[0]
            reward = 0
            author.msg_count += 1
            ##The punctuation reward requires more conditions to prevent abusing
            #charset = '`!@#$%^&*()-+*/,.<>;:[]{}\\|\'\"'
            #for char in charset:
            #    reward += message.content.count(f'{char} ') * 10

            reward += int(round(len(message.content) * 0.1)) #Content reward
            reward += (len(message.attachments) + len(message.stickers) + len(message.embeds)) * 10 #quickly made formula for attachments, stickers and embeds reward

            author.Points += reward
            author.save()

            for func in on_message:
                await func([self.bot, message, reward])

    society = discord.SlashCommandGroup("society", locale_class.get('desc'))

    @society.command(description = locale_class.get('add').get('desc'))
    async def add(self, ctx, member: discord.Member, amount: int):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('society').get('add')
        ephemeral = True
        if ctx.channel.permissions_for(ctx.guild.me).send_messages: ephemeral = False
        if ctx.author != ctx.guild.owner: answer = locale.get('bot_denied').format_map({'permission': locale.get('permissions').get('owner')})
        else:
            memberDB = db.members.get_or_create(GuildID = guildDB.id, UserID = member.id)[0]
            memberDB.Points += amount
            memberDB.save()
            answer = locale_func.get('success')
        await ctx.respond(content=answer.format_map({'amount': amount, 'member': member}))

    @society.command(description = locale_class.get('ignore').get('desc'))
    async def ignore(self, ctx, channel: discord.TextChannel):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('ignore')
        ephemeral = True
        if ctx.channel.permissions_for(ctx.guild.me).send_messages: ephemeral = False
        if ctx.author != ctx.guild.owner: answer = locale.get('bot_denied').format_map({'permission': locale.get('permissions').get('owner')})
        else:
            channelDB = db.channels.get_or_create(ChannelID = channel.id)
            points_ignore.get_or_create(Channel = channelDB[0].id)
            answer=locale_func.get('success')
        await ctx.respond(content = answer)

    #points = discord.SlashCommandGroup("points", locale().get('points_desc'))

    @society.command(description = locale_class.get('leaderboard').get('desc'))
    async def leaderboard(self, ctx):
        guildDB = db.guilds.get_or_create(GuildID = ctx.guild.id)[0]
        locale = loc.locale(guildDB.locale)
        locale_func = locale.get('society').get('leaderboard')
        #embed = None
        ephemeral = True
        if ctx.channel.permissions_for(ctx.guild.me).send_messages: ephemeral = False
        membersDB = db.members.select().where(db.members.GuildID == guildDB.id).order_by(db.members.Points.desc())
        leaderboard, server_value = await form_leaderboard(ctx, memberToName, membersDB)
        leaderboard = '```' + tabulate.tabulate(leaderboard, headers = [locale_func.get('embed').get('place'), locale_func.get('embed').get('members'), locale_func.get('embed').get('points')], tablefmt = 'github') + '```'
        leaderboard += '```' + locale_func.get('embed').get('summ').format_map({'server_value': server_value}) + '```'

        #embed = await backend.leaderboard_embed(ctx, self.bot, leaderboard, locale)
        #if embed is not None: status += 'success'
        #else: status += 'empty'
        await ctx.respond(content = leaderboard, ephemeral = ephemeral, allowed_mentions = None)






