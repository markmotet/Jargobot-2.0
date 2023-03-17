import sqlite3

def setup_database():
    conn = sqlite3.connect('api_keys.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys
                 (guild_id INTEGER PRIMARY KEY,
                  elevenlabs_api_key TEXT,
                  openai_api_key TEXT)''')
    conn.commit()
    return conn

def store_elevenlabs_api_key(conn, guild_id, api_key):
    with conn:
        conn.execute("INSERT OR REPLACE INTO api_keys (guild_id, elevenlabs_api_key) VALUES (?, ?)", (guild_id, api_key))

def get_elevenlabs_api_key(conn, guild_id):
    with conn:
        api_key = conn.execute("SELECT elevenlabs_api_key FROM api_keys WHERE guild_id=?", (guild_id,)).fetchone()
        if api_key:
            return api_key[0]
        else:
            return None

def store_openai_api_key(conn, guild_id, api_key):
    with conn:
        conn.execute("UPDATE api_keys SET openai_api_key=? WHERE guild_id=?", (api_key, guild_id))

def get_openai_api_key(conn, guild_id):
    with conn:
        api_key = conn.execute("SELECT openai_api_key FROM api_keys WHERE guild_id=?", (guild_id,)).fetchone()
        if api_key:
            return api_key[0]
        else:
            return None

def view_database_entries(conn):
    with conn:
        rows = conn.execute("SELECT * FROM api_keys").fetchall()
        for row in rows:
            print(row)
