"""
analysis12.py — Value for money: most underpaid and overpaid players (2021 season).

Uses a composite production score (PTS + TRB + AST + STL + BLK - TOV per game)
and compares it against salary to find who delivers the most and least
on-court value per dollar.

Output: images/value_for_money_2021.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
    -- Fix two source-data problems in one pass:
    -- 1. Salary stored as "$4,250,000" — strip symbols, cast to integer.
    -- 2. Duplicate rows with identical values — DISTINCT removes them.
    -- Season filter applied here so downstream CTEs never see other years.
    SELECT DISTINCT
        playerName,
        CAST(REPLACE(REPLACE(salary, ',', ''), '$', '') AS INTEGER) AS salary_int
    FROM salaries
    WHERE seasonStartYear = 2021
),
production AS (
    -- Composite production score per game.
    -- Covers all major positive contributions and subtracts turnovers.
    -- G >= 41 = at least half a season, avoids small-sample distortion.
    SELECT
        cs.Player,
        cs.Tm,
        cs.G,
        ROUND((cs.PTS + cs.TRB + cs.AST + cs.STL + cs.BLK - cs.TOV) / cs.G, 2) AS prod_per_game
    FROM clean_stats cs
    WHERE cs.Season = 2021
      AND cs.G >= 41
),
joined AS (
    SELECT
        p.Player,
        p.Tm,
        p.G,
        p.prod_per_game,
        ROUND(s.salary_int / 1000000.0, 2)                           AS salary_millions,
        -- Cost per production unit: lower = more value per dollar (underpaid).
        ROUND(s.salary_int / 1000000.0 / p.prod_per_game, 2)        AS cost_per_unit
    FROM production p
    JOIN clean_salaries s ON p.Player = s.playerName
    -- Exclude minimum-salary noise: very low salaries inflate the metric
    -- for players who happen to be cheap regardless of performance.
    WHERE s.salary_int > 1000000
      AND p.prod_per_game > 0
)
SELECT
    Player,
    Tm,
    G,
    prod_per_game,
    salary_millions,
    cost_per_unit,
    RANK() OVER (ORDER BY cost_per_unit ASC)  AS underpaid_rank,
    RANK() OVER (ORDER BY cost_per_unit DESC) AS overpaid_rank
FROM joined
ORDER BY cost_per_unit ASC;
""", conn)

conn.close()

# --- Scatter plot: salary vs production, coloured by cost efficiency ---

fig, ax = plt.subplots(figsize=(13, 8))

scatter = ax.scatter(
    df['salary_millions'],
    df['prod_per_game'],
    c=df['cost_per_unit'],
    cmap='RdYlGn_r',   # green = cheap (underpaid), red = expensive (overpaid)
    s=60,
    alpha=0.75
)

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('$ millions per production unit\n(lower = better value)', fontsize=10)

# Label the top 10 underpaid and top 5 overpaid players.
top_underpaid = df.nsmallest(10, 'cost_per_unit')
top_overpaid  = df.nlargest(5,  'cost_per_unit')
to_label = pd.concat([top_underpaid, top_overpaid]).drop_duplicates()

texts = []
for _, row in to_label.iterrows():
    t = ax.text(row['salary_millions'], row['prod_per_game'], row['Player'],
                fontsize=7, fontweight='bold')
    texts.append(t)

adjust_text(
    texts,
    ax=ax,
    arrowprops=dict(arrowstyle='-', color='gray', lw=0.5)
)

ax.set_title('Player Contribution relative to Salary: NBA 2021', fontsize=14)
ax.set_xlabel('Salary ($ millions)', fontsize=12)
ax.set_ylabel('Composite Production per Game\n(PTS + TRB + AST + STL + BLK − TOV)', fontsize=11)
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('$%.0fM'))

plt.tight_layout()
os.makedirs('images', exist_ok=True)
plt.savefig('images/value_for_money_2021.png', dpi=150, bbox_inches='tight')
plt.show()
