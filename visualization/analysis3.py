"""
analysis3.py — League-wide scoring trend from 1950 to 2023.

Plots the average PPG across all players per season, revealing
how scoring has shifted across different eras of the game.

Output: images/avg_ppg_by_season.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from adjustText import adjust_text

conn = sqlite3.connect('nba.db')

q3 = pd.read_sql_query("""
  WITH clean_stats AS (
      -- Basketball Reference adds a combined 'TOT' row for players traded mid-season.
      -- We keep TOT and drop the individual team rows for those players,
      -- so each player is counted once per season.
      SELECT * FROM player_stats WHERE Tm = 'TOT'
      UNION ALL
      SELECT * FROM player_stats
      WHERE NOT EXISTS (
          SELECT 1 FROM player_stats p2
          WHERE p2.Player = player_stats.Player
            AND p2.Season = player_stats.Season
            AND p2.Tm = 'TOT'
      )
  ),
  player_avg AS (
      -- G >= 1 excludes players who appeared on a roster but never played.
      SELECT Season, Player, ROUND(PTS / G, 2) AS PPG, G
      FROM clean_stats
      WHERE G >= 1
  )
SELECT
    Season,
    AVG(PPG)    AS avg_PPG,
    COUNT(*)    AS player_count,
    AVG(G)      AS avg_GP
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
plt.show()