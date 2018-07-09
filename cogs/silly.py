from discord.ext import commands
from random import randint
from contextlib import closing
import sqlite3
import aiohttp
from io import BytesIO
from discord import File, Embed, Colour
from random import choice


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
                img_type = resp.headers['content-type'][6:]
                cat_bytes = BytesIO(await resp.read())
                filename = f'cat.{img_type}'
        cat_file = File(cat_bytes, filename)
        # e = Embed()
        # e.colour = Colour.from_rgb(206, 24, 188)
        # e.title = 'Das a cat.'
        # e.set_image(url=f"attachment://{filename}")
        await ctx.send(file=cat_file)

    @commands.command()
    async def choose(self, ctx, *options: commands.clean_content):
        """
        Chooses one of the options for you.
        Use quotes for options consisting of multiple words.
        """
        answer = choice(options)
        await ctx.send(answer)
    
    @commands.command(name='8ball')
    async def ball(self, ctx):
        """
        Ask the 8ball a question.
        """
        options = [
            "Signs point to yes.",
            "Yes.",
            "Reply hazy, try again.",
            "Without a doubt.",
            "My sources say no.",
            "As I see it, yes.",
            "You may rely on it.",
            "Concentrate and ask again.",
            "Outlook not so good.",
            "It is decidedly so.",
            "Very doubtful.",
            "Yes - definitely.",
            "It is certain.",
            "Cannot predict now.",
            "Most likely.",
            "Ask again later.",
            "My reply is no.",
            "Outlook good.",
            "Don't count on it.",
            "Definitely not.",
            "I have my doubts.",
            "Outlook so so.",
            "Who knows?",
            "Are you kidding?",
            "Don't bet on it.",
            "Forget about it.",
            ]
        answer = choice(options)
        await ctx.channel.send(answer)


def setup(bot):
    bot.add_cog(SillyCog(bot))
