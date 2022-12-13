import discord
import cogs
from database import *
from discord.ext import commands

class debug_commands(commands.Cog):
    bot = discord.Bot

    def __init__(self, bot):
        self.bot = bot

    debug = discord.SlashCommandGroup("debug", 'debug commands')

    @debug.command()
    async def force_election(self, ctx):
        await ctx.respond(content="Forcing elections...")
        await cogs.backend.elections(self.bot)

    @debug.command()
    async def force_reset(self, ctx):
        await ctx.respond(content="Forcing reset...")
        await cogs.backend.reset(self.bot)
