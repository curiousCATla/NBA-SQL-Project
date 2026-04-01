# NBA Analytics Project

## Overview

This project explores 74 years of NBA history (1950–2023) using a SQLite database built from four Kaggle datasets. Using SQL embedded in Python, I queried the database to investigate league-wide scoring trends, individual player performance, rookie history, and year-over-year progression. Results are visualized using matplotlib and seaborn.

**Dataset Source:** [NBA Players and Team Data — Kaggle](https://www.kaggle.com/datasets/loganlauton/nba-players-and-team-data?resource=download&select=NBA+Player+Stats%281950+-+2022%29.csv)  
**Data sourced from:** Basketball Reference (player stats) · Hoops Hype (salaries & payroll)

---

## Technical Stack

### SQL Techniques

All queries are written in SQLite and executed via `pd.read_sql_query()`. Key techniques used:

| Technique | Where Used |
|-----------|------------|
| **Common Table Expressions (CTEs)** | Multi-step queries in analyses 3–9 — chains `clean_stats → player_avg → ranked output` |
| **Window Functions** — `RANK() OVER (PARTITION BY ...)` | Rookie scoring leaders (analysis 6) — ranks rookies within each season |
| **Window Functions** — `PERCENT_RANK() OVER (ORDER BY ...)` | Player comparison tool (analysis 7) — computes percentile rank for each stat |
| **`CASE WHEN`** | Scoring tier classification (analysis 5) — buckets PPG into 5 tiers |
| **`NOT EXISTS` subquery** | TOT deduplication — removes duplicate rows for traded players |
| **`UNION ALL`** | TOT deduplication — reconstructs a clean, deduplicated dataset |
| **Multi-table `JOIN`** | Year-over-year improvement (analysis 9) — joins 2021 and 2022 seasons on player name |
| **`HAVING`** | Consistent scorers (analysis 4) — filters groups with 5+ qualifying seasons |
| **Computed columns** | Per-game stats calculated inline: `ROUND(PTS * 1.0 / G, 1) AS PPG` |

**TOT Deduplication Pattern** — used in 6 of 8 analyses to handle players traded mid-season (who appear once per team plus a combined `TOT` row):

```sql
WITH clean_stats AS (
    SELECT * FROM player_stats WHERE Tm = 'TOT'        -- keep the combined row
    UNION ALL
    SELECT * FROM player_stats                          -- keep single-team players
    WHERE NOT EXISTS (
        SELECT 1 FROM player_stats p2
        WHERE p2.Player = player_stats.Player
          AND p2.Season = player_stats.Season
          AND p2.Tm = 'TOT'                             -- only if no TOT row exists
    )
)
```

---

### Python Techniques

| Technique | Library | Where Used |
|-----------|---------|------------|
| SQL → DataFrame bridge | `pandas.read_sql_query()` | All analysis scripts |
| Label overlap prevention | `adjustText.adjust_text()` | Scatter plots with player name labels |
| Unicode normalization | `unicodedata.normalize('NFKD', ...)` | Player name input — handles accented names like "Dončić" → "doncic" |
| Fuzzy string matching | `difflib.get_close_matches()` | Suggests closest player name on typo |
| Polar/radar chart | `matplotlib` with `subplot_kw=dict(polar=True)` | Multi-player percentile comparison |
| Multi-panel subplots | `matplotlib.pyplot.subplots(2, 3)` | Career progression tool |
| Seaborn themes | `seaborn` | Consistent styling across all charts |

---

## Database Schema

The SQLite database (`nba.db`, ~137 MB) contains four tables:

| Table | Description | Rows (approx.) |
|-------|-------------|----------------|
| `player_stats` | Seasonal aggregates per player (1950–2023) | ~30,000 |
| `player_boxscores` | Game-by-game stat lines per player | ~650,000 |
| `salaries` | Individual player salaries with inflation adjustment | ~17,000 |
| `payroll` | Team-level seasonal payroll | ~800 |

---

## Project Structure

```
NBA_SQL/
├── load_data.py          # Loads CSV files into nba.db via pandas + sqlite3
├── analysis.py           # Q1–Q2: Top scorers, PPG vs APG scatter
├── analysis3.py          # Q3: League-wide PPG trend (1950–2023)
├── analysis4.py          # Q4: Players with 5+ seasons of 20+ PPG
├── analysis5.py          # Q5: Scoring tier distribution in 2022
├── analysis6.py          # Q6: Rookie scoring leaders by year since 1953
├── analysis7.py          # Q7: Interactive multi-player radar chart (2022 percentiles)
├── analysis9.py          # Q9: Most improved scorers from 2021 to 2022
├── player_prog.py        # Interactive career progression tool (6-panel chart)
├── data/                 # Source CSV files
├── images/               # Saved visualizations
└── nba.db                # SQLite database
```

---

## Setup & Installation

```bash
# Install dependencies
pip install pandas matplotlib seaborn adjustText

# Build the database from CSV files
python load_data.py

# Run any analysis (example)
python analysis3.py
```

---

## Analyses

### Q1 · Top 10 Single-Season Scorers of All Time

Query orders all seasons by total points per game and returns the top 10.

```sql
SELECT Player, Season, Tm, PTS
FROM player_stats
ORDER BY PTS DESC
LIMIT 10;
```

![Top 10 Single-Season Scorers](images/top_10_scorers.png)

---

### Q2 · Players Averaging 25+ PPG and 7+ APG in a Single Season

Computed columns calculate per-game averages inline. `adjustText` prevents label overlap on the scatter plot.

```sql
SELECT Player, Season, Tm,
    ROUND(PTS * 1.0 / G, 1) AS PPG,
    ROUND(AST * 1.0 / G, 1) AS APG
FROM player_stats
WHERE PPG >= 25 AND APG >= 7 AND G >= 41
ORDER BY PPG DESC;
```

![PPG vs APG Scatter](images/ppg_vs_apg_scatter.png)

**Finding:** Only a handful of players in NBA history have simultaneously dominated in both scoring and playmaking — Oscar Robertson, Magic Johnson, and LeBron James appear most frequently.

---

### Q3 · League-Wide Average PPG Trend (1950–2023)

A two-step CTE first deduplicates traded players, then averages PPG per season across the full league.

```sql
WITH clean_stats AS ( ... ),   -- deduplicate TOT rows
     player_avg AS (
         SELECT Season, Player, ROUND(PTS / G, 2) AS PPG
         FROM clean_stats WHERE G >= 1
     )
SELECT Season, AVG(PPG) AS avg_PPG, COUNT(*) AS player_count
FROM player_avg
GROUP BY Season ORDER BY Season;
```

![Average PPG by Season](images/avg_ppg_by_season.png)

**Finding:** League scoring peaked in the early 1960s, dipped significantly through the defensive era of the 1990s–2000s, and has risen sharply again in the modern three-point era.

---

### Q4 · Players with 5+ Seasons Averaging 20+ PPG

`HAVING` filters groups after aggregation — only players whose count of qualifying seasons meets the threshold survive.

```sql
SELECT Player,
    COUNT(Season)      AS seasons_above_20,
    ROUND(AVG(PPG), 1) AS avg_ppg_in_those_seasons
FROM player_avg
WHERE PPG >= 20
GROUP BY Player
HAVING COUNT(Season) >= 5
ORDER BY seasons_above_20 DESC;
```

![Seasons Above 20 PPG](images/seasons_above_20.png)

---

### Q5 · Scoring Tier Distribution in 2022

`CASE WHEN` classifies each player into one of five scoring tiers based on their per-game average.

```sql
CASE
    WHEN PPG >= 25 THEN 'Elite (25+)'
    WHEN PPG >= 20 THEN 'Star (20–24)'
    WHEN PPG >= 15 THEN 'Starter (15–19)'
    WHEN PPG >= 10 THEN 'Role Player (10–14)'
    ELSE                'Bench (< 10)'
END AS scoring_tier
```

![Scoring Tiers 2022](images/scoring_tiers_2022.png)

---

### Q6 · Highest-Scoring Rookie Each Year Since 1953

A four-step CTE chain: deduplicate → identify each player's first season → join back for rookie stats → `RANK()` within each season to find the top scorer.

```sql
WITH clean_stats AS ( ... ),
     rookie_year   AS (SELECT Player, MIN(Season) AS rookie_season FROM player_stats GROUP BY Player),
     rookie_stats  AS (SELECT cs.Player, cs.Season, ROUND(cs.PTS / cs.G, 2) AS PPG
                       FROM clean_stats cs JOIN rookie_year ry
                       ON cs.Player = ry.Player AND cs.Season = ry.rookie_season
                       WHERE cs.G >= 20),
     ranked_rookies AS (
         SELECT *, RANK() OVER (PARTITION BY Season ORDER BY PPG DESC) AS ppg_rank
         FROM rookie_stats
     )
SELECT Player, Season, PPG FROM ranked_rookies WHERE ppg_rank = 1 AND Season >= 1953;
```

![Rookie PPG by Season](images/highest_rookie_ppg_by_season.png)

---

### Q7 · Interactive Player Comparison — Percentile Radar Chart

`PERCENT_RANK()` window functions compute each player's league-wide percentile rank across five stats simultaneously. The radar chart is drawn using matplotlib's polar projection.

```sql
SELECT Player,
    ROUND(PERCENT_RANK() OVER (ORDER BY PPG) * 100, 1) AS pts_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY APG) * 100, 1) AS ast_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY RPG) * 100, 1) AS reb_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY SPG) * 100, 1) AS stl_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY BPG) * 100, 1) AS blk_percentile
FROM league_2022;
```

**Interactive features:**
- Comma-separated input accepts multiple player names
- `unicodedata.normalize()` maps accented names (e.g. `Dončić`) to plain ASCII input
- `difflib.get_close_matches()` suggests the closest match on typos with a yes/no/stop prompt

---

### Q9 · Most Improved Scorers from 2021 to 2022

Three CTEs isolate each season's data, then a `JOIN` on player name links a player's 2021 and 2022 stats to compute the improvement delta.

```sql
WITH season_2021 AS (SELECT Player, ROUND(PTS * 1.0 / G, 1) AS PPG_2021 FROM clean_stats WHERE Season = 2021 AND G >= 20),
     season_2022 AS (SELECT Player, Tm, ROUND(PTS * 1.0 / G, 1) AS PPG_2022 FROM clean_stats WHERE Season = 2022 AND G >= 20),
     combined    AS (SELECT s22.Player, s21.PPG_2021, s22.PPG_2022,
                            ROUND(s22.PPG_2022 - s21.PPG_2021, 1) AS improvement
                     FROM season_2022 s22 JOIN season_2021 s21 ON s22.Player = s21.Player)
SELECT * FROM combined ORDER BY improvement DESC LIMIT 10;
```

---

## Interactive Tool — Career Progression (`player_prog.py`)

Visualizes any player's career arc across six dimensions in a single 2×3 grid.

```bash
python player_prog.py
# Enter player name: michael jrdan
# → 'michael jrdan' not found. Did you mean 'Michael Jordan'? (yes/no/stop): yes
```

- Pulls all career seasons via the `clean_stats` CTE
- Per-game stats (PPG, APG, RPG, SPG, BPG) computed per season
- 6th panel shows games played as a bar chart to contextualize injury seasons

---

## Key Findings

- **Wilt Chamberlain** holds the all-time single-season scoring record at **50.4 PPG** (1961–62), nearly 10 points ahead of anyone else in history.
- Only **~4% of NBA players** in 2022 qualified as "Elite" scorers (25+ PPG); over half fell into the "Bench" tier.
- League-wide scoring has returned to 1960s levels after a defensive valley spanning roughly 1994–2010.
- The **modern three-point era** has produced some of the highest-scoring rookie classes since the 1960s.
- Fewer than 15 players in the dataset have ever averaged 20+ PPG in 5 or more seasons.

---

## Potential Extensions

- **Salary efficiency** — JOIN `player_stats` with `salaries` to rank players by PPG per $1M
- **Hot streak analysis** — Use the `player_boxscores` table to find the longest consecutive 20+ point games
- **Team payroll vs. win rate** — Correlate team spending with win percentage across seasons
- **Streamlit dashboard** — Deploy analyses as an interactive web app
