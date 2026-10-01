import json
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError

from dentiva.core.errors import InstanceAlreadyRunningError
from dentiva.data.engine import create_sqlite_engine
from dentiva.data.locking import InstanceLock
from dentiva.data.shutdown import ShutdownFlag


@pytest.mark.integration
def test_file_engine_applies_durable_pragmas_and_foreign_keys(tmp_path: Path) -> None:
    engine = create_sqlite_engine(tmp_path / "nested" / "clinic.sqlite3")
    try:
        with engine.connect() as connection:
            values = {
                name: connection.exec_driver_sql(f"PRAGMA {name}").scalar_one()
                for name in (
                    "journal_mode",
                    "foreign_keys",
                    "busy_timeout",
                    "synchronous",
                    "temp_store",
                )
            }
            cache_size = connection.exec_driver_sql("PRAGMA cache_size").scalar_one()
        assert values == {
            "journal_mode": "wal",
            "foreign_keys": 1,
            "busy_timeout": 5_000,
            "synchronous": 2,
            "temp_store": 2,
        }
        assert cache_size == -20_000
        with engine.begin() as connection:
            connection.exec_driver_sql("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
            connection.exec_driver_sql(
                "CREATE TABLE child (parent_id INTEGER REFERENCES parent(id))"
            )
        with pytest.raises(SQLAlchemyIntegrityError), engine.begin() as connection:
            connection.exec_driver_sql("INSERT INTO child (parent_id) VALUES (99)")
    finally:
        engine.dispose()


def test_memory_engine_uses_connection_safe_pragmas(tmp_path: Path) -> None:
    engine = create_sqlite_engine(":memory:", busy_timeout_ms=1_250)
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one() == 1_250
            assert connection.exec_driver_sql("PRAGMA synchronous").scalar_one() == 2
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() == "memory"
    finally:
        engine.dispose()


def test_instance_lock_refuses_a_second_process_lock_and_releases(tmp_path: Path) -> None:
    lock_path = tmp_path / "state" / "dentiva.lock"
    first = InstanceLock(lock_path)
    second = InstanceLock(lock_path)
    first.acquire()
    try:
        with pytest.raises(InstanceAlreadyRunningError):
            second.acquire()
    finally:
        first.release()
    with InstanceLock(lock_path):
        pass
    assert lock_path.exists()


def test_shutdown_flag_is_atomic_state_for_next_start(tmp_path: Path) -> None:
    flag = ShutdownFlag(tmp_path / "data" / "unclean.json")
    assert not flag.was_unclean
    assert not flag.begin_startup()
    assert flag.was_unclean
    assert json.loads(flag.path.read_text(encoding="utf-8"))["pid"] > 0
    assert flag.begin_startup()
    flag.mark_clean_shutdown()
    assert not flag.was_unclean
