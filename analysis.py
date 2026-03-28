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


q2 = pd.read_sql_query("""
SELECT
Player,
Season,
Tm,
ROUND(PTS * 1.0 / G, 1) AS PPG,
ROUND(AST * 1.0 / G, 1) AS APG
FROM player_stats
WHERE PPG >= 25 AND APG >= 7 AND G >= 41
ORDER BY PPG DESC
LIMIT 30;
""", conn)

q2['Label'] = q2['Player'] + '\n(' + q2['Season'].astype(str) + ')'

fig, ax = plt.subplots(figsize=(10, 8))

sns.scatterplot(
    data=q2,
    x='PPG',
    y='APG',
    hue='Player',
    s=120,
    ax=ax
)

# Collect all labels first, then adjust_text spreads them apart automatically
texts = []
for _, row in q2.iterrows():
    texts.append(ax.text(row['PPG'], row['APG'], row['Label'], fontsize=7)) #here all the lables are created and stored in the list "texts". Each label is positioned at the corresponding PPG and APG values for each player, and the text is formatted to include the player's name and season.
adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)) #adjust_text is a function from the adjustText library that helps to prevent overlapping text labels in a plot. It takes a list of text objects and adjusts their positions to minimize overlap, while optionally drawing arrows from the original position to the new position.

ax.axvline(x=25, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax.axhline(y=7,  color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

ax.set_title('Players Averaging 25+ PPG and 7+ APG in a Single Season', fontsize=13)
ax.set_xlabel('Points Per Game (PPG)', fontsize=11)
ax.set_ylabel('Assists Per Game (APG)', fontsize=11)
ax.legend(title='Player', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

plt.tight_layout()

os.makedirs('images', exist_ok=True)
plt.savefig('images/ppg_vs_apg_scatter.png', dpi=150, bbox_inches='tight')
plt.show()


q3 = pd.read_sql_query("""
  WITH clean_stats AS (
      SELECT * FROM player_stats WHERE Tm = 'TOT'
      UNION ALL
      SELECT *  FROM player_stats
      WHERE NOT EXISTS (
          SELECT 1 FROM player_stats p2
          WHERE p2.Player = player_stats.Player
            AND p2.Season = player_stats.Season
            AND p2.Tm = 'TOT'
      )
  ),
 player_avg AS (
	SELECT Season, Player, ROUND(PTS/G, 2) AS PPG, G
	FROM clean_stats
	WHERE G >= 1
  )
SELECT 
Season, AVG(PPG) AS avg_PPG, COUNT(*) AS player_count, AVG(G) AS avg_GP
FROM player_avg
GROUP BY Season
ORDER BY Season;
""", conn) 

fig, ax = plt.subplots(figsize=(12, 5))
sns.scatterplot(
    data=q3,
    x='Season',
    y='avg_PPG',
    ax=ax
)
ax.set_title('Average Player Points Per Game over Time', fontsize=14)
ax.set_xlabel('Season(year)', fontsize=12)
ax.set_ylabel('Average Points Per Game', fontsize=12)

plt.tight_layout()
plt.savefig('images/avg_ppg_by_season.png', dpi=150, bbox_inches='tight')

conn = sqlite3.connect('nba.db')
q4 = pd.read_sql_query("""
  WITH clean_stats AS (
      SELECT * FROM player_stats WHERE Tm = 'TOT'
      UNION ALL
      SELECT *  FROM player_stats
      WHERE NOT EXISTS (
          SELECT 1 FROM player_stats p2
          WHERE p2.Player = player_stats.Player
            AND p2.Season = player_stats.Season
            AND p2.Tm = 'TOT'
      )
  ),
 player_avg AS (
	SELECT Season, Player, ROUND(PTS/G, 2) AS PPG, G
	FROM clean_stats
	WHERE G >= 1
  )
SELECT 
    Player,
    COUNT(Season)    AS seasons_above_20,
    ROUND(AVG(PPG), 1) AS avg_ppg_in_those_seasons
FROM player_avg
WHERE PPG >= 20
GROUP BY Player
HAVING COUNT(Season) >= 5
ORDER BY seasons_above_20 DESC
lIMIT 20;
""", conn) 

fig, ax = plt.subplots(figsize=(12, 5))
sns.barplot(
    data=q4,
    x='seasons_above_20',
    y='Player',
    dodge=False,
    ax=ax
)
ax.set_title('Number of Seasons Players Averaged 20+ PPG', fontsize=14)
ax.set_xlabel('Seasons Above 20 PPG', fontsize=12)
ax.set_ylabel('')

plt.tight_layout()
plt.savefig('images/seasons_above_20.png', dpi=150, bbox_inches='tight')
plt.show()

conn.close()
