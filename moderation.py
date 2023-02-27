import discord
import traceback
from discord.ext import tasks, commands
from datetime import datetime as dt
from datetime import date
import database as db
import localisation as loc

class moderation(commands.Cog):
    bot = discord.Bot()
    def __init__(self, bot):
        self.bot = bot

    moderation = discord.SlashCommandGroup("moderation", loc.get('moderation_desc'))

    @moderation.command(description = loc.get('reports_channel_desc'))
    async def channel(self, ctx):
        if db.is_closed(): db.connect()
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale))
        message = await response.original_response()
        status = 'reports_channel_'
        try:
            if ctx.channel.permissions_for(ctx.guild.me).send_messages:
                query = db.guilds.update(reports_channel = ctx.channel.id).where(db.guilds.GuildID == ctx.guild.id)
                query.execute()
                status += 'success'
            else:
                status = 'bot_denied'
        except:
            traceback.print_exc()
            status = 'exception'
        await message.edit(content=loc.get(status, guild.locale).format_map({'permission': loc.get('manage_roles', guild.locale)}))

    @bot.message_command(name=loc.get('context_report'))
    async def report(self, ctx, message: discord.Message):
        if db.is_closed(): db.connect()
        guild = db.guilds.get(db.guilds.GuildID == ctx.guild.id)
        response = await ctx.respond(content = loc.get('processing', guild.locale), ephemeral = True)
        response = await response.original_response()
        status = 'report_'
        try:
            attachments = 'None'
            for item in message.attachments:
                if attachments == 'None':
                    attachments = ''
                attachments += f'{item.url}\n'

            loc_map = {'author': message.author.mention, 'jump_url': message.jump_url, 'posted_at': int(message.created_at.timestamp()), 'reported_content': message.content, 'attachments': attachments}

            reported_content = loc.get(f'{status}message_head', guild.locale).format_map(loc_map)
            if message.content != '': reported_content += loc.get(f'{status}message_content', guild.locale).format_map(loc_map)
            if message.attachments: reported_content += loc.get(f'{status}message_attach', guild.locale).format_map(loc_map)
            if message.embeds: reported_content += loc.get(f'{status}message_embeds', guild.locale).format_map(loc_map)

            channel = await self.bot.fetch_channel(guild.reports_channel)
            to_react = await channel.send(content = reported_content, embeds = message.embeds)
            await to_react.add_reaction('✅')
            #await channel.send(content=loc.get(f'{status}report', guild.locale).format_map({'author_id': message.author.id, 'reported_content': message.content}))
            status += 'success'
        except: 
            status = 'exception'
            traceback.print_exc()
        await response.edit(content = loc.get(status, guild.locale))

