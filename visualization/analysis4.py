import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from adjustText import adjust_text

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
