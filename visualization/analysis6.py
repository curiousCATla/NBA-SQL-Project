"""
analysis6.py — Highest-scoring rookie each season since 1953.

Identifies each player's debut season, then ranks rookies within
each year by PPG to find the top scorer. The 1953 cutoff reflects
when the league's rookie tracking becomes statistically consistent.

Output: images/rook_ppg_by_season.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from adjustText import adjust_text

conn = sqlite3.connect('nba.db')
q6 = pd.read_sql_query("""
WITH clean_stats AS (
      -- Keep TOT rows for traded players; discard their individual team rows.
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
      -- Each player's earliest season in the dataset is treated as their rookie year.
      SELECT Player, MIN(Season) AS rookie_season
      FROM player_stats
      GROUP BY Player
  ),
  rookie_stats AS (
      -- Join on both player name and season to isolate only the rookie-year row.
      -- G >= 20 excludes players with too few games for a meaningful average.
      SELECT cs.Player, cs.Season, cs.Tm, cs.G,
             ROUND(cs.PTS / cs.G, 2) AS PPG
      FROM clean_stats cs
      JOIN rookie_year ry
          ON cs.Player = ry.Player
         AND cs.Season = ry.rookie_season
      WHERE cs.G >= 20
  ),
  ranked_rookies AS (
      -- PARTITION BY Season means rankings reset for each year,
      -- so rank 1 is the top rookie scorer within that specific season.
      SELECT *,
             RANK() OVER (PARTITION BY Season ORDER BY PPG DESC) AS ppg_rank
      FROM rookie_stats
  )
  SELECT Player, Season, Tm, G, PPG
  FROM ranked_rookies
  WHERE ppg_rank = 1
    AND Season >= 1953
  ORDER BY Season;
""", conn)
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
plt.savefig('images/rook_ppg_by_season.png', dpi=150, bbox_inches='tight')
plt.show()