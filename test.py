import sqlite3

# Create a new database file
conn = sqlite3.connect('mybot.db')

# Create a new table to store the numbers
conn.execute('''
    CREATE TABLE IF NOT EXISTS numbers (
        server_id TEXT PRIMARY KEY,
        number INTEGER
    )
''')

# Save a number for a server
server_id = '12345'
number = 42
conn.execute('''
    INSERT OR REPLACE INTO numbers (server_id, number) 
    VALUES (?, ?)
''', (server_id, number))

# Retrieve the number for a server
result = conn.execute('SELECT number FROM numbers WHERE server_id = ?', (server_id,))
number = result.fetchone()[0]
print(number)

# Close the connection
conn.close()
