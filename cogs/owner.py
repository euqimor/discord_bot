import discord
import sqlite3
import sys
import traceback
from io import StringIO
from textwrap import indent
from contextlib import closing, redirect_stdout
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

    @commands.command(hidden=True, name='exec')
    async def _exec(self, ctx, *, code):
        """
         Executes code presented in a code block of the following format:
         ```py
         ```
        """
        code = code[6:-3]
        if code != '':
            success_flag = '✅'
            failure_flag = '❌'
            temp_out = StringIO()

            env = {
                'ctx': ctx,
                'bot': self.bot
            }
            to_compile = f"def func():\n{indent(code, '  ')}"
            try:
                exec(to_compile, env)
            except Exception as e:
                await ctx.message.add_reaction(failure_flag)
                with redirect_stdout(temp_out):
                    print(f"```py\n{e.__class__.__name__}: {e}\n```")

            func = env['func']
            try:
                with redirect_stdout(temp_out):
                    ret = await func()
            except Exception as e:
                await ctx.message.add_reaction(failure_flag)
                with redirect_stdout(temp_out):
                    print(f"```py\n{e.__class__.__name__}: {e}\n```")
            else:
                value = temp_out.getvalue()
                await ctx.message.add_reaction(success_flag)
                if ret is None:
                    await ctx.send(f"```py\n{value}\n```")
                else:
                    await ctx.send(f'```py\n{value}{ret}\n```')
        else:
            await ctx.send("The command must be in a code block")


def setup(bot):
    bot.add_cog(OwnerCog(bot))
