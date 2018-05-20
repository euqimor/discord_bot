import discord
import sqlite3
from contextlib import closing
from collections import defaultdict
from discord.utils import get


rejections = ['Nope', 'Nu-uh', 'You are not my supervisor!', 'Sorry, you are not important enough to do that -_-',
              'Stop trying that, or I\'ll report you to Nightmom!', 'Yeah, right.']


async def update_banner(ctx, banner_type):
    guild = ctx.guild
    channel = get(guild.text_channels, name='game_suggestions_bot')
    message_list = await channel.history(limit=3).flatten()
    if message_list:
        if banner_type == 'games':
            e = embed_suggestions_in_category(ctx, 'game')
            author_pic_url = 'https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
            e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
            e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
            await message_list[2].edit(embed=e)
            await message_list[1].edit(embed=embed_games_by_author(ctx))
        elif banner_type == 'movies':
            e = embed_suggestions_in_category(ctx, 'movie')
            e.colour = discord.Colour.orange()
            e.set_thumbnail(url='https://lh3.googleusercontent.com/TAzWe4fpDp8T7od9EoLTj4zJLV6EJQwBZjJ4mVjyzmKNzd5mVMdLU3k8J7XvErqsg59X2i71SQ=w50-h50-e365')
            await message_list[0].edit(embed=e)
    else:
        await create_banners(ctx)


async def create_banners(ctx):
    channel = get(ctx.guild.text_channels, name='game_suggestions_bot')
    e = embed_suggestions_in_category(ctx, 'game')
    author_pic_url = 'https://static-cdn.jtvnw.net/jtv_user_pictures/f01a051288087531-profile_image-70x70.png'
    e.set_thumbnail(url='https://cdn0.iconfinder.com/data/icons/social-network-7/50/16-128.png')
    e.set_author(name='AellaQ', url='https://www.twitch.tv/aellaq', icon_url=author_pic_url)
    await channel.send(embed=e)
    await channel.send(embed=embed_games_by_author(ctx))
    e = embed_suggestions_in_category(ctx, 'movie')
    e.colour = discord.Colour.orange()
    e.set_thumbnail(
        url='https://lh3.googleusercontent.com/TAzWe4fpDp8T7od9EoLTj4zJLV6EJQwBZjJ4mVjyzmKNzd5mVMdLU3k8J7XvErqsg59X2i71SQ=w50-h50-e365')
    await channel.send(embed=e)


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
                games = '\n'.join(suggestions_dict[username])
                e.add_field(name=username, value=games, inline=False)
        else:
            e.add_field(name='Nothing has been suggested yet', value=':(', inline=False)
        return e


def embed_suggestions_in_category(ctx, suggestion_type: str):
    title = f'SUGGESTED {suggestion_type.upper()}S'
    e = discord.Embed(colour=discord.Colour.purple())
    with closing(sqlite3.connect(ctx.bot.db_name)) as con:
        with con:
            suggestions = con.execute('SELECT suggestion FROM Suggestions WHERE suggestion_type=?;',(suggestion_type,)).fetchall()
        if suggestions:
            text = '\n'.join([item[0] for item in suggestions])
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
