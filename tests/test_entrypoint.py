import pytest

from spatial_target_atlas import entrypoint


def test_entrypoint_explains_missing_cli_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_find_spec(package: str) -> object | None:
        return None if package == "typer" else object()

    monkeypatch.setattr(entrypoint, "find_spec", fake_find_spec)

    with pytest.raises(SystemExit, match=r"\[cli\]"):
        entrypoint.main()
