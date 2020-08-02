import sqlite3
import os
from urllib.request import pathname2url
from contextlib import closing


def check_database(db_name):
    path = os.path.realpath(db_name)
    db_uri = 'file:{}?mode=rw'.format(pathname2url(path))
    con = None
    try:
        con = sqlite3.connect(db_uri, uri=True)
        print('Database connection test successful: {}'.format(path))
        return True
    except sqlite3.OperationalError:
        print('Database not found: {}\nAttempting to create a new database'.format(path))
        try:
            con = sqlite3.connect(db_name)
            commands = [
                'CREATE TABLE Users(user_id INT PRIMARY KEY, username TEXT);',
                'CREATE TABLE Suggestions (id INTEGER PRIMARY KEY, user_id INT, suggestion TEXT, suggestion_type TEXT,\
                 FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,\
                 UNIQUE (suggestion COLLATE NOCASE, suggestion_type));',
                'CREATE TABLE Proverbs(proverb TEXT);',
                'CREATE TABLE Tags (id INTEGER PRIMARY KEY, user_id INT, tag_name TEXT, tag_content TEXT,\
                 UNIQUE (tag_name COLLATE NOCASE));',
                'CREATE TABLE Tag_Aliases (id INTEGER PRIMARY KEY, user_id INT, tag_id INT, alias TEXT,\
                                 FOREIGN KEY(tag_id) REFERENCES Tags(tag_id) ON DELETE CASCADE,\
                                 UNIQUE (alias COLLATE NOCASE));',
            ]
            for command in commands:
                con.execute(command)
            print('New database created: {}'.format(path))
            return True
        except sqlite3.Error as e:
            print('Database creation failed: {}'.format(e))
    finally:
        if con:
            con.close()
        else:
            return False


def add_user_to_db_or_pass(con, username, user_id):
    con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
    con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))

def add_guild_to_db_or_pass(con, guild_id, prefix_list, locale='en'):
    con.execute('INSERT OR IGNORE INTO Guilds(guild_id, prefix_list, locale) VALUES(?, ?, ?);',
                (guild_id, prefix_list, locale))

def delete_guild_from_db(con, guild_id):
    con.execute('DELETE FROM Guilds WHERE guild_id=?;',
                (guild_id,))

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