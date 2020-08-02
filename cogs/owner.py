import discord
import sqlite3
import sys
import os
import re
import traceback
import aiohttp
from asyncio import TimeoutError
from io import StringIO
from textwrap import indent
from contextlib import closing, redirect_stdout
from discord.ext import commands
from cogs.utils.messages import update_banner


class OwnerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

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
            env.update(globals())
            to_compile = f"async def func():\n{indent(code, '  ')}"
            try:
                exec(to_compile, env)
            except Exception as e:
                await ctx.message.add_reaction(failure_flag)
                return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

            func = env['func']
            try:
                with redirect_stdout(temp_out):
                    ret = await func()
            except Exception as e:
                await ctx.message.add_reaction(failure_flag)
                await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")
            else:
                value = temp_out.getvalue()
                await ctx.message.add_reaction(success_flag)
                if ret is None and value:
                    await ctx.send(f"```py\n{value}\n```")
                elif ret:
                    await ctx.send(f'```py\n{value}{ret}\n```')
        else:
            await ctx.send("The command must be in a code block")

    @commands.command(hidden=True, name='reload')
    async def _reload(self, ctx, *, module):
        """Reloads a module"""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.message.add_reaction('✅')

    @commands.command(hidden=True)
    async def upload(self, ctx, filename: str = None):
        """Uploads a file"""
        def check(reaction, user):
            if user.id == ctx.message.author.id and str(reaction.emoji) in ['✅', '❌']:
                return True
        try:
            attachment = ctx.message.attachments[0]
        except IndexError:
            await ctx.send('No attachment found', delete_after=15)
            return
        base_path = os.path.dirname(os.path.realpath(__file__))
        url = attachment.url
        if filename is None:
            filename = [attachment.filename]
        elif '/' or '\\' in filename:
            filename = re.split(r'[/\\]', filename)
        dest_full_path = os.path.join(base_path, *filename)
        reaction_msg = await ctx.send(f'Uploading {dest_full_path}\n✅ - OK | ❌ - Cancel')
        for reaction in ['✅', '❌']:
            await reaction_msg.add_reaction(reaction)
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except TimeoutError:
            await ctx.send(f'Timeout, aborting.', delete_after=10)
            await reaction_msg.delete()
            await ctx.message.delete()
            return
        try:
            await reaction_msg.clear_reactions()
        except discord.Forbidden:
            pass
        try:
            dest_dir = os.path.dirname(dest_full_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    content = await resp.read()
            with open(dest_full_path, 'wb') as f:
                f.write(content)
            await ctx.send(f'✅ Uploaded {filename[-1]}')
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        finally:
            await reaction_msg.delete()
            await ctx.message.delete()

    @commands.command(hidden=True)
    async def test(self, ctx):
        num_emoji = {1:'1\u20e3', 2:'2\u20e3', 3:'3\u20e3', 4:'4\u20e3',
                     5:'5\u20e3', 6:'6\u20e3', 7:'7\u20e3', 8:'8\u20e3', 9:'9\u20e3', 10:'\U0001f51f'}
        message = await ctx.send(':one: afdasf\n\n:two: aggag\n\n:three: asfasfa\n\n:four: afasfa')
        for key in num_emoji:
            await message.add_reaction(num_emoji[key])

def setup(bot):
    bot.add_cog(OwnerCog(bot))
