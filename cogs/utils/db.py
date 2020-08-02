import sqlite3
import os
from urllib.request import pathname2url
from contextlib import closing


def check_database(db_name):
    path = os.path.realpath(db_name)
    db_uri = f'file:{pathname2url(path)}?mode=rw'
    con = None
    try:
        con = sqlite3.connect(db_uri, uri=True)
        print(f'Database connection test successful: {path}')
        return True
    except sqlite3.Error as e:
        print(f'Database connection failed:\n{e}')
    finally:
        if con:
            con.close()
        else:
            return False


def add_user_to_db_or_pass(con, username, user_id):
    con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
    con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))


async def add_guild_to_db_or_pass(bot, guild_id: int, prefixes: str, locale: str):
    # prefixes must be comma-separated without spaces, ex.: prefixes = '$,!,cc'
    with closing(sqlite3.connect(bot.db_name)) as con:
        with con:
            con.execute('INSERT OR IGNORE INTO Guilds(guild_id, prefix_list, locale) VALUES(?, ?, ?);',
                        (guild_id, prefixes, locale))


async def delete_guild_from_db(bot, guild_id: int):
    with closing(sqlite3.connect(bot.db_name)) as con:
        with con:
            con.execute('PRAGMA foreign_keys = 1;')
            con.execute('DELETE FROM Guilds WHERE guild_id=?;',
                        (guild_id,))


async def load_guild_prefixes(bot, guild_id: int):
    with closing(sqlite3.connect(bot.db_name)) as con:
        with con:
            prefixes = con.execute('SELECT prefix_list FROM Guilds WHERE guild_id=?;',
                                   (guild_id,)).fetchone()[0]
    return list(prefixes.split(','))


def suggestion_exists_check(db_name, suggestion, suggestion_type, user_id=''):
    with closing(sqlite3.connect(db_name)) as con:
        with con:
            if not user_id:
                exists = con.execute('SELECT * FROM Suggestions \
                                      WHERE suggestion LIKE ? AND suggestion_type=?;',
                                     (suggestion, suggestion_type)).fetchall()
            else:
                exists = con.execute('SELECT * FROM Suggestions \
                                      WHERE user_id=? AND suggestion LIKE ? AND suggestion_type=?;',
                                     (user_id, suggestion, suggestion_type)).fetchall()
    return bool(exists)
