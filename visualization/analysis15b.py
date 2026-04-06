"""
analysis15b.py — Injury/Availability Tax using inflation-adjusted salaries.

Identical structure to analysis15.py but uses inflationAdjSalary (all values
expressed in 2021 dollars) so contracts across different eras are comparable.

Two SQL queries:
  1. per_player  — one row per (player, season) with inflation-adj salary wasted.
  2. per_season  — league-wide availability rate and player count per season.

Three visualisations (one figure, three panels):
  Panel 1 (top-left)  : Bar chart — top 10 player-seasons by inflation-adj salary wasted.
  Panel 2 (top-right) : Scatter plot — availability vs inflation-adj salary for those 10.
  Panel 3 (bottom)    : Dual-axis line — avg availability rate (left) and
                        number of qualifying players (right) by season.

Output: images/availability_tax_inflation_adj.png
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

conn = sqlite3.connect('nba.db')

# ── Query 1: per-player availability tax (inflation-adjusted) ─────────────────
#
# clean_stats and clean_salaries are joined on BOTH player name AND season:
#   cs.Player = s.playerName      → same person
#   cs.Season = s.seasonStartYear → same season
#
# Joining on name alone would be wrong across multiple seasons: a player's
# 2010 salary could attach to their 2020 stats row, corrupting every metric.
# The season key pins each salary to the exact year the stats were recorded.

df_players = pd.read_sql_query("""
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
clean_salaries AS (
    SELECT DISTINCT
        playerName,
        seasonStartYear,
        CAST(REPLACE(REPLACE(inflationAdjSalary, ',', ''), '$', '') AS INTEGER) AS salary_int
    FROM salaries
),
per_player AS (
    SELECT
        cs.Player,
        cs.Season,
        CAST(cs.G AS INTEGER)                                            AS Games,
        ROUND(cs.G / 82.0, 3)                                           AS availability_rate,
        ROUND(s.salary_int / 1000000.0, 2)                             AS salary_millions,
        ROUND(s.salary_int / 1000000.0 / cs.G, 3)                     AS cost_per_game_m,
        -- Inflation-adj salary attributed to missed games:
        --   (salary / 82) = prorated cost per game slot
        --   * (82 - G)    = number of slots the player missed
        --   = salary * (1 - G/82)
        ROUND(s.salary_int / 1000000.0 * (1.0 - cs.G / 82.0), 2)     AS salary_wasted_m
    FROM clean_stats cs
    JOIN clean_salaries s
        ON  cs.Player = s.playerName
        AND cs.Season = s.seasonStartYear
    WHERE s.salary_int > 5000000
      AND cs.G         < 82
)
SELECT Player, Season, Games, availability_rate, salary_millions,
       cost_per_game_m, salary_wasted_m
FROM per_player
ORDER BY salary_wasted_m DESC;
""", conn)

# ── Query 2: league-wide availability by season (inflation-adjusted) ──────────

df_season = pd.read_sql_query("""
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
clean_salaries AS (
    SELECT DISTINCT
        playerName,
        seasonStartYear,
        CAST(REPLACE(REPLACE(inflationAdjSalary, ',', ''), '$', '') AS INTEGER) AS salary_int
    FROM salaries
),
-- Rank each player's inflation-adj salary within their season so the
-- filter is relative (above median) rather than a fixed dollar threshold.
salary_pct AS (
    SELECT
        playerName,
        seasonStartYear,
        salary_int,
        PERCENT_RANK() OVER (
            PARTITION BY seasonStartYear
            ORDER BY salary_int
        ) AS salary_percentile
    FROM clean_salaries
)
SELECT
    cs.Season,
    COUNT(*)                   AS num_players,
    ROUND(AVG(cs.G / 82.0), 3) AS avg_availability
FROM clean_stats cs
JOIN salary_pct s
    ON  cs.Player = s.playerName
    AND cs.Season = s.seasonStartYear
WHERE s.salary_percentile >= 0.5   -- top 50% earners each season
GROUP BY cs.Season
ORDER BY cs.Season;
""", conn)

conn.close()

top10 = df_players.head(10).copy()
top10['label'] = top10['Player'] + '\n(' + top10['Season'].astype(str) + ')'

# ── Figure layout: 2 rows, 2 columns; bottom panel spans both columns ─────────

fig = plt.figure(figsize=(16, 14))
ax_bar     = fig.add_subplot(2, 2, 1)
ax_scatter = fig.add_subplot(2, 2, 2)
ax_line    = fig.add_subplot(2, 1, 2)

# ── Panel 1: Bar chart — top 10 inflation-adj salary wasted ──────────────────

bars = ax_bar.barh(top10['label'], top10['salary_wasted_m'],
                   color='#e05c5c', edgecolor='white')
ax_bar.invert_yaxis()
ax_bar.set_xlabel('Inflation-Adj. Salary Wasted ($M, 2021 dollars)', fontsize=10)
ax_bar.set_title('Top 10 Player-Seasons: Inflation-Adj. Salary Paid for Missed Games', fontsize=11)

for bar, (_, row) in zip(bars, top10.iterrows()):
    ax_bar.text(
        bar.get_width() + 0.2,
        bar.get_y() + bar.get_height() / 2,
        f"${row['salary_wasted_m']:.1f}M  ({row['Games']} Games)",
        va='center', fontsize=8
    )

ax_bar.set_xlim(0, top10['salary_wasted_m'].max() + 5)

# ── Panel 2: Scatter — availability vs inflation-adj salary, top 10 ──────────

scatter = ax_scatter.scatter(
    top10['availability_rate'],
    top10['salary_millions'],
    s=top10['salary_wasted_m'] * 20,
    c=top10['salary_wasted_m'],
    cmap='Reds',
    alpha=0.8,
    edgecolors='gray',
    linewidths=0.5
)

cbar = plt.colorbar(scatter, ax=ax_scatter)
cbar.set_label('Inflation-Adj. Salary Wasted ($M)', fontsize=9)

for _, row in top10.iterrows():
    ax_scatter.annotate(
        row['Player'].split(' ')[-1],
        (row['availability_rate'], row['salary_millions']),
        textcoords='offset points', xytext=(6, 4), fontsize=8
    )

ax_scatter.set_xlabel('Availability Rate (Games / 82)', fontsize=10)
ax_scatter.set_ylabel('Inflation-Adj. Salary ($M, 2021 dollars)', fontsize=10)
ax_scatter.set_title('Top 10: Availability Rate vs Inflation-Adj. Salary\n(bubble size = salary wasted)', fontsize=11)
ax_scatter.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))

# ── Panel 3: Dual-axis line — avg availability + player count by season ───────

ax_count = ax_line.twinx()

ax_line.plot(df_season['Season'], df_season['avg_availability'],
             color='#3498db', linewidth=2.5, marker='o', markersize=4,
             label='Avg Availability Rate')
ax_count.plot(df_season['Season'], df_season['num_players'],
              color='#f39c12', linewidth=2, linestyle='--', marker='s', markersize=4,
              label='No. of Qualifying Players')

ax_line.set_xlabel('Season', fontsize=10)
ax_line.set_ylabel('Avg Availability Rate', fontsize=10, color='#3498db')
ax_count.set_ylabel('No. of Qualifying Players (above median salary each season)', fontsize=10, color='#f39c12')
ax_line.set_title('League-Wide Availability Rate & Player Count by Season (1990–2021)', fontsize=11)
ax_line.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
ax_line.tick_params(axis='y', labelcolor='#3498db')
ax_count.tick_params(axis='y', labelcolor='#f39c12')
ax_line.grid(axis='y', linestyle='--', alpha=0.4)

lines_a, labels_a = ax_line.get_legend_handles_labels()
lines_b, labels_b = ax_count.get_legend_handles_labels()
ax_line.legend(lines_a + lines_b, labels_a + labels_b, fontsize=10, loc='lower left')

plt.suptitle('NBA Injury / Availability Tax — Inflation-Adjusted (1990–2021)',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
os.makedirs('images', exist_ok=True)
plt.savefig('images/availability_tax_inflation_adj.png', dpi=150, bbox_inches='tight')
plt.show()
