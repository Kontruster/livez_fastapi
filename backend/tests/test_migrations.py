"""Проверка, что миграции создают схему, совпадающую с моделями.

Этот тест ловит главную проблему прошлой версии проекта: миграции,
которые не описывали реальную схему.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

BACKEND_DIR = Path(__file__).resolve().parent.parent

EXPECTED_TABLES = {
    "users",
    "groups",
    "posts",
    "comments",
    "follows",
    "post_images",
    "alembic_version",
}


def _run_alembic(args: list[str], db_path: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(
        {
            "DATABASE_URL": f"sqlite+aiosqlite:///{db_path.as_posix()}",
            "SECRET_KEY": "test-secret-key-for-tests-only-long-enough-32b",
            "PYTHONPATH": str(BACKEND_DIR),
        }
    )
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def migrated_db(tmp_path):
    """Прогоняет alembic upgrade head на чистой SQLite-базе."""
    db_path = tmp_path / "migration_test.sqlite3"

    result = _run_alembic(["upgrade", "head"], db_path)
    assert result.returncode == 0, f"alembic upgrade failed:\n{result.stderr}"
    return db_path


def test_migrations_create_full_schema(migrated_db):
    engine = create_engine(f"sqlite:///{migrated_db.as_posix()}")
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"Миграции не создали таблицы: {sorted(missing)}"


def test_migrations_match_models(migrated_db):
    """alembic check не должен находить расхождений между моделями и схемой."""
    result = _run_alembic(["check"], migrated_db)
    output = result.stdout + result.stderr

    assert "No new upgrade operations detected" in output, "Модели и миграции разошлись:\n" + output


def test_follows_has_unique_constraint(migrated_db):
    engine = create_engine(f"sqlite:///{migrated_db.as_posix()}")
    inspector = inspect(engine)
    indexes = inspector.get_indexes("follows")
    uniques = inspector.get_unique_constraints("follows")
    engine.dispose()

    has_unique = any(
        set(idx["column_names"]) == {"user_id", "author_id"} and idx["unique"] for idx in indexes
    ) or any(set(uc["column_names"]) == {"user_id", "author_id"} for uc in uniques)
    assert has_unique, "Нет уникального ограничения на пару (user_id, author_id)"


def test_cascade_delete_declared(migrated_db):
    """У дочерних таблиц должен быть ON DELETE CASCADE."""
    engine = create_engine(f"sqlite:///{migrated_db.as_posix()}")
    inspector = inspect(engine)

    comments_fks = inspector.get_foreign_keys("comments")
    posts_fks = inspector.get_foreign_keys("posts")
    engine.dispose()

    comment_targets = {fk["referred_table"]: fk["options"].get("ondelete") for fk in comments_fks}
    post_targets = {fk["referred_table"]: fk["options"].get("ondelete") for fk in posts_fks}

    assert comment_targets.get("posts") == "CASCADE"
    assert comment_targets.get("users") == "CASCADE"
    assert post_targets.get("users") == "CASCADE"
