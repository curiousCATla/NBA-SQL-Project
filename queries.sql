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

--Q4: Which players have averaged 20+ PPG in at least 5 different seasons?

--Q5: How many players fall into each scoring tier per season in 2022?

--Q6: Which players scored above the league average PPG in the 2022 season?

--Q7: For 2022, how did each player's season PPG average compare to their actual per-game PPG from boxscores?

--Q8: Who were the top 3 scorers on each team in the 2022 season?

--Q9: Which players improved their scoring average the most from 2021 to 2022?

--Q10: Which players were the most consistent scorers in 2022?
