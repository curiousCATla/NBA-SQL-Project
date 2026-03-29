import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from adjustText import adjust_text

conn = sqlite3.connect('nba.db')
q1 = pd.read_sql_query("""
SELECT
    Player,
    Season,
    Tm,
    PTS
FROM player_stats
ORDER BY PTS DESC
LIMIT 10;
""", conn) #inputting the SQL query as a string, and the connection object to the database. The result is stored in a pandas DataFrame called q1.
# Combine Player + Season into one label for the y-axis because players like Wilt have multiple entries on this list from different seasons 
q1['Player_Season'] = q1['Player'] + ' (' + q1['Season'].astype(str) + ')'

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(
    data=q1,
    x='PTS',
    y='Player_Season',
    hue='Tm',
    dodge=False,
    ax=ax
)
ax.set_title('Top 10 Single-Season Scorers of All Time', fontsize=14)
ax.set_xlabel('Points Per Game', fontsize=12)
ax.set_ylabel('')
ax.legend(title='Team', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig('images/top_10_scorers.png', dpi=150, bbox_inches='tight')
plt.show()
