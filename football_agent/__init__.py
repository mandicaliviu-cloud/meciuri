from __future__ import annotations

import argparse
import csv
import json
import os
import threading
from tkinter import END, StringVar, Tk, Text, ttk

from football_agent.agent import FootballAgent


class FootballDesktopApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Meciuri AI Desktop")
        self.root.geometry("1200x720")
        self.root.minsize(1050, 600)

        self.source_var = StringVar(value="api")
        self.min_prob_var = StringVar(value="0.70")
        self.limit_var = StringVar(value="15")
        self.league_var = StringVar(value="all")
        self.goals_var = StringVar(value="all")

        self.matches_data = []
        self._build_ui()
        self.load_matches()

    def _build_ui(self) -> None:
        controls = ttk.Frame(self.root, padding=12)
        controls.pack(fill="x")

        ttk.Label(controls, text="Sursă:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            controls,
            textvariable=self.source_var,
            values=["api", "sample"],
            width=12,
            state="readonly",
        ).grid(row=0, column=1, padx=(0, 12), sticky="w")

        ttk.Label(controls, text="Prob. minimă:").grid(row=0, column=2, sticky="w")
        ttk.Entry(controls, textvariable=self.min_prob_var, width=8).grid(row=0, column=3, padx=(0, 12))

        ttk.Label(controls, text="Limită:").grid(row=0, column=4, sticky="w")
        ttk.Entry(controls, textvariable=self.limit_var, width=8).grid(row=0, column=5, padx=(0, 12))

        ttk.Label(controls, text="Ligă:").grid(row=0, column=6, sticky="w")
        ttk.Entry(controls, textvariable=self.league_var, width=18).grid(row=0, column=7, padx=(0, 12))

        ttk.Label(controls, text="Goluri:").grid(row=0, column=8, sticky="w")
        ttk.Combobox(
            controls,
            textvariable=self.goals_var,
            values=["all", "Over 1.5", "Over 2.5", "BTTS Yes"],
            width=14,
            state="readonly",
        ).grid(row=0, column=9, padx=(0, 12))

        ttk.Button(controls, text="Caută meciuri", command=self.load_matches).grid(row=0, column=10, padx=(0, 8))
        ttk.Button(controls, text="Export CSV", command=self.export_csv).grid(row=0, column=11)

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("league", "match", "win_prob", "double_chance", "goals", "confidence")
        self.tree = ttk.Treeview(main, columns=columns, show="headings")
        self.tree.heading("league", text="Ligă")
        self.tree.heading("match", text="Meci")
        self.tree.heading("win_prob", text="Prob. victorie")
        self.tree.heading("double_chance", text="Double chance")
        self.tree.heading("goals", text="Goluri")
        self.tree.heading("confidence", text="Încredere")
        self.tree.column("league", width=160)
        self.tree.column("match", width=230)
        self.tree.column("win_prob", width=120)
        self.tree.column("double_chance", width=120)
        self.tree.column("goals", width=130)
        self.tree.column("confidence", width=110)
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.show_match_details)

        details = ttk.Frame(main, width=360)
        details.pack(side="right", fill="y", padx=(12, 0))

        self.detail_title = ttk.Label(details, text="Detalii meci", font=("Segoe UI", 12, "bold"))
        self.detail_title.pack(anchor="w", pady=(0, 8))

        self.detail_text = Text(details, wrap="word", height=24, width=42, state="disabled", bg="#f6f8fb")
        self.detail_text.pack(fill="both", expand=True)

    def load_matches(self) -> None:
        try:
            min_prob = float(self.min_prob_var.get())
            limit = int(self.limit_var.get())
        except ValueError:
            self._set_details("Valori invalide pentru probabilitatea minimă sau limită.")
            return

        source = self.source_var.get()
        league_filter = self.league_var.get().strip() or "all"
        goals_filter = self.goals_var.get() if self.goals_var.get() != "all" else None

        agent = FootballAgent(
            source=source,
            min_win_prob=min_prob,
            league_filter=league_filter,
            goals_market_filter=goals_filter,
        )

        self.matches_data = agent.find_matches(limit=limit)
        for item in self.tree.get_children():
            self.tree.delete(item)

        for match in self.matches_data:
            self.tree.insert(
                "",
                "end",
                values=(
                    match.league,
                    f"{match.home_team} vs {match.away_team}",
                    f"{match.predicted_win_prob:.2%}",
                    f"{match.double_chance_odds:.2f}",
                    match.goals_market,
                    match.confidence,
                ),
                iid=str(id(match)),
            )

        if self.matches_data:
            self.tree.selection_set(self.tree.get_children()[0])
            self.show_match_details()
        else:
            self._set_details("Nu există meciuri care să respecte criteriile curente.")

    def show_match_details(self, event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        row_index = self.tree.index(selected[0])
        if row_index >= len(self.matches_data):
            return

        match = self.matches_data[row_index]
        text = (
            f"Echipa gazdă: {match.home_team}\n"
            f"Echipa oaspete: {match.away_team}\n"
            f"Ligă: {match.league}\n"
            f"Data: {match.kickoff}\n"
            f"Probabilitate victorie: {match.predicted_win_prob:.2%}\n"
            f"Double chance: {match.double_chance_odds:.2f}\n"
            f"Goluri: {match.goals_market}\n"
            f"Scor estimat: {match.score_prediction}\n"
            f"Încredere: {match.confidence}\n\n"
            f"Motiv: {match.reason}"
        )
        self._set_details(text)

    def export_csv(self) -> None:
        if not self.matches_data:
            self._set_details("Nu există date de exportat.")
            return

        file_path = os.path.join(os.getcwd(), "meciuri_ai_export.csv")
        fieldnames = [
            "home_team",
            "away_team",
            "league",
            "kickoff",
            "predicted_win_prob",
            "double_chance_odds",
            "goals_market",
            "confidence",
            "reason",
            "score_prediction",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for match in self.matches_data:
                writer.writerow(match.to_dict())

        self._set_details(f"Export CSV realizat cu succes: {file_path}")

    def _set_details(self, text: str) -> None:
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", END)
        self.detail_text.insert(END, text)
        self.detail_text.configure(state="disabled")


def main() -> None:
    parser = argparse.ArgumentParser(description="Meciuri AI Desktop")
    parser.add_argument("--cli", action="store_true", help="Ruleaza in modul CLI")
    parser.add_argument("--source", choices=["sample", "api"], default="api")
    parser.add_argument("--min-win-prob", type=float, default=0.70)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--league", default="all")
    parser.add_argument("--goals-market", choices=["all", "Over 1.5", "Over 2.5", "BTTS Yes"], default="all")
    args = parser.parse_args()

    if args.cli:
        agent = FootballAgent(
            source=args.source,
            min_win_prob=args.min_win_prob,
            league_filter=args.league,
            goals_market_filter=args.goals_market if args.goals_market != "all" else None,
        )
        matches = agent.find_matches(limit=args.limit)
        print(json.dumps([m.to_dict() for m in matches], ensure_ascii=False, indent=2))
        return

    root = Tk()
    FootballDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
