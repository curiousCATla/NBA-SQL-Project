import pandas as pd
import sqlite3
import os

# 1. Load CSVs into pandas DataFrames
player_stats = pd.read_csv(os.path.join('data', 'NBA_Player_Stats.csv'))
player_boxscores = pd.read_csv(os.path.join('data', 'NBA_Player_Box Score_Stats.csv'))


# 2. Drop leftover index columns produced when the CSVs were originally exported.
#    Any column whose name starts with "Unnamed" is just a row number artifact — not real data.
unnamed_cols = [col for col in player_stats.columns if col.startswith('Unnamed')]
player_stats = player_stats.drop(columns=unnamed_cols)

unnamed_cols = [col for col in player_boxscores.columns if col.startswith('Unnamed')]
player_boxscores = player_boxscores.drop(columns=unnamed_cols)

# 3. Sanity check — confirm the unnamed columns are gone
print(player_stats.shape)        # (rows, columns)
print(player_stats.dtypes)       # column names and their inferred types
print(player_stats.head())       # first 5 rows
print(player_boxscores.shape)    
print(player_boxscores.dtypes)  
print(player_boxscores.head())   

# 4. Create (or connect to) a SQLite database file
#    If nba.db doesn't exist yet, SQLite will creates it automatically.
conn = sqlite3.connect('nba.db')

# 5. Write each DataFrame into its own table inside the database
#    if_exists='replace' drops and recreates the table every time you run this script,
#    so data stays in sync with CSVs.
#    index=False tells pandas NOT to write the DataFrame's row numbers as a column.
player_stats.to_sql('player_stats', conn, if_exists='replace', index=False)
player_boxscores.to_sql('player_boxscores', conn, if_exists='replace', index=False)

print("\nTables loaded successfully!")

# 5. Quick verification — ask SQLite which tables now exist in the database
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables in nba.db:", cursor.fetchall())

# 6. Close the connection when you're done
conn.close()


