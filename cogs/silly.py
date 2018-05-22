from discord.ext import commands
from random import randint
from contextlib import closing
import sqlite3
import aiohttp
from io import BytesIO
from discord import File, Embed


class SillyCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def wisdom(self, ctx, *, word_or_phrase=''):
        """
        Inspirational words of wisdom
        Add one or more words after the command to try and search for a proverb with the given word or phrase
        Get a random proverb if the words weren't provided or found
        """
        line = ''
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            if word_or_phrase:
                word_or_phrase = '%{}%'.format(word_or_phrase.strip())
                with con:
                    line = con.execute('SELECT proverb FROM Proverbs WHERE proverb LIKE ?',
                                       (word_or_phrase,)).fetchone()
            if line:
                line = line[0]
            else:
                with con:
                    max_id = con.execute('SELECT MAX(ROWID) FROM Proverbs;').fetchone()[0]
                    _id = randint(1, max_id)
                    line = con.execute('SELECT proverb FROM Proverbs WHERE ROWID=?', (_id,)).fetchone()[0]
        emoji = ''
        try:
            for item in ctx.guild.emojis:
                if item.name == 'praisegold' or item.name == 'praise_golden':
                    emoji = item
                    break
        except:
            pass
        await ctx.send('{} {}'.format(line, emoji))

    @wisdom.command()
    async def use(self, ctx, *, word_or_phrase=''):
        """
        Replaces "The Dark Souls" with supplied word or phrase
        """
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                max_id = con.execute('SELECT MAX(ROWID) FROM Proverbs;').fetchone()[0]
                _id = randint(1, max_id)
                line = con.execute('SELECT proverb FROM Proverbs WHERE ROWID=?', (_id,)).fetchone()[0]
        line = line.replace('The Dark Souls', word_or_phrase)
        emoji = ''
        try:
            roll = randint(1, 100)
            if roll <= 20:
                for item in ctx.guild.emojis:
                    if item.name == 'praisegold' or item.name == 'praise_golden':
                        emoji = item
                        break
            elif 20 < roll <= 60:
                for item in ctx.guild.emojis:
                    if item.name == 'thonk':
                        emoji = item
                        break
            else:
                roll_emoji = randint(0, len(ctx.guild.emojis))
                emoji = ctx.guild.emojis[roll_emoji]
        except:
            pass
        await ctx.send('{} {}'.format(line, emoji))

    @commands.command()
    async def cat(self, ctx):
        """
        Cat.
        Posts a random cat pic.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get('https://cataas.com/cat') as resp:
                cat_bytes = BytesIO(await resp.read())
        cat_file = File(cat_bytes, 'cat.png')
        e = Embed()
        e.set_image(url="attachment://cat.png")
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(SillyCog(bot))
