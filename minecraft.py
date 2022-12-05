from datetime import datetime
from mcstatus import JavaServer
from mcstatus import BedrockServer
import discord
from discord.ext import commands
from database import *

class servers(BaseModel):
    id = PrimaryKeyField()
    IP = CharField()
    edition = CharField()
    version = CharField()
    online = BooleanField()

class legacy(BaseModel):
    id = PrimaryKeyField()
    type = CharField()
    MessageID = BigIntegerField(null = True)
    ChannelID = BigIntegerField()
    IP = ForeignKeyField(servers, db_column = 'IP')
    edition = CharField()
    role = CharField(null = True)

db.create_tables([servers, legacy])

def ping_mc(ip, edition):
    if(edition[0] == 'J'):
        server = JavaServer.lookup(ip, timeout = 5)
    else:
        server = BedrockServer.lookup(ip, timeout = 1)
    return server

async def compile_embed(server, ip, edition, version):
    embed = discord.Embed(
        title = "[{0} {1}]{2} Server Status".format(edition, version, ip),
        timestamp = datetime.now()
        )
    try:
        status = server.status()
        status_disp = f":green_circle:Online: {status.players.online}/{status.players.max}"
    except:
        status_disp = f":red_circle:Offline"
    embed.add_field(name = "Edition", value = edition)
    embed.add_field(name = "Server IP", value = ip)
    embed.add_field(name = "Players", value = status_disp)
    return embed

#Discord
class mc_cmd(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot, debug=False):
        self.bot = bot
    @bot.slash_command(description = "Generates an embed message with mc server status. All fields are not case sensitive")
    async def addserver(self, ctx, ip, edition = 'JAVA'):
        role = discord.utils.get(ctx.guild.roles, name="MinecraftOp")
        if role in ctx.author.roles:
            edition = edition.upper()

        response = await ctx.respond(content="Please wait for the next status update, usually it doesn't takes more than 1 minute.")
        message = await response.original_message()
        server = mc.servers.get_or_create(IP = ip, edition = edition, online = False, version = "Unknown")[0]
        mc.legacy.create(MessageID = message.id, type = "update", ChannelID = ctx.channel.id, IP = server.id, edition = edition)

    @bot.slash_command(description = "Sets channel for mc server status notifications")
    async def setnotification(self, ctx, ip, edition = 'JAVA', sub_role = ''):
        role = discord.utils.get(ctx.guild.roles, name="MinecraftOp")
        if role in ctx.author.roles:
            edition = edition.upper()

        response = await ctx.respond(content=f"Notifications for [{edition[0][0]}]{ip} status set!")
        server = mc.servers.get_or_create(IP = ip, edition = edition, online = False, version = "Unknown")[0]
        mc.legacy.create(type = "notify", ChannelID = ctx.channel.id, edition = edition, IP = server.id, role = sub_role)

    @bot.slash_command(description = "Removes mc server status notifications for this channel.")
    async def stopnotification(self, ctx, ip, edition = 'JAVA', sub_role = ''):
        role = discord.utils.get(ctx.guild.roles, name="MinecraftOp")
        if role in ctx.author.roles:
            edition = edition.upper()
            try:
                mc.legacy.get(mc.legacy.ChannelID == ctx.channel.id, mc.legacy.type == "notify").delete_instance()
                content = "Record deleted"
            except: content = "not found"
            await ctx.respond(content)




