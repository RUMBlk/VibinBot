import discord
import society
from database import *
from discord.ext import commands

class debug_commands(commands.Cog):
    bot = discord.Bot

    def __init__(self, bot):
        self.bot = bot

    debug = discord.SlashCommandGroup("debug", 'debug commands')
