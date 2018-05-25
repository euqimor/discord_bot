import discord
import sqlite3
import sys
import traceback
from io import StringIO
from contextlib import closing
from discord.ext import commands
from cogs.utils.messages import update_banner


class OwnerCog:
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def status(self, ctx, user: discord.Member):
        if user.activity:
            await ctx.send(f'{user.name} is {user.activity.type.name}')
        else:
            await ctx.send(f'{user.name}: no activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    async def mystatus(self, ctx):
        user = ctx.message.author
        await ctx.send(user.activity.type.name) if user.activity else await ctx.send('No activity')

    @commands.command(hidden=True)
    @commands.guild_only()
    async def stream(self, ctx):
        await self.bot.change_presence(activity=discord.Streaming(name="test", url="https://www.twitch.tv/123"))

    @commands.command()
    @commands.guild_only()
    async def wipe_user(self, ctx, user_id: str):
        """Purges the user and all related content from the database, command available only to Admin role"""
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

    @commands.command()
    async def set_prefix(self, ctx, message: str):
        prefix = message.strip()
        ctx.bot.command_prefix = prefix
        await ctx.send('The prefix is set to ' + str(ctx.bot.command_prefix))

    @commands.command(aliases=['set_nickname'])
    async def set_nick(self, ctx, *, message: str = ''):
        nickname = message.strip()
        bot_member = [x for x in ctx.bot.get_all_members() if x.bot and x.id == ctx.bot.user.id][0]
        await bot_member.edit(nick=nickname)
        await ctx.send('Nickname set')

    @commands.command(aliases=['set_playing'])
    async def set_status(self, ctx, *, message: str = ''):
        status = message.strip()
        await ctx.bot.change_presence(activity=discord.Game(status))
        await ctx.send('Status set')

    @commands.command(hidden=True)
    async def exec(self, ctx, *, code):
        """
         Executes code presented in a code block of the following format:
         ```py
         ```
        """
        code = code[6:-3]
        success_flag = 'U2714'
        failure_flag = 'U274C'
        base_out = sys.stdout
        temp_out = StringIO()
        try:
            sys.stdout = temp_out
            exec(code, globals(), locals())
            ctx.message.add_reaction(success_flag)
            await ctx.send(f"```py\n{temp_out.getvalue()}\n```")
        except:
            ctx.message.add_reaction(failure_flag)
            traceback.print_exc(file=temp_out, chain=False)
            await ctx.send(f"```py\n{temp_out.getvalue()}\n```")
        finally:
            sys.stdout = base_out


def setup(bot):
    bot.add_cog(OwnerCog(bot))
