from discord.ext import commands
import sqlite3
from cogs.utils.db import add_user_to_db_or_pass, suggestion_exists_check
from cogs.utils.messages import update_banner, get_suggestion_name
from cogs.utils.misc import check_admin_rights
from contextlib import closing


class SuggestionsCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def suggest(self, ctx, *, data):
        """Adds a game suggestion"""
        user_id = ctx.author.id
        username = str(ctx.author.name)
        game = ' '.join(data.split())
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                add_user_to_db_or_pass(con, username, user_id)
            try:
                with con:
                    con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',
                                (user_id, game, 'game'))
                await update_banner(ctx, 'games')
                await ctx.send('{} suggested "{}" for stream'.format(username, game))
            except sqlite3.IntegrityError:
                await ctx.send('"{}" has already been suggested'.format(game))

    @commands.command(aliases=['movie_suggest'])
    async def suggest_movie(self, ctx, *, data):
        """Adds a movie suggestion"""
        user_id = ctx.author.id
        username = str(ctx.author.name)
        movie = ' '.join(data.split())
        with closing(sqlite3.connect(self.bot.db_name)) as con:
            with con:
                add_user_to_db_or_pass(con, username, user_id)
            try:
                with con:
                    con.execute('INSERT INTO Suggestions(user_id, suggestion, suggestion_type) VALUES(?, ?, ?);',
                                (user_id, movie, 'movie'))
                await update_banner(ctx, 'movies')
                await ctx.send('{} suggested "{}" for movie night'.format(username, movie))
            except sqlite3.IntegrityError:
                await ctx.send('"{}" has already been suggested'.format(movie))

    @commands.command()
    async def remove(self, ctx, *, data):
        """Removes the game suggestion if the game was suggested by the user issuing the command"""
        if await check_admin_rights(ctx):
            await self.adminremove(ctx, data)
        else:
            user_id = ctx.author.id
            username = str(ctx.author.name)
            game = await get_suggestion_name(ctx, 'game', data)
            if game:
                with closing(sqlite3.connect(self.bot.db_name)) as con:
                    with con:
                        con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
                        con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))
                    if suggestion_exists_check(self.bot.db_name, game, 'game', user_id):
                        with con:
                            con.execute(
                                'DELETE FROM Suggestions WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                (user_id, game, 'game'))
                        if not suggestion_exists_check(self.bot.db_name, game, 'game', user_id):
                            await update_banner(ctx, 'games')
                            await ctx.send('Successfully deleted "{}" from {}\'s game suggestions'.format(game, username))
                        else:
                            await ctx.send(
                                'Couldn\'t delete "{}" from {}\'s game suggestions, please contact Euqimor for troubleshooting'.format(
                                    game, username))
                    else:
                        await ctx.send('"{}" not found in {}\'s game suggestions'.format(game, username))
            else:
                await ctx.send(f'Couldn\'t find anything matching "{data}" in {username}\'s suggestions')

    @commands.command(aliases=['movie_remove'])
    async def remove_movie(self, ctx, *, data):
        """Removes the movie suggestion if the movie was suggested by the user issuing the command"""
        if await check_admin_rights(ctx):
            await self.adminremove_movie(ctx, data)
        else:
            user_id = ctx.author.id
            username = str(ctx.author.name)
            movie = await get_suggestion_name(ctx, 'movie', data)
            if movie:
                with closing(sqlite3.connect(self.bot.db_name)) as con:
                    with con:
                        con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
                        con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))
                    if suggestion_exists_check(self.bot.db_name, movie, 'movie', user_id):
                        with con:
                            con.execute(
                                'DELETE FROM Suggestions WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                (user_id, movie, 'movie'))
                        if not suggestion_exists_check(self.bot.db_name, movie, 'movie', user_id):
                            await update_banner(ctx, 'movies')
                            await ctx.send('Successfully deleted "{}" from {}\'s movie suggestions'.format(movie, username))
                        else:
                            await ctx.send(
                                'Couldn\'t delete "{}" from {}\'s movie suggestions, please contact Euqimor for troubleshooting'
                                .format(movie, username))
                    else:
                        await ctx.send('"{}" not found in {}\'s movie suggestions'.format(movie, username))
            else:
                await ctx.send(f'Couldn\'t find anything matching "{data}" in {username}\'s suggestions')

    async def adminremove(self, ctx, data):
        """Removes the game from any user's suggestions"""
        game = await get_suggestion_name(ctx, 'game', data)
        if game:
            if suggestion_exists_check(self.bot.db_name, game, 'game'):
                with closing(sqlite3.connect(self.bot.db_name)) as con:
                        with con:
                            con.execute('DELETE FROM Suggestions WHERE suggestion LIKE ? AND suggestion_type=?;',
                                        (game, 'game'))
                        if not suggestion_exists_check(self.bot.db_name, game, 'game'):
                            await update_banner(ctx, 'games')
                            await ctx.send('Successfully deleted "{}" from game suggestions'.format(game))
                        else:
                            await ctx.send(
                                'Couldn\'t delete "{}" from game suggestions, please contact Euqimor for troubleshooting'
                                .format(game))
            else:
                await ctx.send('"{}" not found in game suggestions'.format(game))
        else:
            await ctx.send(f'Couldn\'t find anything matching "{data}" in game suggestions')

    async def adminremove_movie(self, ctx, data):
        """Removes the movie from any user's suggestions"""
        movie = await get_suggestion_name(ctx, 'movie', data)
        if movie:
            if suggestion_exists_check(self.bot.db_name, movie, 'movie'):
                with closing(sqlite3.connect(self.bot.db_name)) as con:
                    with con:
                        con.execute('DELETE FROM Suggestions WHERE suggestion LIKE ? AND suggestion_type=?;',
                                    (movie, 'movie'))
                    if not suggestion_exists_check(self.bot.db_name, movie, 'movie'):
                        await update_banner(ctx, 'movies')
                        await ctx.send('Successfully deleted "{}" from movie suggestions'.format(movie))
                    else:
                        await ctx.send(
                            'Couldn\'t delete "{}" from movie suggestions, please contact Euqimor for troubleshooting'
                            .format(movie))
            else:
                await ctx.send('"{}" not found in movie suggestions'.format(movie))
        else:
            await ctx.send(f'Couldn\'t find anything matching "{data}" in movie suggestions')

    @commands.command()
    async def test(self, ctx):
        message = await ctx.send(':one: afdasf\n\n:two: aggag\n\n:three: asfasfa\n\n:four: afasfa')
        message.add_reaction(u'\u0031')


def setup(bot):
    bot.add_cog(SuggestionsCog(bot))
