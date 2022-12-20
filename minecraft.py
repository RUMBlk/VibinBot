from database import *
from datetime import datetime
from mcstatus import JavaServer
from mcstatus import BedrockServer
import discord
from discord.ext import commands, tasks
import cogs
import traceback
import localisation as loc

#Section: Database
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
    locale = CharField(default = 'en_US')

db.create_tables([servers, legacy])

async def ping_mc(ip, edition):
    if(edition[0] == 'J'):
        server = await JavaServer.async_lookup(ip)
    else:
        server = await BedrockServer.async_lookup(ip)
    return server

async def compile_embed(locale, server, ip, edition, version):
    embed = discord.Embed(
        title = loc.get('mc_status_embed_title', locale).format(edition=edition, version=version, ip=ip),
        timestamp = datetime.now()
        )
    try:
        status = server.status()
        status_disp = loc.get('mc_status_embed_online', locale).format_map({'online': status.players.online, 'slots': status.players.max})
    except:
        status_disp = loc.get('mc_status_embed_offline', locale)
    embed.add_field(name = loc.get('mc_status_embed_edition', locale), value = edition)
    embed.add_field(name = loc.get('mc_status_embed_ip', locale), value = ip)
    embed.add_field(name = loc.get('mc_status_embed_players', locale), value = status_disp)
    return embed

class init(commands.Cog):
    bot = discord.Bot()

    @tasks.loop(seconds = 10)
    async def updatestatus(self):
        await self.bot.wait_until_ready()

        for server in servers.select():
            embed = None
            ping = None
            try:
                ping = await ping_mc(server.IP, server.edition)
                server.version = ping.status().version.name
            except:
                server.online = False

            for item in legacy.select().where(legacy.IP == server.id, legacy.edition == server.edition):
                try:
                    if item.type == "update":
                            channel = self.bot.get_channel(item.ChannelID)
                            message = await channel.fetch_message(item.MessageID)
                            if embed is None: embed = await compile_embed(item.locale, ping, server.IP, server.edition, server.version)
                            await message.edit(content = "",embed = embed)
                    elif item.type == "notify":
                        if ping is not None:
                            if ping.status().players.online > 0 and server.online == False:
                                await self.bot.get_channel(item.ChannelID).send(content = loc.get('mc_notification', item.locale).format(role = item.role, edition = server.edition, ip = server.IP))
                                server.online = True
                except:
                    traceback.print_exc()
                    if self.bot.is_closed() == False:
                        item.delete_instance()
            server.save()

    def __init__(self, bot):
        self.bot = bot
        self.bot.add_cog(minecraft_commands(self.bot))
        self.updatestatus.start()
        print(loc.get('mc_ready'))


class minecraft_commands(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot, debug=False):
        self.bot = bot

    minecraft = discord.SlashCommandGroup("minecraft", loc.get('minecraft_desc'))
    @minecraft.command(description = loc.get('addserver_desc'))
    async def addserver(self, ctx, ip, edition = 'JAVA'):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale))
        message = await response.original_response()
        status = 'addserver_'

        if not (ctx.guild.me.guild_permissions.manage_webhooks or ctx.channel.permissions_for(ctx.guild.me).manage_webhooks):
            status = 'bot_denied'
        elif ctx.channel.permissions_for(ctx.author).manage_webhooks:
            edition = edition.upper()
            try:
                server = servers.get(servers.IP == ip, servers.edition == edition)
            except:
                server = servers.create(IP = ip, edition = edition, online = False, version = "Unknown")
            legacy.create(MessageID = message.id, type = "update", ChannelID = ctx.channel.id, IP = server.id, edition = edition, locale = locale)
            status += 'success'
        else:
            status = 'channel_denied'

        await message.edit(content=loc.get(status, locale).format_map({'permission': loc.get('manage_webhooks', locale)}))

    @minecraft.command(description = loc.get('setnotification_desc'))
    async def setnotification(self, ctx, ip, edition = 'JAVA', sub_role = ''):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale))
        message = await response.original_response()
        status = 'setnotification_'

        if not (ctx.guild.me.guild_permissions.manage_webhooks or ctx.channel.permissions_for(ctx.guild.me).manage_webhooks):
            status = 'bot_denied'
        elif ctx.channel.permissions_for(ctx.author).manage_webhooks:
            edition = edition.upper()
            try:
                server = servers.get(servers.IP == ip, servers.edition == edition)
            except:
                server = servers.create(IP = ip, edition = edition, online = False, version = "Unknown")
            try:
                legacy.get(legacy.type == "notify", legacy.ChannelID == ctx.channel.id, legacy.edition == edition, legacy.IP == server.id)
                status += 'fail'
            except:
                legacy.create(type = "notify", ChannelID = ctx.channel.id, edition = edition, IP = server.id, role = sub_role, locale = locale)
                status += 'success'
        else:
            status = 'channel_denied'
        await message.edit(content=loc.get(status, locale).format_map({'edition': edition[0][0], 'ip': ip, 'permission': loc.get('manage_webhooks', locale)}))

    @minecraft.command(description = loc.get('stopnotification_desc'))
    async def stopnotification(self, ctx, ip, edition = 'JAVA'):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale))
        message = await response.original_response()
        status = 'stopnotification_'

        if not (ctx.guild.me.guild_permissions.manage_webhooks or ctx.channel.permissions_for(ctx.guild.me).manage_webhooks):
            status = 'bot_denied'
        elif ctx.channel.permissions_for(ctx.author).manage_webhooks:
            edition = edition.upper()
            try:
                server = servers.get(servers.IP == ip, servers.edition == edition)
                legacy.get(legacy.type == "notify", legacy.ChannelID == ctx.channel.id, legacy.IP == server.id).delete_instance()
                status += 'success'
            except: status += 'fail'
        else:
            status = 'channel_denied'
        await message.edit(content=loc.get(status, locale).format_map({'permission': loc.get('manage_webhooks', locale)}))





