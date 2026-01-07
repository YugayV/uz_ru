import tg_bot.games as games


def test_load_games_from_disk():
    disk = games._load_games_from_disk()
    assert disk is not None
    assert isinstance(disk, list)
    assert len(disk) >= 1


def test_get_random_game():
    g = games.get_random_game()
    assert isinstance(g, dict)
    assert "id" in g and "type" in g
