from __future__ import annotations

from pathlib import Path

from src.domain.models import RawNote


class FileSystemNoteSource:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path

    def list_paths(self) -> list[str]:
        if not self.vault_path.exists():
            return []

        return sorted(
            str(path.relative_to(self.vault_path))
            for path in self.vault_path.rglob("*.md")
            if path.is_file()
        )

    def read_note(self, path: str) -> RawNote:
        full_path = self.vault_path / path

        if not full_path.exists():
            return RawNote(
                path=path,
                text=None,
                mtime=0.0,
                exists=False,
                read_status="missing",
            )

        try:
            text = full_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return RawNote(
                path=path,
                text=None,
                mtime=0.0,
                exists=False,
                read_status="missing",
            )
        except OSError as exc:
            status = "icloud_deferred" if getattr(exc, "errno", None) == 35 else "error"
            return RawNote(
                path=path,
                text=None,
                mtime=0.0,
                exists=True,
                read_status=status,
            )

        return RawNote(
            path=path,
            text=text,
            mtime=full_path.stat().st_mtime,
            exists=True,
            read_status="ok",
        )
