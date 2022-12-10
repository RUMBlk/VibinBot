from minecraft import servers
import discord
from database import *
import traceback
import minecraft as mc
from discord.ext import tasks, commands
from datetime import datetime

class Bot(object):
    def __init__(self, bot, delay, bot_token, debug=False):
        @bot.event
        async def on_connect():
            for guild in bot.guilds:
                try:
                    guilds.get(guilds.GuildID == guild.id)
                except:
                    guilds.create(GuildID = guild.id)

        @bot.event
        async def on_guild_join(guild):
            try:
                guilds.get(guilds.GuildID == guild.id)
            except:
                guilds.create(GuildID = guild.id)


        @bot.event
        async def on_message(message):
            if message.author.bot is False:
                guild = guilds.get(GuildID = message.guild.id)
                try:
                    author = members.get(members.GuildID == guild.id, members.UserID == message.author.id)
                except:
                    author = members.create(GuildID = guild.id, UserID = message.author.id, msg_count = 0, points = 0)
                author.msg_count += 1
                author.points += 10
                charset = '`!@#$%^&*()-+*/,.<>;:[]{}\\|\'\" '
                print(message.content)
                for char in message.content:
                    if char in charset:
                        author.points += 10
                author.save()

        @tasks.loop(seconds = float(delay))
        async def updatestatus():
            for server in mc.servers:
                embed = None
                ping = None
                try:
                    ping = mc.ping_mc(server.IP, server.edition)
                    server.version = ping.status().version.name
                except:
                    server.online = False

                for item in mc.legacy.select().where(mc.legacy.IP == server.id, mc.legacy.edition == server.edition):
                    try:
                        if item.type == "update":
                                channel = bot.get_channel(item.ChannelID)
                                message = await channel.fetch_message(item.MessageID)
                                if embed is None: embed = await mc.compile_embed(ping, server.IP, server.edition, server.version)
                                await message.edit(content = "",embed = embed)
                        elif item.type == "notify":
                            if ping is not None:
                                if ping.status().players.online > 0 and server.online == False:
                                    await bot.get_channel(item.ChannelID).send(content = f"{item.role} [{server.edition}]{server.IP} server is up!")
                                    server.online = True
                    except:
                        if debug is True: traceback.print_exc()
                        if bot.is_closed() == False:
                            item.delete_instance()
                server.save()

        @updatestatus.before_loop
        async def before_updatestatus():
            print('The bot is preparing...')
            await bot.wait_until_ready()
            bot.add_cog(cmd(bot, debug))
            bot.add_cog(mc.mc_cmd(bot, debug))
            await bot.sync_commands()
            print('The bot is ready')

        updatestatus.start()
        bot.run(bot_token)
        pass

class cmd(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot, debug=False):
        self.bot = bot

    @bot.slash_command(description = "no desc")
    async def role_offset(self, ctx, role: discord.Role, claim = "ACTIVITY"):
        content = "smth went wrong temp text"
        try:
            adm_role = discord.utils.get(ctx.guild.roles, name="Vibin Admins")
            if adm_role in ctx.author.roles:
                guild = guilds.get(guilds.GuildID == ctx.guild.id)
                if claim.upper() == "ACTIVITY":
                    try:
                        query = role_tags.update(offset = role.id).where(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY")
                        query.execute()
                    except:
                        print("bruh")
                        role_tags.create(GuildID = guild.id, tag = "ACTIVITY", offset = role.id)
                    content = f"Now custom activity roles will be placed after {role.name} role"
                else:
                    content = "not done yet"
            else:
                content="lol nope"
        except: pass
        await ctx.respond(content)

    @bot.slash_command(description = "Claim a custom role if you're very active or boosted the server! claim options: ACTIVITY, BOOSTS")
    async def claimrole(self, ctx, name, color, claim='ACTIVITY'):
        response = await ctx.respond("Processing...")
        message = await response.original_response()
        content = "Sorry, only top-10 active members of the server can claim a custom role!"
        try:
            guild = guilds.get(guilds.GuildID == ctx.guild.id)
            i = 0
            for member in members.select().where(members.GuildID == guild.id).order_by(members.points.desc()):
                i += 1
                if ctx.author.id == member.UserID and i<=10:
                    if claim.upper() == "ACTIVITY":
                        try:
                            tag = role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY")
                        except:
                            tag = role_tags.create(GuildID = guild.id, tag = "ACTIVITY")
                        if backend.has_tag(ctx.author, tag).answer == False:
                            role = await ctx.guild.create_role(name=name, colour=discord.Colour(int(color[1:], 16)))
                            try:
                                offset = role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY").offset
                                if offset is not None:
                                    await role.edit(position=ctx.guild.get_role(offset).position-1)
                            except: traceback.print_exc()
                            await ctx.author.add_roles(role)
                            roles.create(RoleID = role.id, tag = tag.id)
                            content = "Here you go!"
                        else:
                            content = "Sorry, only one activity role per member"
                    break
        except:
            content = "Sorry, something went wrong processing your request."
            print("Couldn't respond to request!")
            traceback.print_exc()
        await message.edit(content)

    @bot.slash_command(description = "Delete a custom role if you don't want it or want to change it! claim options: ACTIVITY, BOOSTS")
    async def unclaimrole(self, ctx, claim='ACTIVITY'):
        try:
            guild = guilds.get(guilds.GuildID == ctx.guild.id)
            if claim.upper() == "ACTIVITY":
                try:
                    content = "You don't have an activity role to unclaim!"
                    tag = backend.has_tag(ctx.author, role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY"))
                    if tag.answer == True:
                        await ctx.guild.get_role(tag.role.id).delete()
                        tag.row.delete_instance()
                        content = "Here you go!"
                except: pass
            elif claim.upper() == "BOOSTS":
                content = "not done yet :/"
        except:
            content = "Role doesn't exists anymore"
        await ctx.respond(content)

    @bot.slash_command(description = "literally a leaderboard")
    async def leaderboard(self, ctx):
        content = "Counting messages..."

        embed = None
        response = await ctx.respond(content)
        message = await response.original_response()
        try:
            content = "Here you go:"
            guild = guilds.get(guilds.GuildID == ctx.guild.id)
            leaderboard = members.select().where(members.GuildID == guild.id).order_by(members.points.desc())
            place_field = ""
            user_field = ""
            points_field = ""
            i = 0
            for member in leaderboard:
                i += 1
                place_field += str(i) + "\n"
                UserID = await self.bot.fetch_user(member.UserID)
                user_field += UserID.display_name + "\n"
                points_field += str(member.points) + "\n"
            if i == 0:
                content = "The leaderboard is empty, please try later."
            else:
                embed = discord.Embed(
                    title = "{} leaderboard".format(ctx.guild.name),
                    timestamp = datetime.now()
                )
                embed.add_field(name = "No.", value = place_field)
                embed.add_field(name = "Members", value = user_field)
                embed.add_field(name = "Points", value = points_field)
        except:
            content = "Sorry, something went wrong processing your request."
            embed = None
            traceback.print_exc()
        await message.edit(content, embed=embed)

class backend():
    class has_tag():
        answer = False
        role = None
        row = None
        def __init__(self, user: discord.Member, tag):
            for role in user.roles:
                try:
                    row = roles.get(roles.RoleID == role.id)
                    if str(row.tag) == str(tag.id):
                        self.answer = True
                        self.role = role
                        self.row = row
                        break
                except: pass



