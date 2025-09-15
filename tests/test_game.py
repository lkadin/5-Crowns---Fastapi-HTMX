from five_crowns import Player
from five_crowns import Action


class TestGame:

    def test_initialization(self, game):
        assert game.players == {}
        assert game.NUM_OF_ROUNDS == 11
        assert game.game_status == "Not started"
        assert game.actions == []

    def test_next_turn(self, game_ready):
        game_ready.start()
        turn = game_ready.whose_turn()
        game_ready.next_turn()
        assert game_ready.whose_turn() != turn

    def test_whose_turn_name(self, game_ready):
        assert (
            game_ready.whose_turn_name()
            == game_ready.players[
                game_ready.player_index_to_id(game_ready.current_player_index)
            ].name
        )

    def test_whose_turn(self, game_ready):
        assert isinstance(game_ready.whose_turn(), int)

    def test_add_all_actions(self, game_ready):
        game_ready.set_game_status(None)
        game_ready.add_all_actions()
        assert len(game_ready.actions) == 5

        game_ready.set_game_status("Waiting")
        game_ready.add_all_actions()
        assert len(game_ready.actions) == 5

        game_ready.set_game_status("In Progress")
        game_ready.add_all_actions()
        assert len(game_ready.actions) == 5

    def test_enable_all_actions(self, game_ready):
        for action in game_ready.actions:
            if action.name not in ("Start", "Restart","Pick_from_discard","Pick_from_deck"):
                assert action.action_status == "enabled"

    def test_wait(self, game):
        game.wait()
        assert game.game_status == "Waiting"

    def test_start(self, game_ready):
        game_ready.start()
        assert game_ready.deck is not None
        assert len(game_ready.actions) > 0

    def test_your_turn(self, game_ready):
        assert isinstance(game_ready.your_turn(), bool)

    def test_player(self, game_ready, ids):
        assert isinstance(game_ready.player("1"), Player)

    def test_initial_deal(self, game_ready, ids):
        for player in game_ready.players.values():
            assert len(player.hand) == 3

    def test_action_from_action_name(self, game_ready):
        for action in game_ready.actions:
            assert isinstance(game_ready.action_from_action_name(action.name), Action)
        assert game_ready.action_from_action_name(None).name == "No_action"
        assert game_ready.action_from_action_name("FRED").name == "No_action"
        assert isinstance(game_ready.action_from_action_name("Assassinate"), Action)

    def test_process_action(self, game_ready):
        for action in game_ready.actions:
            assert game_ready.process_action(action, game_ready.user_id) is None

    def test_process_action_start(self, game_ready):
        action = Action("Start",  "enabled", )
        user_id = game_ready.player_index_to_id(game_ready.current_player_index)
        game_ready.set_game_status("Waiting")
        game_ready.process_action(action, user_id)
        assert game_ready.game_status == "In progress"


    def test_player_id(self, game_ready, ids):
        assert game_ready.player_id("Lee") == "1"


    def test_set_current_action(self, game_ready):
        game_ready.set_current_action("Start", "1")
        assert game_ready.get_current_action().name == "Start"

    def test_set_game_status(self, game_ready):
        assert game_ready.get_game_status() == "In progress"
        game_ready.set_game_status("Waiting")
        assert game_ready.get_game_status() == "Waiting"

