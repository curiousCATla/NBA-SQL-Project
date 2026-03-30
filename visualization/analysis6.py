
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from adjustText import adjust_text

conn = sqlite3.connect('nba.db')
q6 = pd.read_sql_query("""
WITH clean_stats AS (
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
  rookie_year AS (
      SELECT Player, MIN(Season) AS rookie_season
      FROM player_stats
      GROUP BY Player
	  --By only considering 2 columns, it makes the SQL more efficient
  ),
  rookie_stats AS (
      SELECT cs.Player, cs.Season, cs.Tm, cs.G,
             ROUND(cs.PTS  / cs.G, 2) AS PPG
      FROM clean_stats cs
      JOIN rookie_year ry
          ON cs.Player = ry.Player
         AND cs.Season = ry.rookie_season
	  --Using 2 distinct parameters for JOIN to find the player's rookie stats
      WHERE cs.G >= 20
  ),
  ranked_rookies AS (
      SELECT *,
             RANK() OVER (PARTITION BY Season ORDER BY PPG DESC) AS ppg_rank
	  --Using a partition to compare each player's rookie season, and finding the rookie with the highest points per game. 
      FROM rookie_stats
  )
  SELECT Player, Season, Tm, G, PPG
  FROM ranked_rookies
  WHERE ppg_rank = 1
    AND Season >= 1953
  ORDER BY Season;
""" , conn)
fig, ax = plt.subplots(figsize=(12, 5))
sns.scatterplot(
    data=q6,
    x='Season',
    y='PPG',
    ax=ax
)
ax.set_title('Highest Rookie Average Points Per Game by Season', fontsize=14)
ax.set_xlabel('Season(year)', fontsize=12)
ax.set_ylabel('Average Points Per Game', fontsize=12)

plt.tight_layout()
plt.savefig('images/highest_rookie_ppg_by_season.png', dpi=150, bbox_inches='tight')
plt.show()