--Q1: Who were the top 10 single-season scorers of all time?
SELECT
	Player,
	Season,
	Tm,
	PTS
FROM player_stats
ORDER BY PTS DESC
LIMIT 10;
--Q2: Which players averaged 25+ PPG and 7+ AST in the same season?
SELECT 
Player, 
Season, 
Tm,
PTS/G AS PPG, 
AST/G AS APG
FROM player_stats
WHERE PPG >= 25  AND APG >= 7 AND G >= 41
--An NBA season has 82 games, setting a minimum on the number of games played (G >= 41), filters outliers
ORDER BY PPG DESC
LIMIT 30

--Q3: How has the league-wide average points per game changed each season?
  WITH clean_stats AS ( --The WITH notation can only be used once in a SQL
      SELECT * FROM player_stats WHERE Tm = 'TOT'
      UNION ALL
      SELECT *  FROM player_stats
      WHERE NOT EXISTS (
          SELECT 1 FROM player_stats p2
          WHERE p2.Player = player_stats.Player
            AND p2.Season = player_stats.Season
            AND p2.Tm = 'TOT'
      )
  ), --When a player gets traded in the middle of the season, there will be repeated row entries of the same player in their initial team, final team, and total
	--The clean_stats CTE removes the duplicated rows and only keeps the total if a player gets traded in the season and played on both teams
 player_avg AS ( --The second CTE does not require the WITH notation, but a "," to separate the two CTEs
	SELECT Season, Player, ROUND(PTS/G, 2) AS PPG, G
	FROM clean_stats
	WHERE G >= 1
  )
--The second finds PPG but also filters out any null entry/ when a player did not play that season 
SELECT 
Season, AVG(PPG) AS avg_PPG, COUNT(*) AS player_count, AVG(G) AS avg_GP
--In addition to average points per game, I also include the player count and the average number of games players play 
FROM player_avg
GROUP BY Season
ORDER BY Season;

--Q4: Which players have averaged 20+ PPG in at least 5 different seasons?
--There has been a total of 121 players in the history of the NBA who have averaged above 20+ PPG in at least 5 different seasons, with LeBron James at the top of the list with a total of 19 seasons
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

--Q5: How many players fall into each scoring tier per season in 2022?

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
player_tier_2022 AS (
    SELECT
        Player,
        Tm,
        CAST(PTS AS FLOAT) / G AS PPG,
        CASE
            WHEN CAST(PTS AS FLOAT) / G >= 25 THEN 'Elite (25+)'
            WHEN CAST(PTS AS FLOAT) / G >= 20 THEN 'Star (20-24)'
            WHEN CAST(PTS AS FLOAT) / G >= 15 THEN 'Starter (15-19)'
            WHEN CAST(PTS AS FLOAT) / G >= 10 THEN 'Role Player (10-14)'
            ELSE 'Bench (< 10)'
        END AS scoring_tier
	  -- using 'CASE WHEN' to define scoring tiers, and categorize each player 
    FROM clean_stats
    WHERE Season = 2022
      AND G >= 1
)
SELECT
    scoring_tier,
    COUNT(*) AS num_players
FROM player_tier_2022
GROUP BY scoring_tier
ORDER BY MIN(PPG) DESC;
-- using MIN(PPG) ensure the table is ordered from the highest scoring tier to the lowest

--Q6: Who are the leading scoring rookies each year in the NBA since the 1953 season, and what is their average PPG?

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
  rookie_year AS (
      SELECT Player, MIN(Season) AS rookie_season
      FROM player_stats
      GROUP BY Player
	  --By only considering 2 columns, it makes the SQL more efficient
  ),
  rookie_stats AS (
      SELECT cs.Player, cs.Season, cs.Tm, cs.G,
             ROUND(cs.PTS  / cs.G, 2) AS PPG
      FROM clean_stats cs
      JOIN rookie_year ry
          ON cs.Player = ry.Player
         AND cs.Season = ry.rookie_season
	  --Using 2 distinct parameters for JOIN to find the player's rookie stats
      WHERE cs.G >= 20
  ),
  ranked_rookies AS (
      SELECT *,
             RANK() OVER (PARTITION BY Season ORDER BY PPG DESC) AS ppg_rank
	  --Using a partition to compare each player's rookie season, and finding the rookie with the highest points per game. 
      FROM rookie_stats
  )
  SELECT Player, Season, Tm, G, PPG
  FROM ranked_rookies
  WHERE ppg_rank = 1
    AND Season >= 1953
  ORDER BY Season;

--Q7: What are each player's scoring, assist, and rebound percentages relative to the rest of the league in the 2022 season?

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
          ROUND(TRB * 1.0 / G, 1) AS RPG                                                                                                           
      FROM clean_stats                                                                                                                             
      WHERE Season = 2022 AND G >= 20
)
SELECT 
	Player, Player, Tm, G, PPG, APG, RPG, 
	ROUND(PERCENT_RANK() OVER (ORDER BY PPG) * 100, 1) AS pts_percentile,
    ROUND(PERCENT_RANK() OVER (ORDER BY APG) * 100, 1) AS ast_percentile,                                                                    
    ROUND(PERCENT_RANK() OVER (ORDER BY RPG) * 100, 1) AS reb_percentile 
-- the 'PERCENT_RANK() OVER(ORDER BY)' window function ranks calculates the relative percentile rank of a row within this set of data 
FROM league_2022
ORDER BY pts_percentile DESC;  

--Q8: Who were the top 3 scorers on each team in the 2022 season?

 WITH league_2022 AS (
      SELECT
          Player, Tm, G,PTS, 
			RANK() OVER (PARTITION BY Tm ORDER BY PTS DESC) AS team_ranking
      FROM player_stats                                                                                                                        
      WHERE Season = 2022
	  AND G>=1
)
SELECT
	Tm, team_ranking,
	Player, PTS, G 
	FROM league_2022
	WHERE team_ranking <= 3
	--I notice that the WHERE condition requires the team_ranking to be calculated from the input table, therefore, I had to move it inside the CTE 
	ORDER BY Tm, team_ranking;

--Q9: Which players improved their scoring average the most from 2021 to 2022?

--Q10: Which players were the most consistent scorers in 2022?
