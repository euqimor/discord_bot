import discord
import sqlite3
from contextlib import closing
from collections import defaultdict


rejections = ['Nope', 'Nu-uh', 'You are not my supervisor!', 'Sorry, you are not important enough to do that -_-',
              'Stop trying that, or I\'ll report you to Nightmom!', 'Yeah, right.']


async def update_banner(ctx, banner_type):
    def suggestions_exist(suggestion_type):
        with closing(sqlite3.connect(ctx.bot.db_name)) as con:
            with con:
                if con.execute('SELECT * FROM Suggestions WHERE suggestion_type=? LIMIT 1;', (suggestion_type,)).fetchall():
                    return True
        return False

    guild = ctx.guild
    channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
    message_list = []
    async for message in channel.history(limit=100):
        if message.author.id == ctx.bot.user.id:
            message_list.append(message)
    if message_list:
        if banner_type == 'games' and suggestions_exist('game'):
            e = embed_suggestions_in_category(ctx, 'game')
            author_pic_url = 'https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
            e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
            e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
            await message_list[2].edit(embed=e)
            await message_list[1].edit(embed=embed_games_by_author(ctx))
        elif banner_type == 'movies' and suggestions_exist('movie'):
            e = embed_suggestions_in_category(ctx, 'movie')
            e.colour = discord.Colour.orange()
            e.set_thumbnail(url='https://lh3.googleusercontent.com/TAzWe4fpDp8T7od9EoLTj4zJLV6EJQwBZjJ4mVjyzmKNzd5mVMdLU3k8J7XvErqsg59X2i71SQ=w50-h50-e365')
            await message_list[0].edit(embed=e)
        else:
            for message in message_list:
                message.delete()
    else:
        if suggestions_exist('game') or suggestions_exist('movie'):
            e = embed_suggestions_in_category(ctx, 'game')
            author_pic_url = 'https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
            e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
            e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
            await channel.send(embed=e)
            await channel.send(embed=embed_games_by_author(ctx))
            e = embed_suggestions_in_category(ctx, 'movie')
            e.colour = discord.Colour.orange()
            e.set_thumbnail(url='https://lh3.googleusercontent.com/TAzWe4fpDp8T7od9EoLTj4zJLV6EJQwBZjJ4mVjyzmKNzd5mVMdLU3k8J7XvErqsg59X2i71SQ=w50-h50-e365')
            await channel.send(embed=e)


def message_games_by_author(ctx):
    with closing(sqlite3.connect(ctx.bot.db_name)) as con:
        with con:
            suggestions = con.execute('SELECT username, suggestion \
                                        FROM Users NATURAL JOIN \
                                        (SELECT * FROM Suggestions WHERE suggestion_type="game") Q;').fetchall()
        if suggestions:
            message = '__**SUGGESTIONS BY AUTHOR**__\n\n'
            suggestions_dict = defaultdict(list)
            for username, game in suggestions:
                suggestions_dict[username].append(game)
            for username in suggestions_dict:
                message += '**{}:**\n```'.format(username)
                for game in suggestions_dict[username]:
                    message += '\n{}'.format(game)
                message += '```'
        else:
            message = '__**SUGGESTIONS BY AUTHOR**__\n\nNothing has been suggested yet'
        return message


def embed_games_by_author(ctx):
    title = 'SUGGESTIONS BY AUTHOR'
    e = discord.Embed(colour=discord.Colour.purple(), title=title)
    with closing(sqlite3.connect(ctx.bot.db_name)) as con:
        with con:
            suggestions = con.execute('SELECT username, suggestion \
                                        FROM Users NATURAL JOIN \
                                        (SELECT * FROM Suggestions WHERE suggestion_type="game") Q;').fetchall()
        if suggestions:
            suggestions_dict = defaultdict(list)
            for username, game in suggestions:
                suggestions_dict[username].append(game)
            for username in suggestions_dict:
                games = ''
                for game in suggestions_dict[username]:
                    games += '{}\n'.format(game)
                e.add_field(name=username, value=games[:-1], inline=False)
        else:
            e.add_field(name='Nothing has been suggested yet', value=':(', inline=False)
        return e


def message_suggestions_in_category(ctx, suggestion_type: str):
    with closing(sqlite3.connect(ctx.bot.db_name)) as con:
        with con:
            suggestions = con.execute('SELECT suggestion FROM Suggestions WHERE suggestion_type=?;',(suggestion_type,)).fetchall()
        if suggestions:
            message = '__**SUGGESTED {}S**__\n```\n'.format(suggestion_type.upper())
            for entry in suggestions:
                message += '\n{}'.format(entry[0])
            message += '```'
        else:
            message = '__**SUGGESTED {}S**__\n\nNothing has been suggested yet'.format(suggestion_type.upper())
        return message


def embed_suggestions_in_category(ctx, suggestion_type: str):
    title = 'SUGGESTED {}S'.format(suggestion_type.upper())
    e = discord.Embed(colour=discord.Colour.purple())
    with closing(sqlite3.connect(ctx.bot.db_name)) as con:
        with con:
            suggestions = con.execute('SELECT suggestion FROM Suggestions WHERE suggestion_type=?;',(suggestion_type,)).fetchall()
        if suggestions:
            text = ''
            for entry in suggestions:
                text += '{}\n'.format(entry[0])
            e.add_field(name=title, value=text[:-1], inline=False)
        else:
            text = 'Nothing has been suggested yet'
            e.add_field(name=title, value=text, inline=False)
        return e


def split_message(message):
    message_list = []
    if len(message) < 2000:
        return [message]
    else:
        i = message[:2000].rfind('\n')
        message_list.append(message[:i])
        for item in split_message(message[i:]):
            message_list.append(item)
    return message_list
