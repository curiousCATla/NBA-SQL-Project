"""
analysis11.py — Salary efficiency: scoring value per dollar spent (2021 season).

Joins player scoring stats with salary data to compute PPG per $1M,
identifying which players deliver the most on-court value relative
to their contract. Uses 2021 as the most recent season with salary data.

Output: images/salary_efficiency_2021.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import os
from adjustText import adjust_text

conn = sqlite3.connect('nba.db')

df = pd.read_sql_query("""
WITH clean_stats AS (
    -- Deduplicate traded players: keep the combined TOT row, drop individual team rows.
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
clean_salaries AS (
    -- Two problems to fix in the source data:
    -- 1. Salary is stored as a string like "$4,250,000" — strip symbols, cast to integer.
    -- 2. Some players have duplicate rows with identical values — DISTINCT removes them.
    SELECT DISTINCT
        playerName,
        seasonStartYear,
        CAST(REPLACE(REPLACE(salary, ',', ''), '$', '') AS INTEGER) AS salary_int
    FROM salaries
),
player_value AS (
    SELECT
        cs.Player,
        cs.Tm,
        cs.G,
        ROUND(cs.PTS / cs.G, 1)                          AS PPG,
        ROUND(sal.salary_int / 1000000.0, 2)                    AS salary_millions,
        -- Core metric: points scored per $1M of salary.
        -- Higher = more scoring value per dollar spent.
        ROUND((cs.PTS * 1.0 / cs.G) / (sal.salary_int / 1000000.0), 2) AS ppg_per_million
    FROM clean_stats cs
    JOIN clean_salaries sal
        ON cs.Player     = sal.playerName
       AND cs.Season     = sal.seasonStartYear
    -- G >= 41 = at least half a season played.
    -- Filters out injury-shortened seasons where a small sample inflates the metric.
    WHERE cs.Season = 2021
      AND cs.G >= 41
)
SELECT Player, Tm, G, PPG, salary_millions, ppg_per_million
FROM player_value
ORDER BY ppg_per_million DESC;

""", conn)

conn.close()

# --- Scatter plot: salary vs PPG, coloured by value ---

fig, ax = plt.subplots(figsize=(12, 8))

# Colour each point by ppg_per_million so high-value players stand out visually.
scatter = ax.scatter(
    df['salary_millions'],
    df['PPG'],
    c=df['ppg_per_million'],
    cmap='RdYlGn',        # red = poor value, yellow = average, green = great value
    s=60,
    alpha=0.7
)

# Add a colourbar legend to explain the colour scale.
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('PPG per $1M', fontsize=11)

# Label only the top 10 and bottom 5 by value to keep the chart readable.
top10    = df.head(10)
bottom5  = df.nsmallest(5, 'ppg_per_million')
to_label = pd.concat([top10, bottom5]).drop_duplicates()

# Step 1: create one text object per label and collect them in a list.
# ax.text() returns a Text object — adjust_text needs the full list to
# know which labels are competing for space.
texts = []
for _, row in to_label.iterrows():
    t = ax.text(row['salary_millions'], row['PPG'], row['Player'], fontsize=7, fontweight='bold')
    texts.append(t)

# Step 2: pass the list to adjust_text.
# arrowprops draws a thin line from the nudged label back to the data point.
adjust_text(
    texts,
    ax=ax,
    arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)
)

ax.set_title('NBA 2021 — Scoring Value per Dollar Spent', fontsize=14)
ax.set_xlabel('Salary ($ millions)', fontsize=12)
ax.set_ylabel('Points Per Game (PPG)', fontsize=12)
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('$%.0fM'))

plt.tight_layout()
os.makedirs('images', exist_ok=True)
plt.savefig('images/salary_efficiency_2021.png', dpi=150, bbox_inches='tight')
plt.show()
