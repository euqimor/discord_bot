import discord
from discord.ext import commands
import dict_query
from time import sleep
import random

# TODO PROVIDE HELP INSTRUCTIONS, separate commands into groups, add multi-server support(?)
# TODO 2000 symbols limit for suggestions list

description = '''An awkward attempt at making a discord bot'''
bot = commands.Bot(command_prefix='$', description=description)


async def check_admin_rights(ctx):
    try:
        roles_list = ctx.author.roles
    except AttributeError:
        await ctx.send('Something went wrong. If you tried this command in a DM, the bot '
                       'doesn\'t know how to check if you have admin rights.')
        return None
    roles = []
    for role in roles_list:
        roles.append(role.name)
    success_flag = 0
    if 'Admin' in roles:
        success_flag = 1
    elif ctx.author.id == 173747843314483210:
        success_flag = 1
    return bool(success_flag)


def load_game_suggestions():
    """
    :return: tries to load a dict of suggestions from a file,
    otherwise returns empty dict
    """
    suggestions = load_data('suggestions')
    if not suggestions:
        suggestions = {}
    return suggestions


def save_data(data, filename):
    """
    :param data: data to be stored into a file
    :param filename: filename to save data to
    :return: None, saves dict as a file for future usage
    """
    with open(filename, 'w') as file:
        file.write(str(data))


def load_data(filename):
    """
    :param filename: file from which to load the data
    :return: returns eval() of the file contents
    """
    try:
        with open(filename) as file:
            data = eval(file.read())
        return data
    except FileNotFoundError:
        print('File not found')
    except:
        print('Something went wrong during data evaluation')


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='with turrets'))


def create_games_message(suggestions):
    if suggestions:
        message = '__**SUGGESTIONS BY AUTHOR**__\n\n'
        for userid in suggestions:
            message += '**'+suggestions[userid]['username']+':**\n'+'```'
            for game in suggestions[userid]['games']:
                message += '\n' + game
            message += '```'
    else:
        message = 'Nothing has been suggested yet'
    return message


@bot.command()
async def games_full(ctx):
    """Prints games suggested so far grouped by suggestion author's name"""
    message = create_games_message(suggestions)
    await ctx.send(message)


def create_list_message(suggestions):
    if suggestions:
        set_of_games = set({})
        message = '__**SUGGESTED GAMES**__\n```\n'
        for userid in suggestions:
            for game in suggestions[userid]['games']:
                if game.lower() not in [x.lower() for x in set_of_games]:
                    set_of_games.add(game)
        for game in set_of_games:
            message += '\n' + game
        message += '```'
    else:
        message = 'Nothing has been suggested yet'
    return message


@bot.command()
async def games_list(ctx):
    """Prints games suggested so far in one list"""
    message = create_list_message(suggestions)
    await ctx.send(message)


@bot.command()
async def suggest(ctx, *, data):
    """Adds a game suggestion"""
    userid = ctx.author.id
    name = str(ctx.author.name)
    game = ' '.join(data.split())
    if userid in suggestions:
        if game.lower() not in [x.lower() for x in suggestions[userid]['games']]:
            suggestions[userid]['games'].add(game)
        else:
            await ctx.send('{} is in your suggestions already'.format(game))
        if suggestions[userid]['username'] != name:
            suggestions[userid]['username'] = name
    else:
        suggestions[userid] = {}
        suggestions[userid]['username'] = name
        suggestions[userid]['games'] = {game}
    save_data(suggestions, 'suggestions')
    await update_games_banner(ctx)
    await ctx.send(name+' suggested '+game)


@bot.command()
async def remove(ctx, *, data):
    """Removes the game suggestion if the game was suggested by the user issuing the command"""
    userid = ctx.author.id
    name = str(ctx.author.name)
    game = ' '.join(data.split())
    success_flag = 0
    game_not_found = 1
    if userid in suggestions:
        if suggestions[userid]['games'] != set({}):
            for existing_game in suggestions[userid]['games']:
                if game.lower() == existing_game.lower():
                    game_not_found = 0
                    suggestions[userid]['games'].remove(existing_game)
        else:
            del suggestions[userid]  # note to self: should change this if anything else is to be stored for userid except for name and game suggestions
        save_data(suggestions, 'suggestions')
        await update_games_banner(ctx)
        success_flag = 1
    if success_flag:
        await ctx.send('Successfully deleted '+game+' from '+name+'\'s suggestions')
    elif game_not_found:
        await ctx.send('Game \"'+game+'\" not found in '+name+'\'s suggestions')
    else:
        await ctx.send('Something went wrong')


@bot.command()
async def adminremove(ctx, *, data):
    """Removes the game from every list, command only available to Admin role"""
    try:
        role_obj_list = ctx.author.roles
    except AttributeError:
        await ctx.send('Something went wrong. If you tried this command in a DM, the bot '
                       'doesn\'t know how to check if you have admin rights.')
        return None
    game = ' '.join(data.split())
    roles = []
    ids_to_delete = []
    for role in role_obj_list:
        roles.append(role.name)
    if 'Admin' in roles:
        success_flag = 0
        for userid in suggestions:
            if game in suggestions[userid]['games']:
                suggestions[userid]['games'].remove(game)
                success_flag = 1  # flag is placed here because below is only deletion of users with empty suggestions
                if suggestions[userid]['games'] == set({}):
                    ids_to_delete.append(userid)
        for userid in ids_to_delete:
            del suggestions[userid]
            save_data(suggestions, 'suggestions')
            await update_games_banner(ctx)
        if success_flag:
            await ctx.send('Successfully deleted ' + game + ' from suggestions')
        else:
            await ctx.send('Game \"'+game+'\" not found in suggestions')
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def adminwipe(ctx):
    """Purges the game suggestions list, command only available to Admin role"""
    try:
        role_obj_list = ctx.author.roles
    except AttributeError:
        await ctx.send('Something went wrong. If you tried this command in a DM, the bot '
                       'doesn\'t know how to check if you have admin rights.')
        return None
    roles = []
    for role in role_obj_list:
        roles.append(role.name)
    if 'Admin' in roles:
        global suggestions
        suggestions = {}
        save_data(suggestions, 'suggestions')
        await update_games_banner(ctx)
        await ctx.send('The list is empty now :\'(')
    else:
        await ctx.send(random.choice(rejections))


@bot.command(aliases=['miriam', 'Miriam', 'MIRIAM', 'GODDAMITMIRIAM', 'word', 'mw', 'Merriam'])
async def merriam(ctx, *, word: str):
    """Queries Merriam-Webster's Collegiate Dictionary for a word definition. Well, tries to at least..."""
    word = ' '.join(word.split())
    # try:
    query_result = dict_query.query_merriam(word, keys['merriam_webster'])
    cases = query_result  # the word may have changed if you queried for the past tense for example
    # except:
    #     await ctx.send('Something went wrong during online query')
    # try:
    phrase = dict_query.parse_merriam(cases)
    # except:
    #     await ctx.send('Something went wrong during result parsing')
    if phrase != '' and phrase is not None:
        if len(phrase) >= 2000:
            message_list = dict_query.split_message(phrase)
            # for message in message_list:
            await ctx.send(message_list[0])
            await ctx.send('\_'*20+'\nRead more: '+'https://www.merriam-webster.com/dictionary/'+'%20'.join(word.split(' ')))
        else:
            await ctx.send(phrase)
    else:
        message = await ctx.send('Could not find the word or something went wrong with the request')
        sleep(4)
        await message.delete()


# @bot.command()
# async def adc(ctx, *, data: str):
#     message = ctx.message
#     tshootdata = str(message.channel)+' | '+str(isinstance(message.channel, discord.DMChannel))
#     # channels = str(str(x)+'; ' for x in bot.get_all_channels())
#     await ctx.send(tshootdata)


async def update_games_banner(ctx):
    guild = bot.guilds[0]  # TODO think about fixing this. Or don't... Remember that right now ctx is not used
    channel = [x for x in guild.text_channels if x.name == 'game_suggestions_bot'][0]
    message_list = []
    async for message in channel.history(limit=100):
        if message.author.id == bot.user.id:
            message_list.append(message)
    if message_list:
        if suggestions:
            await message_list[0].edit(content=create_games_message(suggestions))
            await message_list[1].edit(content=create_list_message(suggestions))
        else:
            await message_list[0].delete()
            await message_list[1].delete()
    else:
        if suggestions:
            await channel.send(create_list_message(suggestions))
            await channel.send(create_games_message(suggestions))


@bot.command()
async def set_prefix(ctx, message: str):  # TODO save permanently
    prefix = message.strip()
    if await check_admin_rights(ctx):
        bot.command_prefix = prefix
        await ctx.send('The prefix is set to '+str(bot.command_prefix))
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def set_nick(ctx, *, message: str = ''):
    nickname = message.strip()
    if await check_admin_rights(ctx):
        bot_member = [x for x in bot.get_all_members() if x.bot and x.id == bot.user.id][0]
        await bot_member.edit(nick=nickname)
        await ctx.send('Nickname set')
    else:
        await ctx.send(random.choice(rejections))


@bot.command()
async def set_status(ctx, *, message: str = ''):  # TODO save permanently?
    status = message.strip()
    if await check_admin_rights(ctx):
        await bot.change_presence(game=discord.Game(name=status))
        await ctx.send('Status set')
    else:
        await ctx.send(random.choice(rejections))


if __name__ == '__main__':
    keys = load_data('keys')
    rejections = ['Nope', 'Nu-uh', 'You are not my supervisor!', 'Sorry, you are not important enough to do that -_-',
                  'Stop trying that, or I\'ll report you to Nightmom!', 'Yeah, right.']
    suggestions = load_game_suggestions()
    bot.run(keys['bot'])
