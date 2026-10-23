import sqlite3
from typing import Any, Dict, List


class MatchHistoryStore:
    def __init__(self, db_path: str = "meciuri_history.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    league TEXT,
                    kickoff TEXT,
                    predicted_win_prob REAL,
                    double_chance_odds REAL,
                    goals_market TEXT,
                    confidence TEXT,
                    reason TEXT,
                    score_prediction TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    league TEXT,
                    kickoff TEXT,
                    predicted_win_prob REAL,
                    double_chance_odds REAL,
                    goals_market TEXT,
                    confidence TEXT,
                    reason TEXT,
                    score_prediction TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def save_snapshot(self, matches: List[Dict[str, Any]]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            for match in matches:
                conn.execute(
                    """
                    INSERT INTO matches(
                        home_team, away_team, league, kickoff,
                        predicted_win_prob, double_chance_odds, goals_market,
                        confidence, reason, score_prediction
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        match.get("home_team"),
                        match.get("away_team"),
                        match.get("league"),
                        match.get("kickoff"),
                        match.get("predicted_win_prob"),
                        match.get("double_chance_odds"),
                        match.get("goals_market"),
                        match.get("confidence"),
                        match.get("reason"),
                        match.get("score_prediction"),
                    ),
                )
            conn.commit()

    def save_selected(self, match: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO saved_matches(
                    home_team, away_team, league, kickoff,
                    predicted_win_prob, double_chance_odds, goals_market,
                    confidence, reason, score_prediction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match.get("home_team"),
                    match.get("away_team"),
                    match.get("league"),
                    match.get("kickoff"),
                    match.get("predicted_win_prob"),
                    match.get("double_chance_odds"),
                    match.get("goals_market"),
                    match.get("confidence"),
                    match.get("reason"),
                    match.get("score_prediction"),
                ),
            )
            conn.commit()

    def get_recent_snapshot(self, limit: int = 20) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT home_team, away_team, league, kickoff, predicted_win_prob,
                       double_chance_odds, goals_market, confidence, reason, score_prediction
                FROM matches
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "home_team": row[0],
                "away_team": row[1],
                "league": row[2],
                "kickoff": row[3],
                "predicted_win_prob": row[4],
                "double_chance_odds": row[5],
                "goals_market": row[6],
                "confidence": row[7],
                "reason": row[8],
                "score_prediction": row[9],
            }
            for row in rows
        ]

    def get_saved_matches(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT home_team, away_team, league, kickoff, predicted_win_prob,
                       double_chance_odds, goals_market, confidence, reason, score_prediction
                FROM saved_matches
                ORDER BY id DESC
                """
            ).fetchall()
        return [
            {
                "home_team": row[0],
                "away_team": row[1],
                "league": row[2],
                "kickoff": row[3],
                "predicted_win_prob": row[4],
                "double_chance_odds": row[5],
                "goals_market": row[6],
                "confidence": row[7],
                "reason": row[8],
                "score_prediction": row[9],
            }
            for row in rows
        ]
