import discord
import society
from database import *
from discord.ext import commands
import datetime

class debug_commands(commands.Cog):
    bot = discord.Bot

    def __init__(self, bot):
        self.bot = bot

    debug = discord.SlashCommandGroup("debug", 'debug commands')
    @debug.command()
    async def fetch_message(self, ctx, messageid):
        channel = await ctx.bot.fetch_channel(ctx.channel.id)
        message = await channel.fetch_message(messageid)
        print('--f--')
        print(int(round(message.created_at.timestamp())))
        print(message.content)
        print(message.embeds)
        print(message.attachments)
        print('--f--')

    @debug.command()
    async def fetch_history(self, ctx, timestamp: int):
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        channel = await ctx.bot.fetch_channel(ctx.channel.id)
        async for msg in channel.history(around = timestamp, limit = 11):
            print(msg.content)