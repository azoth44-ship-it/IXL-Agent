from ixl_agent.goal import Goal

def test_goal_creation():
    g = Goal.create(80, 3)
    assert g.target_score == 80
    assert g.seconds_left <= 180

def test_invalid_target():
    try:
        Goal.create(120, 3)
    except ValueError:
        return
    assert False, "expected ValueError"
