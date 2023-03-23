import sqlite3

def setup_database():
    conn = sqlite3.connect('api_keys.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys
                 (guild_id INTEGER PRIMARY KEY,
                  elevenlabs_api_key TEXT,
                  openai_api_key TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS voices
                (voice_id TEXT PRIMARY KEY,
                guild_id INTEGER,
                role_message TEXT,
                FOREIGN KEY (guild_id) REFERENCES api_keys (guild_id))''')
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

def get_role_message(conn, voice_id):
    with conn:
        role_message = conn.execute("SELECT role_message FROM voices WHERE voice_id=?", (voice_id,)).fetchone()
        if role_message:
            return role_message[0]
        else:
            return None

def store_voice_role(conn, voice_id, guild_id, role_message):
    with conn:
        conn.execute("INSERT OR REPLACE INTO voices (voice_id, guild_id, role_message) VALUES (?, ?, ?)", (voice_id, guild_id, role_message))

def voice_id_exists(conn, voice_id, guild_id):
    with conn:
        voice_id = conn.execute("SELECT voice_id FROM voices WHERE voice_id=? AND guild_id=?", (voice_id, guild_id)).fetchone()
        if voice_id:
            return True
        else:
            return False