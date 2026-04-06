"""
analysis5.py — Scoring tier distribution across the 2022 NBA season.

Classifies every player into one of five tiers by PPG and shows
what proportion of the league falls into each category.

Output: images/scoring_tiers_2022.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from adjustText import adjust_text

conn = sqlite3.connect('nba.db')
q5 = pd.read_sql_query("""
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
player_tier_2022 AS (
    SELECT
        Player,
        Tm,
        CAST(PTS AS FLOAT) / G AS PPG,
        -- Tier boundaries are based on common basketball analysis conventions
        -- for categorising player scoring roles.
        CASE
            WHEN CAST(PTS AS FLOAT) / G >= 25 THEN 'Elite (25+)'
            WHEN CAST(PTS AS FLOAT) / G >= 20 THEN 'Star (20-24)'
            WHEN CAST(PTS AS FLOAT) / G >= 15 THEN 'Starter (15-19)'
            WHEN CAST(PTS AS FLOAT) / G >= 10 THEN 'Role Player (10-14)'
            ELSE 'Bench (< 10)'
        END AS scoring_tier
    FROM clean_stats
    WHERE Season = 2022
      AND G >= 1
)
SELECT
    scoring_tier,
    COUNT(*) AS num_players
FROM player_tier_2022
GROUP BY scoring_tier
-- MIN(PPG) orders tiers from highest to lowest scoring in the pie chart,
-- since we can't ORDER BY the CASE expression directly after GROUP BY.
ORDER BY MIN(PPG) DESC;
""", conn)

labels = q5['scoring_tier']
sizes  = q5['num_players']

fig, ax = plt.subplots()
ax.pie(sizes, labels=labels, autopct='%1.1f%%')

ax.set_title('NBA 2022 — Players per Scoring Tier')
plt.tight_layout()
plt.savefig('images/scoring_tiers_2022.png', dpi=150, bbox_inches='tight')
plt.show()
