import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import numpy as np
from utils import build_name_map, lookup_player

conn = sqlite3.connect('nba.db')

# Pull career stats for all players, one row per (player, season), using TOT for traded seasons
career_stats = pd.read_sql_query("""
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
    )
    SELECT
        Player,
        Season,
        G,
        ROUND(PTS * 1.0 / G, 1) AS PPG,
        ROUND(AST * 1.0 / G, 1) AS APG,
        ROUND(TRB * 1.0 / G, 1) AS RPG,
        ROUND(STL * 1.0 / G, 1) AS SPG,
        ROUND(BLK * 1.0 / G, 1) AS BPG
    FROM clean_stats
    WHERE G >= 1
    ORDER BY Player, Season
""", conn)

name_map = build_name_map(career_stats['Player'].unique())

# --- Input loop ---
player_name = input("Enter player name: ").strip()
canonical = lookup_player(player_name, name_map)
if not canonical:
    print("No player selected. Exiting.")
    exit()

player_data = career_stats[career_stats['Player'] == canonical].sort_values('Season')

if player_data.empty:
    print(f"No data found for '{canonical}'.")
    exit()

# --- Plot career progression ---
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
fig.suptitle(f"{canonical} — Career Progression", fontsize=15, fontweight='bold')

stats = [
    ('PPG', 'Points per Game', 'steelblue'),
    ('APG', 'Assists per Game', 'seagreen'),
    ('RPG', 'Rebounds per Game', 'darkorange'),
    ('SPG', 'Steals per Game', 'mediumpurple'),
    ('BPG', 'Blocks per Game', 'crimson'),
]

seasons = player_data['Season'].tolist()

for ax, (col, label, color) in zip(axes.flat, stats):
    ax.plot(seasons, player_data[col], marker='o', color=color, linewidth=2)
    ax.set_title(label)
    ax.set_xlabel('Season')
    ax.set_ylabel(label)
    ax.set_xticks(seasons)
    ax.set_xticklabels(seasons, rotation=45, fontsize=7)
    ax.grid(True, alpha=0.3)

# Use the last subplot for games played
ax = axes.flat[5]
ax.bar(seasons, player_data['G'], color='slategray', alpha=0.7)
ax.set_title('Games Played')
ax.set_xlabel('Season')
ax.set_ylabel('G')
ax.set_xticks(seasons)
ax.set_xticklabels(seasons, rotation=45, fontsize=7)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()
