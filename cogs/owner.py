import discord
import sqlite3
from contextlib import closing
from discord.ext import commands
from cogs.utils.misc import check_admin_rights
from cogs.utils.messages import update_banner, rejections
from random import choice as random_choice


class OwnerCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def status(self, ctx, user: discord.Member):
        if user.activity:
            await ctx.send(f'{user.name} is {user.activity.type.name}')
        else:
            await ctx.send(f'{user.name}: no activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def mystatus(self, ctx):
        user = ctx.message.author
        await ctx.send(user.activity.type.name) if user.activity else await ctx.send('No activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def stream(self, ctx):
        await self.bot.change_presence(activity=discord.Streaming(name="test", url="https://www.twitch.tv/123"))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def wipe_user(self, ctx, user_id: str):
        """Purges the user and all related content from the database, command available only to Admin role"""
        if await check_admin_rights(ctx):
            user_id = user_id.strip('<@>')
            with closing(sqlite3.connect(self.bot.db_name)) as con:
                with con:
                    exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;', (user_id,)).fetchall()
                if exists:
                    username = exists[0][0]
                    with con:
                        con.execute('PRAGMA FOREIGN_KEYS=ON;')
                        con.execute('DELETE FROM Users WHERE user_id=?;', (user_id,))
                        exists = con.execute('SELECT username FROM Users WHERE user_id=? LIMIT 1;',
                                             (user_id,)).fetchall()
                    if not exists:
                        await update_banner(ctx, 'movies')
                        await update_banner(ctx, 'games')
                        await ctx.send('Successfully deleted user {} from the database'.format(username))
                    else:
                        await ctx.send('Couldn\'t delete the user, please contact Euqimor for troubleshooting')
                else:
                    await ctx.send('User not found in the database')
        else:
            await ctx.send(random_choice(rejections))

    @commands.command()
    @commands.is_owner()
    async def set_prefix(self, ctx, message: str):  # TODO save permanently
        prefix = message.strip()
        if await check_admin_rights(ctx):
            ctx.bot.command_prefix = prefix
            await ctx.send('The prefix is set to ' + str(ctx.bot.command_prefix))
        else:
            await ctx.send(random_choice(rejections))

    @commands.command(aliases=['set_nickname'])
    @commands.is_owner()
    async def set_nick(self, ctx, *, message: str = ''):
        nickname = message.strip()
        if await check_admin_rights(ctx):
            bot_member = [x for x in ctx.bot.get_all_members() if x.bot and x.id == ctx.bot.user.id][0]
            await bot_member.edit(nick=nickname)
            await ctx.send('Nickname set')
        else:
            await ctx.send(random_choice(rejections))

    @commands.command(aliases=['set_playing'])
    @commands.is_owner()
    async def set_status(self, ctx, *, message: str = ''):  # TODO save permanently?
        status = message.strip()
        if await check_admin_rights(ctx):
            await ctx.bot.change_presence(activity=discord.Game(status))
            await ctx.send('Status set')
        else:
            await ctx.send(random_choice(rejections))


def setup(bot):
    bot.add_cog(OwnerCog(bot))
