from src.core.config import Settings


def test_settings_reads_values_from_dotenv(tmp_path, monkeypatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        'OBSIDIAN_RAG_VAULT_PATH="/tmp/vault"\n'
        'OBSIDIAN_RAG_GENERATOR_MODEL="gemma3"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OBSIDIAN_RAG_VAULT_PATH", raising=False)
    monkeypatch.delenv("OBSIDIAN_RAG_GENERATOR_MODEL", raising=False)

    settings = Settings.from_env()

    assert str(settings.vault_path) == "/tmp/vault"
    assert settings.generator_model == "gemma3"


def test_environment_variables_override_dotenv(tmp_path, monkeypatch) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        'OBSIDIAN_RAG_GENERATOR_MODEL="gemma3"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OBSIDIAN_RAG_GENERATOR_MODEL", "qwen3:8b")

    settings = Settings.from_env()

    assert settings.generator_model == "qwen3:8b"
