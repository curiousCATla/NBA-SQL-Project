"""
analysis13.py — Position Premium: which positions are over/undervalued by the market (2021 season).

For each primary position (PG, SG, SF, PF, C), computes average salary and average
composite production, then derives a position_premium score:
    (position's salary share) / (position's production share)
Values above 1.0 = market overpays this position relative to output.
Values below 1.0 = market underpays this position relative to output.

Output: images/position_premium_2021.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

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
    -- Strip "$" and "," from salary text, cast to integer, deduplicate, filter to 2021.
    SELECT DISTINCT
        playerName,
        CAST(REPLACE(REPLACE(salary, ',', ''), '$', '') AS INTEGER) AS salary_int
    FROM salaries
    WHERE seasonStartYear = 2021
),
per_player AS (
    SELECT
        -- Extract primary position: "SF-PF" -> "SF", "C-PF" -> "C", etc.
        SUBSTR(cs.Pos, 1, INSTR(cs.Pos || '-', '-') - 1)              AS position,
        (cs.PTS + cs.TRB + cs.AST + cs.STL + cs.BLK - cs.TOV) / cs.G AS prod_per_game,
        s.salary_int / 1000000.0                                       AS salary_millions
    FROM clean_stats cs
    JOIN clean_salaries s ON cs.Player = s.playerName
    WHERE cs.Season      = 2021
      AND cs.G           >= 41
      AND s.salary_int   > 1000000
      AND (cs.PTS + cs.TRB + cs.AST + cs.STL + cs.BLK - cs.TOV) / cs.G > 0
),
position_avgs AS (
    SELECT
        position,
        COUNT(*)             AS num_players,
        AVG(prod_per_game)   AS avg_prod,
        AVG(salary_millions) AS avg_salary
    FROM per_player
    GROUP BY position
)
SELECT
    position,
    num_players,
    ROUND(avg_prod,   2) AS avg_prod,
    ROUND(avg_salary, 2) AS avg_salary_millions,
    -- premium = (this position's share of total salary)
    --         / (this position's share of total production)
    -- Window functions compute grand totals in one pass — no subquery needed.
    ROUND(
        (avg_salary / SUM(avg_salary) OVER ()) /
        (avg_prod   / SUM(avg_prod)   OVER ()),
    2) AS position_premium
FROM position_avgs
ORDER BY position_premium DESC;
""", conn)

conn.close()

# --- Bar chart: position premium ---

# Red if premium > 1 (overpaid), green if <= 1 (underpaid).
colors = ['#e05c5c' if p > 1 else '#5cb85c' for p in df['position_premium']]

fig, ax = plt.subplots(figsize=(9, 6))

bars = ax.bar(df['position'], df['position_premium'], color=colors, edgecolor='white', width=0.5)

# Reference line at 1.0 = fairly paid.
ax.axhline(1.0, color='black', linewidth=1.2, linestyle='--', label='Fairly valued (1.0)')

# Annotate each bar with its premium value and player count.
for bar, (_, row) in zip(bars, df.iterrows()):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.01,
        f"{row['position_premium']:.2f}\n(n={int(row['num_players'])})",
        ha='center', va='bottom', fontsize=9, fontweight='bold'
    )

ax.set_title('Position Premium: Salary Share vs Production Share: NBA 2021', fontsize=13)
ax.set_xlabel('Primary Position', fontsize=11)
ax.set_ylabel('Position Premium\n(>1 = overpaid, <1 = underpaid)', fontsize=11)
ax.set_ylim(0, df['position_premium'].max() + 0.2)
ax.legend(fontsize=10)

plt.tight_layout()
os.makedirs('images', exist_ok=True)
plt.savefig('images/position_premium_2021.png', dpi=150, bbox_inches='tight')
plt.show()
