# 7. Player Comparison Tool
# This script allows users to input player names and generates a radar chart comparing their percentile ranks in key stats for the 2022 season. 
# The input is a comma-separated list of player names, and the output is a radar chart visualizing how each player ranks in points, assists, rebounds, steals, and blocks compared to their peers in the 2022 season.
# 7. Player Comparison Tool
# This script allows users to input player names and generates a radar chart comparing their percentile ranks in key stats for the 2022 season. 
# The input is a comma-separated list of player names, and the output is a radar chart visualizing how each player ranks in points, assists, rebounds, steals, and blocks compared to their peers in the 2022 season.
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sqlite3
from adjustText import adjust_text
import numpy as np
import unicodedata
import difflib
conn = sqlite3.connect('nba.db')
q6 = pd.read_sql_query("""

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
league_2022 AS (
      SELECT
          Player, Tm, G,
          ROUND(PTS * 1.0 / G, 1) AS PPG,                                                                                                          
          ROUND(AST * 1.0 / G, 1) AS APG,
          ROUND(TRB * 1.0 / G, 1) AS RPG,      
          ROUND(STL * 1.0 / G, 1) AS SPG,
          ROUND(BLK * 1.0 / G, 1) AS BPG                                                                                                                  
      FROM clean_stats                                                                                                                             
      WHERE Season = 2022 AND G >= 20
)
SELECT 
    Player, Tm, G, PPG, APG, RPG, 
	ROUND(PERCENT_RANK() OVER (ORDER BY PPG) * 100, 1) AS pts_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY APG) * 100, 1) AS ast_percentile,                                                                    
    ROUND(PERCENT_RANK() OVER (ORDER BY RPG) * 100, 1) AS reb_percentile, 
    ROUND(PERCENT_RANK() OVER (ORDER BY SPG) * 100, 1) AS stl_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY BPG) * 100, 1) AS blk_percentile
-- the 'PERCENT_RANK() OVER(ORDER BY)' window function ranks calculates the relative percentile rank of a row within this set of data 
FROM league_2022
ORDER BY pts_percentile DESC;

""",conn) # dataframe with player stats and their percentile ranks in points, assists, rebounds, steals, and blocks for the 2022 season.

def normalize(name):
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()
# unicodedata.normalize('NFKD') decomposes accented characters (e.g. č → c + accent mark)
# .encode('ascii', 'ignore') drops the accent marks, .decode('ascii') converts back to a string
# so "Dončić" → "doncic", allowing plain English keyboard input to match accented names

name_map = {normalize(p): p for p in q6['Player']}  # maps normalized name → original name

raw_input = input("Enter player names (comma-separated): ").strip()
player_names = [name.strip() for name in raw_input.split(',')]

players = []
for name in player_names:
    current_name = name
    # Outer loop: retries the full lookup whenever the user re-enters a name after typing 'no'.
    # Breaks out only when a player is successfully matched and appended.
    while True:
        match = name_map.get(normalize(current_name))
        if match:
            players.append(q6[q6['Player'] == match].iloc[0])
            break

        suggestions = difflib.get_close_matches(normalize(current_name), name_map.keys(), n=1, cutoff=0.6)
        if suggestions:
            closest = name_map[suggestions[0]]
            # Inner loop: retries only the yes/no prompt until a valid answer is given.
            # Breaks out on 'yes' or 'no'; exits the script on 'stop'.
            while True:
                answer = input(f"'{current_name}' not found. Did you mean '{closest}'? (yes/no/stop): ").strip().lower()
                if answer == 'yes':
                    players.append(q6[q6['Player'] == closest].iloc[0])
                    break
                elif answer == 'no':
                    current_name = input("Re-enter player name: ").strip()
                    break
                elif answer == 'stop':
                    exit()
                else:
                    print("Please type yes, no, or stop.")
            if answer == 'yes':
                break
        else:
            print(f"'{current_name}' not found and no close matches.")
            current_name = input("Re-enter player name (or type 'stop'): ").strip()
            if current_name.lower() == 'stop':
                exit()

if not players:
    print("No valid players found.")
    exit()

categories = ['PTS', 'AST', 'REB', 'STL', 'BLK']
N = len(categories)
angles = [n / N * 2 * np.pi for n in range(N)]
angles += angles[:1]   # close the loop

fig, ax = plt.subplots(subplot_kw=dict(polar=True))
ax.set_theta_offset(np.pi / 2)
# the ax.set_theta_offset(np.pi / 2) rotates the plot so that the first category (PTS) starts at the top of the circle, which is a common convention for radar charts.

for row in players:
    values = [
        row['pts_percentile'],
        row['ast_percentile'],
        row['reb_percentile'],
        row['stl_percentile'],
        row['blk_percentile'],
    ]
    values += values[:1]
    ax.plot(angles, values, linewidth=2, label=row['Player'])
    ax.fill(angles, values, alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
ax.set_ylim(0, 100)
ax.set_yticks([25, 50, 75, 100])
ax.set_yticklabels(['25th', '50th', '75th', '100th'], fontsize=7)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

names_str = ', '.join(row['Player'] for row in players)
ax.set_title(f"{names_str} — 2022 Percentile Ranks", pad=15)
plt.tight_layout()
plt.show()

