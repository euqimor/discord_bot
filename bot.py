import discord
from discord.ext import commands
import dict_query
import os
from time import sleep

description = '''An awkward attempt at making a discord bot'''
bot = commands.Bot(command_prefix='$', description=description)

def load_game_suggestions():
    '''
    :return: tries to load a dict of suggestions from a file,
    otherwise returns empty dict
    '''
    suggestions = {}
    os.chdir(os.path.expanduser('~/bothelper/'))
    try:
        suggestions = load_data('suggestions')
    except:
        pass
    return suggestions


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# DON'T FORGET TO CHANGE NICK BACK TO NAME IN SUGGEST
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# CHANGE | BOT.RUN | COMMAND_PREFIX | PLAYING WITH |
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


def save_data(data, filename):
    '''
    :param data: data to be stored into a file
    :param filename: filename to save data to
    :return: None, saves dict as a file for future usage
    '''
    with open(filename, 'w') as file:
        file.write(str(data))

def load_data(filename):
    '''
    :param filename: file from which to load the data
    :return: returns eval() of the file contents
    '''
    data = ''
    try:
        with open(filename) as file:
            data = eval(file.read())
        return data
    except(FileNotFoundError):
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

@bot.command()
async def games(ctx):
    """Prints games suggested so far
    grouped by suggester's name"""
    message = ''
    try:
        for name in suggestions:
            message+='```\r'+'Suggested by '+name+':'
            for game in suggestions[name]:
                message+='\r'+game
            message+='```'
        await ctx.send(message)
    except:
        await ctx.send('Nothing has been suggested so far')

@bot.command()
async def echo(ctx, *, message: str):
    message = ' '.join(message.split())
    msg = await ctx.send(message)
    sleep(3)
    await msg.delete()

@bot.command()
async def echo2(ctx, *, data: str):
    await ctx.send(data+'| nick: '+ctx.author.nick)

@bot.command()
async def merriam(ctx, *, word: str):
    """Prints games suggested so far
    grouped by suggester's name"""
    word = ' '.join(word.split())
    # try:
    cases = dict_query.query_merriam(word)
    # except:
    #     await ctx.send('Something went wrong during online query')
    # try:
    phrase = dict_query.compose_merriam(cases, word)
    # except:
    #     await ctx.send('Something went wrong during result parsing')
    if phrase != '' and phrase is not None:
        await ctx.send(phrase)
    else:
        message = await ctx.send('Could not find the word or something went wrong with the request')
        sleep(4)
        bot.delete_message(message)

miriam = merriam

@bot.command()
async def list(ctx):
    """Prints games suggested so far
    in one list"""
    try:
        set_of_games = set({})
        message = '```\rGames suggested so far:'
        for name in suggestions:
            for game in suggestions[name]:
                set_of_games.add(game)
        for game in set_of_games:
            message+='\r'+game
        message+='```'
        await ctx.send(message)
    except:
        await ctx.send('Nothing has been suggested yet')

@bot.command()
async def suggest(ctx, *, data):
    """Adds a game suggestion"""
    name = str(ctx.author.nick)
    game = ' '.join(data.split())
    if name in suggestions:
        suggestions[name].add(game)
    else:
        suggestions[name] = {game}
    await ctx.send(name+' suggested '+game)
    save_data(suggestions, 'suggestions')

@bot.command()
async def remove(ctx, *, data):
    """Removes game suggestion if the game
    was suggested by the user issuing the command"""
    name = str(ctx.author.nick)
    game = ' '.join(data.split())
    if name in suggestions:
        if game in suggestions[name]:
            suggestions[name].remove(game)
            if suggestions[name] == set({}):
                del suggestions[name]
            save_data(suggestions, 'suggestions')
            await ctx.send('Successfully deleted '+game+' from '+name+'\'s suggestions')
    else:
        await ctx.send('You cannot delete a game you didn\'t suggest')

@bot.command()
async def adminremove(ctx, *, data):
    """Removes game from every suggestion,
    command only available to Admin role"""
    name = str(ctx.author.nick)
    role_obj_list = ctx.author.roles
    game = ' '.join(data.split())
    roles = []
    names_to_delete = []
    for role in role_obj_list:
        roles.append(role.name)
    if 'Admin' in roles:
        for name in suggestions:
            if game in suggestions[name]:
                suggestions[name].remove(game)
                if suggestions[name] == set({}):
                    names_to_delete.append(name)
        for name in names_to_delete:
            del suggestions[name]
        save_data(suggestions, 'suggestions')
        await ctx.send('Successfully deleted ' + game + ' from suggestions')
    else:
        await ctx.send('You need to be an admin to issue this command')

if __name__ == '__main__':
    suggestions = load_game_suggestions()
    # bot.run('MzU3NjUyMTE3MTQ3NzQ2MzA2.DJtBFg.Ph9XfkThb6HM9W7KJ9Ud7fSxkYc') #cutie-pie
    bot.run('MzU3ODg3OTcwMjczMDAxNDcy.DJwzog.SDutum51myHyYMnGvIc_7_rYCZ8') #test-instance
