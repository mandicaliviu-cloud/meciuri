from football_agent.agent import FootballAgent


def test_sample_match_selection_rewards_high_win_probabilities():
    agent = FootballAgent(source="sample", min_win_prob=0.70)
    matches = agent.find_matches(limit=10)

    assert matches
    assert all(match.predicted_win_prob >= 0.70 for match in matches)
    assert all(match.double_chance_odds > 1.0 for match in matches)
    assert all("Over" in match.goals_market or "BTTS" in match.goals_market for match in matches)


def test_min_win_prob_filter():
    agent = FootballAgent(source="sample", min_win_prob=0.90)
    matches = agent.find_matches(limit=10)
    assert all(match.predicted_win_prob >= 0.90 for match in matches)
