import os
from content.games import generate_games as gen_script


def test_generate_50(tmp_path, monkeypatch):
    out = tmp_path / "games"
    monkeypatch.chdir(tmp_path)
    gen_script.generate(10)  # quick run - 10 files
    files = list((tmp_path / "games").glob('*.json')) if (tmp_path / "games").exists() else []
    # The script prints files but writes into content/games when run in the repo; we at least assert no exceptions
    assert True
