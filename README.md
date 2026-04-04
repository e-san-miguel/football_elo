# Women's International Football Elo Ratings

Elo ratings for women's national football (soccer) teams, computed using the [eloratings.net](https://www.eloratings.net/about) methodology adapted for the women's game.

## Current Rankings

| Rank | Team | Rating |
|---:|:---|---:|
| 1 | Spain | 2395 |
| 2 | United States | 2393 |
| 3 | Japan | 2291 |
| 4 | England | 2290 |
| 5 | France | 2279 |
| 6 | Germany | 2262 |
| 7 | Sweden | 2255 |
| 8 | Brazil | 2204 |
| 9 | Canada | 2158 |
| 10 | Netherlands | 2093 |

Full rankings in [`output/current_rankings.csv`](output/current_rankings.csv).

## Methodology

Uses the World Football Elo Rating formula:

**Rn = Ro + K × G × (W − We)**

- **K factor** — tournament importance: World Cup/Olympics (60), continental championships (50), qualifiers (40), other tournaments (30), friendlies (20)
- **G factor** — goal difference multiplier: 1-goal win = 1.0, 2-goal win = 1.5, 3+ goals (N) = (11 + N) / 8
- **We** — expected result: `1 / (10^(-dr/400) + 1)`, with +100 home advantage
- **W** — actual result: win = 1, draw = 0.5, loss = 0 (shootouts count as draws)
- **Initial rating** — 1500 for all teams

## Data Source

Match data from [martj42/womens-international-results](https://github.com/martj42/womens-international-results) (CC0 license) — 11,000+ women's international matches from 1956 to present.

## Usage

```bash
# Install
pip install -e .

# Run full pipeline (download data, compute ratings, generate output)
python -m football_elo run

# Show rankings in terminal
python -m football_elo rankings --top 30

# Audit tournament K-factor mapping
python -m football_elo audit

# Options
python -m football_elo run --force-download --start-date 1990-01-01 --top 30
```

## Output

- `output/current_rankings.csv` — full rankings
- `output/current_rankings.md` — markdown table
- `output/full_history.csv` — per-team-per-match rating history
- `output/top_teams_history.png` — rating chart over time

## License

CC0 1.0 Universal — public domain.
