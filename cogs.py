import asyncio
import discord
import traceback
from discord.ext import tasks, commands
from datetime import datetime as dt
from datetime import date
from database import *
import localisation as loc

class Intents(discord.Intents):
    pass

class events(commands.Cog):
    bot = discord.Bot()

    @commands.Cog.listener("on_ready")
    async def on_startup(self):
        config = None
        try:
            config = internal.get(internal.id == 1)
        except:
            config = internal.create()

        today = date.today()

        if today > config.last_reset:
            try:
                query = roles.select().where(roles.expires != None, roles.expires >= today)
                for role in query:
                    guild = guilds.get(guilds.id == role.GuildID)
                    ds_role = await self.bot.get_guild(guild.GuildID).get_role(role.RoleID)
                    ds_role.delete()
                    role.delete_instance()
            except: pass

        if today.month > config.last_reset.month:
            try:
                try:
                    await backend.elections(self.bot)
                except: pass

                await backend.reset(self.bot)
            except: pass

        config.last_reset = date.today()
        config.save()

        for guild in self.bot.guilds:
            print("sdfs")
            guild_db = None
            try:
                guild_db = guilds.get(guilds.GuildID == guild.id)
            except:
                guild_db = guilds.create(GuildID = guild.id)

            for member in guild.members:
                if member.bot is False:
                    try:
                        members.get(members.GuildID == guild_db.id, members.UserID == member.id)
                    except: 
                        members.create(GuildID = guild_db.id, UserID = member.id, msg_count = 0, points = 0)

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
            try:
                author = members.get(members.GuildID == guild.id, members.UserID == message.author.id)
            except:
                author = members.create(GuildID = guild.id, UserID = message.author.id, msg_count = 0, points = 0)
            author.msg_count += 1
            author.points += 10
            charset = '`!@#$%^&*()-+*/,.<>;:[]{}\\|\'\"'
            for char in charset:
                author.points += message.content.count(f'{char} ') * 10
            author.save()

class society(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot):
        self.bot = bot

    admin = discord.SlashCommandGroup("admin", loc.get('admin_desc'))

    @admin.command(description = loc.get('admin_role_desc'))
    async def role(self, ctx, role: discord.Role):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale))
        message = await response.original_response()
        status = 'admin_role_'
        try:
            if not (ctx.guild.me.guild_permissions.manage_roles or ctx.channel.permissions_for(ctx.guild.me).manage_roles):
                status = 'bot_denied'
            elif ctx.channel.permissions_for(ctx.author).manage_roles:
                    try:
                        role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ADMIN")
                        query = role_tags.update(original = role.id).where(role_tags.GuildID == guild.id, role_tags.tag == "ADMIN")
                        query.execute()
                    except:
                        role_tags.create(GuildID = guild.id, tag = "ADMIN", original = role.id)
                    status += 'success'
            else:
                status = 'channel_denied'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, locale).format_map({'role_name': role.name, 'permission': loc.get('manage_roles', locale)}))


    @admin.command(description = loc.get('admin_apply_desc'))
    async def apply(self, ctx):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale))
        message = await response.original_response()
        status = 'admin_apply_'

        try:
            if not (ctx.guild.me.guild_permissions.administrator or ctx.channel.permissions_for(ctx.guild.me).administrator):
                status = 'bot_denied'
            else:
                try:
                    member = members.get(members.GuildID == guild.id, members.UserID == ctx.author.id)
                    place = backend.leaderboard_place(guild.id, ctx.author.id)
                    if place <= 10:
                        try:
                            candidates.get(candidates.GuildID == guild.id, candidates.UserID == member.id)
                            status += 'fail'
                        except:
                            candidates.create(GuildID = guild.id, UserID = member.id)
                            status += 'success'
                    else: status += 'not_active'
                except: status = 'author_not_found'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, locale).format_map({'permission': loc.get('administrator', locale)}))

    @admin.command(description = loc.get('admin_apply_desc'))
    async def vote(self, ctx, member: discord.Member):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale), ephemeral = True)
        message = await response.original_response()
        status = 'admin_vote_'

        try:
            if not (ctx.guild.me.guild_permissions.administrator or ctx.channel.permissions_for(ctx.guild.me).administrator):
                status = 'bot_denied'
            else:
                try:
                    author = members.get(members.GuildID == guild.id, members.UserID == ctx.author.id)
                    member_db = members.get(members.GuildID == guild.id, members.UserID == member.id)
                    try:
                        candidate = candidates.get(candidates.GuildID == guild.id, candidates.UserID == member_db.id)
                        try:
                            votes.get(votes.UserID == author.id, votes.candidate == candidate.id)
                            status += 'alr_voted'
                        except:
                            votes.create(UserID = author.id, candidate = candidate.id)
                            status += 'success'
                    except: status += 'not_candidate'
                except: status = "author_not_found"
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, locale).format_map({'permission': loc.get('administrator', locale), 'candidate': member}))

class commands(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot):
        self.bot = bot

    role_config = discord.SlashCommandGroup("role", loc.get('role_desc'))
    @role_config.command(description = loc.get('activity_desc'))
    async def activity(self, ctx, offset_role: discord.Role):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(content = loc.get('processing', locale))
        message = await response.original_response()
        status = 'role_offset_'
        try:
            if not (ctx.guild.me.guild_permissions.manage_roles or ctx.channel.permissions_for(ctx.guild.me).manage_roles):
                status = 'bot_denied'
            elif ctx.channel.permissions_for(ctx.author).manage_roles:
                    try:
                        role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY")
                        query = role_tags.update(original = offset_role.id).where(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY")
                        query.execute()
                    except:
                        role_tags.create(GuildID = guild.id, tag = "ACTIVITY", original = offset_role.id)
                    status += 'success'
            else:
                status = 'channel_denied'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, locale).format_map({'role_name': offset_role.name, 'permission': loc.get('manage_roles', locale)}))

    claimrole = discord.SlashCommandGroup("claimrole", loc.get('claimrole_desc'))
    @claimrole.command(description = loc.get('claimrole_desc'))
    async def activity(self, ctx, name, color):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(loc.get('processing', locale))
        message = await response.original_response()
        status = 'claimrole_'
        try:
            i = 0
            for member in members.select().where(members.GuildID == guild.id).order_by(members.points.desc()):
                i += 1
                if ctx.author.id == member.UserID and i<=10:
                    try:
                        tag = role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY")
                    except:
                        tag = role_tags.create(GuildID = guild.id, tag = "ACTIVITY")
                    if backend.has_tag(ctx.author, tag).answer == False:
                        role = await ctx.guild.create_role(name=name, colour=discord.Colour(int(color[1:], 16)))
                        try:
                            offset = role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY").original
                            if offset is not None:
                                await role.edit(position=ctx.guild.get_role(offset).position-1)
                        except: pass
                        await ctx.author.add_roles(role)
                        roles.create(GuildID = guild.id, RoleID = role.id, tag = tag.id)
                        status += 'a_success'
                    else:
                        status += 'a_fail'
                else:
                    status += 'a_!top'
                    break
            if i == 0:
                status = 'leaderboard_empty'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content = loc.get(status, locale))


    unclaimrole = discord.SlashCommandGroup("unclaimrole", loc.get('unclaimrole_desc'))
    @unclaimrole.command(description = loc.get('unclaimrole_desc'))
    async def activity(self, ctx):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        response = await ctx.respond(loc.get('processing', locale))
        message = await response.original_response()
        status = 'unclaimrole_'
        try:
            tag = backend.has_tag(ctx.author, role_tags.get(role_tags.GuildID == guild.id, role_tags.tag == "ACTIVITY"))
            if tag.answer == True:
                await ctx.guild.get_role(tag.role.id).delete()
                tag.row.delete_instance()
                status += 'a_success'
        except: 
            status += 'a_fail'
        await message.edit(loc.get(status, locale))

    @bot.slash_command(description = loc.get('leaderboard_desc'))
    async def leaderboard(self, ctx, ephemeral: bool):
        guild = guilds.get(guilds.GuildID == ctx.guild.id)
        locale = guild.locale
        embed = None
        response = await ctx.respond(content = loc.get('leaderboard_proc', locale), ephemeral = ephemeral)
        message = await response.original_response()
        status = 'leaderboard_'
        try:
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
                embed = discord.Embed(
                    title = loc.get('leaderboard_embed_title', locale).format_map({'guild': ctx.guild.name}),
                    timestamp = dt.now()
                )
                embed.add_field(name = loc.get('leaderboard_embed_place', locale), value = place_field)
                embed.add_field(name = loc.get('leaderboard_embed_members', locale), value = user_field)
                embed.add_field(name = loc.get('leaderboard_embed_points', locale), value = points_field)
                if i == 10: break
            if i == 0:
                status += 'empty'
            else:
                status += 'success'
        except:
            traceback.print_exc()
            status = 'exception'
            embed = None
        await message.edit(content = loc.get(status, locale), embed=embed)

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

    def leaderboard_place(guild_db_id, member_id):
        leaderboard = leaderboard = members.select().where(members.GuildID == guild_db_id).order_by(members.points.desc())
        place = 0
        for member in leaderboard:
            place += 1
            if member.UserID == member_id: return place

    async def elections(bot):
        guilds_db = guilds.select()

        for guild_db in guilds_db:
            guild = bot.get_guild(guild_db.GuildID)
            if guild.me.guild_permissions.administrator:
                cands = candidates.select().where(candidates.GuildID == guild_db.id)
                new_admin = {'id': None, 'votes': None}
                for candidate in cands:
                    vots = votes.select().where(votes.candidate == candidate.id).count()
                    if new_admin['votes'] is None or vots > new_admin['votes']:
                        cand_member = members.select().where(members.id == candidate.UserID).get()
                        new_admin = {'id': cand_member.UserID, 'votes': vots}
                try:
                    admin_tag = role_tags.get(role_tags.GuildID == guild_db.id, role_tags.tag == "ADMIN")
                    admin_role = guild.get_role(admin_tag.original)
                    try:
                        guild_members = await guild.fetch_members(limit=None)
                        for member in guild_members:
                            member.remove_roles(admin_role)
                    except: pass
                    admin_member = await guild.fetch_member(new_admin['id'])
                    await admin_member.add_roles(admin_role)
                    if guild.system_channel:
                        await guild.system_channel.send(loc.get('admin_congrats', guild_db.locale).format_map({'new_admin_id': admin_member.id}))
                except: pass
    async def reset(bot):
        try:
            tags = role_tags.select().where(role_tags.tag == "ACTIVITY")
            for tag in tags:
                query = roles.select().where(roles.tag == tag.id)
                for role in query:
                    guild_db = guilds.get(guilds.id == role.GuildID)
                    guild = bot.get_guild(guild_db.GuildID)
                    ds_role = guild.get_role(role.RoleID)
                    await ds_role.delete()
                    role.delete_instance()
            members.update(points = 0).where(members.points != 0).execute()
            candidates.delete().execute()
            votes.delete().execute()
        except: traceback.print_exc()






