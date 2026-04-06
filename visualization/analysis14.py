"""
analysis14.py — Salary Curve by Age: when do players peak in pay vs. performance?

Aggregates all seasons where salary data exists (1990–2021) to compute the
average production score and average salary at each age, then indexes both
curves to their own peak (100 = peak age) so they can be compared on the
same axis.

Output: images/salary_curve_by_age.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

conn = sqlite3.connect('nba.db')

df = pd.read_sql_query("""
WITH clean_stats AS (
    -- Deduplicate traded players: keep the combined TOT row, drop individual team rows.
    -- The TOT row aggregates stats across all teams a player played for that season,
    -- so it correctly represents their full-season production.
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
    -- Strip "$" and "," from salary text, cast to integer, deduplicate.
    -- No season filter here — we keep all years (1990–2021) so the age
    -- aggregation in per_player covers the full salary history.
    SELECT DISTINCT
        playerName,
        seasonStartYear,
        CAST(REPLACE(REPLACE(salary, ',', ''), '$', '') AS INTEGER) AS salary_int
    FROM salaries
),
per_player AS (
    -- How clean_stats and clean_salaries are joined:
    --
    --   clean_stats  has one row per (Player, Season)  after deduplication.
    --   clean_salaries has one row per (playerName, seasonStartYear) after DISTINCT.
    --
    --   We join on BOTH columns:
    --       cs.Player = s.playerName        — same person
    --       cs.Season = s.seasonStartYear   — same season
    --
    --   Joining on player name alone would be wrong: a player's 2015 salary
    --   could attach to their 2021 stats row, inflating or deflating the age
    --   averages. The season key ensures each salary is matched to the exact
    --   season the stats were recorded in.
    SELECT
        cs.Age,
        (cs.PTS + cs.TRB + cs.AST + cs.STL + cs.BLK - cs.TOV) / cs.G AS prod_per_game,
        s.salary_int / 1000000.0                                        AS salary_millions
    FROM clean_stats cs
    JOIN clean_salaries s
        ON  cs.Player = s.playerName
        AND cs.Season = s.seasonStartYear
    WHERE cs.G           >= 20
      AND s.salary_int   >  1000000
      AND (cs.PTS + cs.TRB + cs.AST + cs.STL + cs.BLK - cs.TOV) / cs.G > 0
),
age_avgs AS (
    SELECT
        Age,
        COUNT(*)             AS num_players,
        AVG(prod_per_game)   AS avg_prod,
        AVG(salary_millions) AS avg_salary
    FROM per_player
    GROUP BY Age
)
SELECT
    Age,
    num_players,
    ROUND(avg_prod,   2) AS avg_prod,
    ROUND(avg_salary, 2) AS avg_salary_millions,
    -- Index both metrics to their own peak so they share the same 0-100 scale.
    -- 100 = the age at which this metric is highest; other ages are a % of that peak.
    -- This makes it possible to overlay production and salary on one axis and
    -- directly compare *when* each peaks, regardless of their different units.
    ROUND(avg_prod   / MAX(avg_prod)   OVER () * 100, 1) AS prod_index,
    ROUND(avg_salary / MAX(avg_salary) OVER () * 100, 1) AS salary_index
FROM age_avgs
WHERE Age BETWEEN 19 AND 38
ORDER BY Age;
""", conn)

conn.close()



# --- Dual-line chart: production index vs salary index by age ---

peak_prod_age   = int(df.loc[df['prod_index']   == df['prod_index'].max(),   'Age'].iloc[0])
peak_salary_age = int(df.loc[df['salary_index'] == df['salary_index'].max(), 'Age'].iloc[0])

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(df['Age'], df['prod_index'],   color='#2ecc71', linewidth=2.5, marker='o', markersize=4, label='Production Index')
ax.plot(df['Age'], df['salary_index'], color='#e74c3c', linewidth=2.5, marker='o', markersize=4, label='Salary Index')

# Mark each peak with a vertical dashed line.
ax.axvline(peak_prod_age,   color='#2ecc71', linestyle='--', linewidth=1.2,
           label=f'Production peak: age {peak_prod_age}')
ax.axvline(peak_salary_age, color='#e74c3c', linestyle='--', linewidth=1.2,
           label=f'Salary peak: age {peak_salary_age}')

# Shade the lag region between the two peaks.
if peak_salary_age > peak_prod_age:
    ax.axvspan(peak_prod_age, peak_salary_age, alpha=0.08, color='gray',
               label=f'Salary lag: {peak_salary_age - peak_prod_age} yr(s)')

ax.set_title('Average Salary vs Performance by Age: NBA(1990–2021)', fontsize=13)
ax.set_xlabel('Age', fontsize=11)
ax.set_ylabel('Index (100 = peak)', fontsize=11)
ax.set_xticks(df['Age'])
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
os.makedirs('images', exist_ok=True)
plt.savefig('images/salary_curve_by_age.png', dpi=150, bbox_inches='tight')
plt.show()
