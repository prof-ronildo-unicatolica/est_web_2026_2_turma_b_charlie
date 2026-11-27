def test_worker_uses_shared_mongo_database_dependency():
    from app.core.database import get_mongo_db
    from app.workers import reserva_worker

    assert reserva_worker.get_mongo_db is get_mongo_db
