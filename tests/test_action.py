from five_crowns import ActionStatus
def test_action(action):
    """
    Test that Action object is correctly initialized.
    """
    assert action.action_status == ActionStatus.ENABLED
