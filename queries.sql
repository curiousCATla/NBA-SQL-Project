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

--Q6: Which players scored above the league average PPG in the 2022 season?

--Q7: For 2022, how did each player's season PPG average compare to their actual per-game PPG from boxscores?

--Q8: Who were the top 3 scorers on each team in the 2022 season?

--Q9: Which players improved their scoring average the most from 2021 to 2022?

--Q10: Which players were the most consistent scorers in 2022?
