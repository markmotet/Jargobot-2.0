import sqlite3
import json
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
    
    #Create table that stores active_voice_ids, message_lists, connections, message_ids
    c.execute('''CREATE TABLE IF NOT EXISTS server_data
                (guild_id INTEGER PRIMARY KEY,
                active_voice_id TEXT,
                message_list TEXT,
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

def get_role_message(conn, voice_id):
    with conn:
        role_message = conn.execute("SELECT role_message FROM voices WHERE voice_id=?", (voice_id,)).fetchone()
        if role_message:
            return role_message[0]
        else:
            return None

def set_role_message(conn, voice_id, guild_id, role_message):
    with conn:
        conn.execute("INSERT OR REPLACE INTO voices (voice_id, guild_id, role_message) VALUES (?, ?, ?)", (voice_id, guild_id, role_message))

def voice_id_exists(conn, voice_id, guild_id):
    with conn:
        voice_id = conn.execute("SELECT voice_id FROM voices WHERE voice_id=? AND guild_id=?", (voice_id, guild_id)).fetchone()
        if voice_id:
            return True
        else:
            return False
        
def set_server_data(conn, guild_id, column, value):
    c = conn.cursor()

    # Insert the guild_id if it doesn't exist
    c.execute("INSERT OR IGNORE INTO server_data (guild_id) VALUES (?)", (guild_id,))

    if column in ['message_list']:
        # Ensure the value is a list containing dictionaries with the required keys or an empty list
        if isinstance(value, list) and (not value or all(isinstance(item, dict) and 'role' in item and 'content' in item for item in value)):
            # Convert the list to a JSON string
            value = json.dumps(value)
        else:
            raise ValueError("Value must be a list containing dictionaries with 'role' and 'content' keys, or an empty list")

    # Update the column with the new value
    c.execute(f"UPDATE server_data SET {column} = ? WHERE guild_id = ?", (value, guild_id))
    print(f"Updated {column} to {value} for guild {guild_id}")
    conn.commit()

def append_to_message_list(conn, guild_id, message_dict):
    if not (isinstance(message_dict, dict) and 'role' in message_dict and 'content' in message_dict):
        raise ValueError("Message dictionary must have 'role' and 'content' keys")

    c = conn.cursor()

    # Retrieve the current message_list
    current_message_list = get_server_data(conn, guild_id, 'message_list')

    # If there is no current message_list, create a new one
    if current_message_list is None:
        current_message_list = []

    # Append the message_dict to the current_message_list
    current_message_list.append(message_dict)

    # Update the message_list in the database
    set_server_data(conn, guild_id, 'message_list', current_message_list)


def get_server_data(conn, guild_id, column):

    print(f"Getting {column} for guild {guild_id}...")

    c = conn.cursor()
    c.execute(f"SELECT {column} FROM server_data WHERE guild_id = ?", (guild_id,))
    result = c.fetchone()

    print(f"Result: {result}...")

    if result:
        if column in ['message_list']:
            return json.loads(result[0])
        return result[0]
    else:
        return None
    
def show_table(conn, table_name):
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    rows = c.fetchall()
    for row in rows:
        print(row)
