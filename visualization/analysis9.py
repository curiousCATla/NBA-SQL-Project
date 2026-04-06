"""
analysis9.py — Most improved scorers from the 2021 to 2022 season.

Compares each player's PPG in both seasons and ranks by the
largest positive difference. Only players who appeared in both
seasons with 20+ games qualify.

Output: displayed interactively (not saved to file)
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sqlite3
import numpy as np

conn = sqlite3.connect('nba.db')

q9 = pd.read_sql_query("""
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
  season_2021 AS (
      -- G >= 20 ensures a statistically meaningful sample for each season.
      SELECT Player, ROUND(PTS * 1.0 / G, 1) AS PPG_2021
      FROM clean_stats
      WHERE Season = 2021 AND G >= 20
  ),
  season_2022 AS (
      SELECT Player, Tm, ROUND(PTS * 1.0 / G, 1) AS PPG_2022
      FROM clean_stats
      WHERE Season = 2022 AND G >= 20
  ),
  combined AS (
      -- INNER JOIN means only players present in both seasons are included.
      -- Players who debuted in 2022 or didn't play in 2021 are excluded.
      SELECT
          s22.Player, s22.Tm,
          s21.PPG_2021, s22.PPG_2022,
          ROUND(s22.PPG_2022 - s21.PPG_2021, 1) AS improvement
      FROM season_2022 s22
      JOIN season_2021 s21 ON s22.Player = s21.Player
  )
SELECT Player, Tm, PPG_2021, PPG_2022, improvement
FROM combined
ORDER BY improvement DESC
LIMIT 10;
""", conn)

x = np.arange(len(q9['Player']))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(x - width/2, q9['PPG_2021'], width, label='2021')
ax.bar(x + width/2, q9['PPG_2022'], width, label='2022')

for i, row in q9.iterrows():
    # Label floats above the 2022 bar to show the exact improvement at a glance.
    ax.text(i + width/2, row['PPG_2022'] + 0.2, f"+{row['improvement']}",
            ha='center', va='bottom', fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(q9['Player'], rotation=45, ha='right')
ax.set_title('Most Improved Players in PPG from 2021 to 2022', fontsize=14)
ax.set_ylabel('Points Per Game')
ax.legend()
plt.tight_layout()
plt.show()
