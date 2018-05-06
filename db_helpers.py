def add_user_to_db_or_pass(con, username, user_id):
    con.execute('UPDATE OR IGNORE Users SET username=? WHERE user_id=?;', (username, user_id))
    con.execute('INSERT OR IGNORE INTO Users(username, user_id) VALUES(?, ?);', (username, user_id))