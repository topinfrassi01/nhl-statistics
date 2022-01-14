# nhl-statistics
Pet project using NHL data to try to make me not ashamed of my pool's performance

The goal of this project is to try my hand at creating tools to help me build my NHL pools.

The first idea I had is to predict future points by looking at players that had similar consecutive N seasons and look at their N+1 point total.

In order to find comparable players, I compile sequences of N years for each player, keeping only a subset of statistics and use `KNearestNeighbors` to find players with similar statistics over N years. I then use `LinearRegression` to predict number of points for the player by looking at the player's past N seasons and the comparable players N past seasons.

So far, I must admit this model is not very impressive, it barely outperforms the baseline of predicting that player X will have the same number of points as its last season. Looking at feature importance, I can see that the comparable players statistics aren't really used. I believe that by finding better comparables, I might reach a better model. 

So, the following steps for this project is to find better features to find comparable players and to use these features to get a better points prediction model.

I just got data from MoneyPuck which contains some advanced stats that should help me achieve this objective.
