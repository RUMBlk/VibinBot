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
            bot.add_cog(cmd(bot, debug))
            bot.add_cog(mc.mc_cmd(bot, debug))
            await bot.sync_commands()

        @bot.event
        async def on_guild_join(guild):
            guilds.get_or_create(GuildID = guild.id)

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

        #async def leaderboard_update(guild, forced = False):
        #    lbUpdateDate = db.execute("SELECT * FROM guilds WHERE GuildID=?", [str(guild.id)]).fetchone()["lbUpdateDate"]
        #    if lbUpdateDate is None or forced or lbUpdateDate.replace(tzinfo=timezone.utc) < datetime.today().replace(day=1, tzinfo=timezone.utc):
        #        db.execute(f"UPDATE MEMBERS_{str(guild.id)} SET points=?", (0,))
        #        for channel in guild.channels:
        #            can_read=False
        #            try:
        #                async for message in channel.history(limit = 1):
        #                    can_read = True
        #            except:
        #                can_read = False
        #            if isinstance(channel, discord.channel.TextChannel) and can_read == True:
        #                print(channel.name)
        #                async for message in channel.history(limit = None):
        #                    if message.created_at.replace(tzinfo=timezone.utc) < datetime.today().replace(day=1, tzinfo=timezone.utc):
        #                        break;
        #                    if db.execute(f"SELECT * FROM MEMBERS_{str(guild.id)} WHERE UserID=?", [str(message.author.id)]).fetchone() is None:
        #                        db.execute(f"INSERT INTO MEMBERS_{str(guild.id)} (UserID, points) VALUES (?, ?)", (str(message.author.id), 0,))
        #                        #guild_members = db.execute("SELECT * FROM {}_MEMBERS").fetchall()

        #                    members = db.execute(f"SELECT * FROM MEMBERS_{str(guild.id)} ORDER BY points DESC").fetchall()
        #                    member = db.execute(f"SELECT * FROM MEMBERS_{str(guild.id)} WHERE UserID=?", [str(message.author.id)]).fetchone()
        #                    if not members.index(member) < 3 and member["aRoleID"] is not None:
        #                        await guild.get_role(int(member["aRoleID"])).delete()
        #                    db.execute(f"UPDATE MEMBERS_{str(guild.id)} SET aRoleID=? WHERE UserID=?", (member["aRoleID"], str(message.author.id),))

        #                    db.execute(
        #                        f"UPDATE MEMBERS_{str(guild.id)} SET points=? WHERE UserID=?",
        #                        (db.execute(f"SELECT * FROM MEMBERS_{str(guild.id)} WHERE UserID=?", [str(message.author.id)]).fetchone()["points"] + 1, str(message.author.id))
        #                    )
        #                    print(channel.name + " " + str(message.created_at))
        #        db.execute("UPDATE guilds SET lbUpdateDate=? WHERE GuildID=?", (datetime.today().replace(tzinfo=timezone.utc), str(guild.id),))
        #    if forced == True: print("Forced leaderboard recount has been finished!")

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
            print('The bot is ready')

        updatestatus.start()
        bot.run(bot_token)
        pass

class cmd(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot, debug=False):
        self.bot = bot

    #@bot.slash_command(description = "Debug command")
    #async def debug(self, ctx):
    #    db.save()

    #@slash_command(description = "pls don't ruin the database ;-;")
    #async def sql(ctx, to_execute: str, params=None):
    #    role = discord.utils.get(ctx.guild.roles, name="Vibin Admins")
    #    if role in ctx.author.roles:
    #        try:
    #            content=None
    #            if params is None: content = str(db.execute(to_execute).fetchall()).replace("),", "),\n")
    #            else:
    #                params = params.split("?")
    #                content =  str(db.execute(to_execute, tuple(params)).fetchall()).replace("),", "),\n")
    #            await ctx.respond(content)
    #        except:
    #            await ctx.respond("smth went wrong")
    #            traceback.print_exc()
    #    else:
    #        await ctx.respond("lol nope")

    #@bot.slash_command(description = "no desc")
    #async def role_offset(self, ctx, role: discord.Role, claim = "ACTIVITY"):
    #    adm_role = discord.utils.get(ctx.guild.roles, name="Vibin Admins")
    #    if adm_role in ctx.author.roles:
    #        if claim.upper() == "ACTIVITY":
    #            guilds.update().where(guilds.GuildID == ctx.guild.id)
    #            content = f"Now custom activity roles will be places after {role.name} role"
    #        else:
    #            content = "not done yet"
    #    else:
    #        content="lol nope"
    #    await ctx.respond(content)

    #@bot.slash_command(description = "Claim a custom role if you're very active or boosted the server! claim options: ACTIVITY, BOOSTS")
    #async def claimrole(self, ctx, name, color, claim='ACTIVITY'):
    #    try:
    #        guild = guilds.get(guilds.GuildID == ctx.guild.id)
    #        i = 0
    #        for member in members.select().where(members.GuildID == ctx.guild.id).order_by(members.points.desc()):
    #            i += 1
    #            if ctx.author.id == member.UserID:
    #                #members = db.execute(f"SELECT * FROM MEMBERS_{str(ctx.guild.id)} ORDER BY points DESC").fetchall()
    #                #member = db.execute(f"SELECT * FROM MEMBERS_{str(ctx.guild.id)} WHERE UserID=?", [str(ctx.author.id)]).fetchone()
    #                if claim.upper() == "ACTIVITY":
    #                    role = await ctx.guild.create_role(name=name, colour=discord.Colour(int(color[1:], 16)))
    #                    if guild["aRoleID"] is not None:
    #                        await role.edit(position=ctx.guild.get_role(int(guild["aRoleID"])).position-1)
    #                    await ctx.author.add_roles(role)
    #                    db.execute(f"UPDATE MEMBERS_{str(ctx.guild.id)} SET aRoleID=? WHERE UserID=?", (str(role.id), str(ctx.author.id),))
    #                    content = "Here you go!"
    #                elif claim.upper() == "ACTIVITY":
    #                    content = "Sorry, only one activity role per member"
    #                elif claim.upper() == "BOOSTS":
    #                    content = "not done yet :/"
    #                break
    #            elif i > 10:
    #                content = "Sorry, only top-10 active members of the server can claim a custom role!"
    #                break
    #    except:
    #        content = "Sorry, something went wrong processing your request."
    #        print("Couldn't respond to request!")
    #        traceback.print_exc()
    #    await ctx.respond(content)

    #@bot.slash_command(description = "Delete a custom role if you don't want it or want to change it! claim options: ACTIVITY, BOOSTS")
    #async def unclaimrole(self, ctx, claim='ACTIVITY'):
    #    try:
    #        member = members.get(members.UserID == ctx.author.id)
    #        if claim.upper() == "ACTIVITY":
    #            #db.execute(f"UPDATE MEMBERS_{str(ctx.guild.id)} SET aRoleID=? WHERE UserID=?", (None, str(ctx.author.id),))
    #            #await ctx.guild.get_role(int(role)).delete()
    #            content = "Here you go!"
    #        elif claim.upper() == "ACTIVITY":
    #            content = "You don't have an activity role to unclaim!"
    #        elif claim.upper() == "BOOSTS":
    #            content = "not done yet :/"
    #    except:
    #        content = "Role doesn't exists"
    #    await ctx.respond(content)

    @bot.slash_command(description = "literally a leaderboard")
    async def leaderboard(self, ctx):
        content = "Counting messages..."

        embed = None
        response = await ctx.respond(content)
        message = await response.original_response()
        try:
            content = "Here you go:"
            embed = discord.Embed(
                title = "{} leaderboard list".format(ctx.guild.name),
                timestamp = datetime.now()
                )
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
            embed.add_field(name = "No.", value = place_field)
            embed.add_field(name = "Members", value = user_field)
            embed.add_field(name = "Points", value = points_field)
        except:
            content = "Sorry, something went wrong processing your request."
            embed = None
            traceback.print_exc()
        await message.edit(content, embed=embed)




