import discord
import society
from database import *
from discord.ext import commands

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
        print(message.content)
        print(message.embeds)
        print(message.attachments)
        print('--f--')