from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


@dataclass
class MatchCandidate:
    home_team: str
    away_team: str
    league: str
    kickoff: str
    predicted_win_prob: float
    double_chance_odds: float
    goals_market: str
    confidence: str
    reason: str
    score_prediction: str = "1-0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "league": self.league,
            "kickoff": self.kickoff,
            "predicted_win_prob": round(self.predicted_win_prob, 3),
            "double_chance_odds": round(self.double_chance_odds, 2),
            "goals_market": self.goals_market,
            "confidence": self.confidence,
            "reason": self.reason,
            "score_prediction": self.score_prediction,
        }


class FootballAgent:
    def __init__(
        self,
        source: str = "sample",
        min_win_prob: float = 0.70,
        league_filter: str = "all",
        goals_market_filter: Optional[str] = None,
    ) -> None:
        self.source = source
        self.min_win_prob = min_win_prob
        self.league_filter = league_filter.lower() if league_filter else "all"
        self.goals_market_filter = goals_market_filter

    def fetch_matches(self) -> List[Dict[str, Any]]:
        if self.source == "api":
            return self._fetch_from_api()
        return self._get_sample_matches()

    def _fetch_from_api(self) -> List[Dict[str, Any]]:
        api_key = os.getenv("THE_ODDS_API_KEY")
        if not api_key:
            return self._get_sample_matches()

        sports = [
            part.strip()
            for part in os.getenv(
                "ODDS_SPORTS",
                "soccer_epl,soccer_serie_a,soccer_bundesliga,soccer_laliga,soccer_ligue1",
            ).split(",")
            if part.strip()
        ]
        region = os.getenv("ODDS_REGION", "uk")
        results: List[Dict[str, Any]] = []

        for sport in sports:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": region,
                "markets": "h2h,totals",
                "oddsFormat": "decimal",
            }
            try:
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, list):
                    results.extend(payload)
            except Exception:
                continue

        normalized: List[Dict[str, Any]] = []
        for match in results:
            if not isinstance(match, dict):
                continue
            bookmakers = match.get("bookmakers") or []
            if not bookmakers:
                continue

            home_team = match.get("home_team") or match.get("homeTeam") or "Home team"
            away_team = match.get("away_team") or match.get("awayTeam") or "Away team"
            league = match.get("sport_title") or "Football"
            kickoff = match.get("commence_time") or datetime.utcnow().isoformat()

            best_home = 0.0
            best_draw = 0.0
            best_away = 0.0
            best_total = 0.0
            best_btts = 0.0

            for bookmaker in bookmakers:
                for market in bookmaker.get("markets", []):
                    key = market.get("key")
                    outcomes = market.get("outcomes") or []
                    if key == "h2h":
                        for outcome in outcomes:
                            name = (outcome.get("name") or "").strip().lower()
                            price = float(outcome.get("price", 0) or 0)
                            if name == home_team.lower():
                                best_home = max(best_home, price)
                            elif name == away_team.lower():
                                best_away = max(best_away, price)
                            elif name in ("draw", "x"):
                                best_draw = max(best_draw, price)
                    elif key == "totals":
                        for outcome in outcomes:
                            name = (outcome.get("name") or "").strip().lower()
                            price = float(outcome.get("price", 0) or 0)
                            if name in ("over 1.5", "over 2.5"):
                                best_total = max(best_total, price)
                            if name in ("btts yes", "both teams to score yes"):
                                best_btts = max(best_btts, price)

            if best_home <= 1.0 or best_draw <= 1.0:
                continue

            normalized.append(
                {
                    "home_team": home_team,
                    "away_team": away_team,
                    "league": league,
                    "kickoff": kickoff,
                    "home_win_odds": best_home,
                    "draw_odds": best_draw,
                    "away_win_odds": best_away or 4.0,
                    "double_chance_odds": self._calculate_double_chance(best_home, best_draw),
                    "goals_market": self._pick_goals_market(best_total, best_btts),
                    "goals_odds": max(best_total, best_btts, 1.0),
                    "team_strength": self._public_team_strength(best_home, best_draw, best_away or 4.0),
                }
            )

        return normalized

    def _get_sample_matches(self) -> List[Dict[str, Any]]:
        return [
            {
                "home_team": "Barcelona",
                "away_team": "Valencia",
                "league": "La Liga",
                "kickoff": "2026-10-29T20:00:00Z",
                "home_win_odds": 1.58,
                "draw_odds": 4.4,
                "away_win_odds": 6.2,
                "double_chance_odds": 1.42,
                "goals_market": "Over 1.5",
                "goals_odds": 1.63,
                "team_strength": 0.82,
            },
            {
                "home_team": "Inter",
                "away_team": "Lazio",
                "league": "Serie A",
                "kickoff": "2026-10-31T21:00:00Z",
                "home_win_odds": 1.66,
                "draw_odds": 3.9,
                "away_win_odds": 5.1,
                "double_chance_odds": 1.36,
                "goals_market": "Over 1.5",
                "goals_odds": 1.58,
                "team_strength": 0.79,
            },
            {
                "home_team": "Bayern Munich",
                "away_team": "Wolfsburg",
                "league": "Bundesliga",
                "kickoff": "2026-11-01T18:30:00Z",
                "home_win_odds": 1.35,
                "draw_odds": 6.0,
                "away_win_odds": 9.5,
                "double_chance_odds": 1.29,
                "goals_market": "Over 2.5",
                "goals_odds": 1.72,
                "team_strength": 0.89,
            },
            {
                "home_team": "PSG",
                "away_team": "Monaco",
                "league": "Ligue 1",
                "kickoff": "2026-10-30T20:45:00Z",
                "home_win_odds": 1.52,
                "draw_odds": 4.8,
                "away_win_odds": 6.8,
                "double_chance_odds": 1.33,
                "goals_market": "BTTS Yes",
                "goals_odds": 1.61,
                "team_strength": 0.84,
            },
            {
                "home_team": "Real Madrid",
                "away_team": "Sevilla",
                "league": "La Liga",
                "kickoff": "2026-11-03T20:00:00Z",
                "home_win_odds": 1.44,
                "draw_odds": 4.9,
                "away_win_odds": 7.5,
                "double_chance_odds": 1.38,
                "goals_market": "Over 2.5",
                "goals_odds": 1.75,
                "team_strength": 0.87,
            },
            {
                "home_team": "Arsenal",
                "away_team": "Fulham",
                "league": "Premier League",
                "kickoff": "2026-10-28T18:00:00Z",
                "home_win_odds": 1.47,
                "draw_odds": 5.0,
                "away_win_odds": 7.0,
                "double_chance_odds": 1.39,
                "goals_market": "Over 1.5",
                "goals_odds": 1.64,
                "team_strength": 0.83,
            },
        ]

    def find_matches(self, limit: Optional[int] = None) -> List[MatchCandidate]:
        matches: List[MatchCandidate] = []
        for item in self.fetch_matches():
            home_team = item.get("home_team") or "Home team"
            away_team = item.get("away_team") or "Away team"
            league = item.get("league") or "Unknown league"
            kickoff = item.get("kickoff") or datetime.utcnow().isoformat()

            home_win_odds = float(item.get("home_win_odds", 2.0))
            draw_odds = float(item.get("draw_odds", 3.5))
            away_win_odds = float(item.get("away_win_odds", 5.0))
            double_chance_odds = float(
                item.get("double_chance_odds", self._calculate_double_chance(home_win_odds, draw_odds))
            )
            goals_odds = float(item.get("goals_odds", 1.4))
            goals_market = item.get("goals_market") or self._pick_goals_market(goals_odds, goals_odds)
            team_strength = float(
                item.get("team_strength", self._public_team_strength(home_win_odds, draw_odds, away_win_odds))
            )

            if self.league_filter != "all" and self.league_filter not in league.lower():
                continue
            if self.goals_market_filter and goals_market != self.goals_market_filter:
                continue

            win_prob = self._estimate_home_win_prob(home_win_odds, draw_odds, away_win_odds, team_strength)
            if win_prob < self.min_win_prob:
                continue
            if double_chance_odds <= 1.0 or goals_odds <= 1.0:
                continue

            score_prediction = self._predict_score(home_win_odds, away_win_odds)
            confidence = "High" if win_prob >= 0.80 else "Moderate"
            reason = self._build_reason(team_strength, home_win_odds, draw_odds, away_win_odds)

            matches.append(
                MatchCandidate(
                    home_team=home_team,
                    away_team=away_team,
                    league=league,
                    kickoff=kickoff,
                    predicted_win_prob=win_prob,
                    double_chance_odds=double_chance_odds,
                    goals_market=goals_market,
                    confidence=confidence,
                    reason=reason,
                    score_prediction=score_prediction,
                )
            )

        matches.sort(key=lambda x: (x.predicted_win_prob, x.double_chance_odds), reverse=True)
        if limit is not None:
            return matches[:limit]
        return matches

    def _estimate_home_win_prob(
        self,
        home_win_odds: float,
        draw_odds: float,
        away_win_odds: float,
        team_strength: float,
    ) -> float:
        home_imp = 1.0 / home_win_odds
        draw_imp = 1.0 / draw_odds
        away_imp = 1.0 / away_win_odds
        total = home_imp + draw_imp + away_imp
        fair_home_prob = (home_imp / total) if total else 0.33
        favorite_bonus = max(0.0, (2.20 - home_win_odds) * 0.18)
        strength_bonus = max(0.0, (team_strength - 0.5) * 0.45)
        probability = fair_home_prob * 1.20 + favorite_bonus + strength_bonus
        return min(0.95, max(0.0, probability))

    def _calculate_double_chance(self, home_win_odds: float, draw_odds: float) -> float:
        if home_win_odds <= 0 or draw_odds <= 0:
            return 1.0
        return max(1.05, (home_win_odds * draw_odds) / (home_win_odds + draw_odds))

    def _public_team_strength(self, home_win_odds: float, draw_odds: float, away_win_odds: float) -> float:
        if home_win_odds <= 0 or draw_odds <= 0 or away_win_odds <= 0:
            return 0.55

        favorite = max(0.0, 2.2 - home_win_odds)
        outsider = max(0.0, away_win_odds - 3.0)
        if favorite > 0:
            return 0.63 + min(0.24, favorite * 0.14) + min(0.08, outsider * 0.01)
        return 0.57 + min(0.12, (draw_odds - 3.0) * 0.02)

    def _pick_goals_market(self, total_odds: float, btts_odds: float) -> str:
        if total_odds > btts_odds:
            return "Over 1.5"
        if total_odds > 1.6:
            return "Over 2.5"
        return "BTTS Yes"

    def _predict_score(self, home_win_odds: float, away_win_odds: float) -> str:
        home_goals = max(0, int(round(2.0 - (home_win_odds - 1.0) * 0.8)))
        away_goals = max(0, int(round(1.0 + (away_win_odds - 3.0) * 0.25)))
        return f"{max(0, home_goals)}-{max(0, away_goals)}"

    def _build_reason(
        self,
        team_strength: float,
        home_win_odds: float,
        draw_odds: float,
        away_win_odds: float,
    ) -> str:
        reasons = []
        if home_win_odds <= 1.8:
            reasons.append("favorit clar")
        if draw_odds >= 4.0:
            reasons.append("remiză mai puțin probabilă")
        if team_strength >= 0.75:
            reasons.append("forță echipei acasă")
        if away_win_odds >= 4.5:
            reasons.append("adversar cu cotă ridicată")
        if not reasons:
            return "profil echilibrat, dar cu avantaj tematic pentru gazdă"
        return ", ".join(reasons)


if __name__ == "__main__":
    agent = FootballAgent(source="sample", min_win_prob=0.70)
    matches = agent.find_matches(limit=5)
    print(json.dumps([match.to_dict() for match in matches], ensure_ascii=False, indent=2))
