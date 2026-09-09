import os
import uuid

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://turnos:turnos_dev@localhost:5432/turnos_test"
)

from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Employee, Shift, ShiftRule, ShiftRuleEmployee

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_rule(db_session):
    def _make(name="Jornada Completa", day="8", week="40") -> ShiftRule:
        rule = ShiftRule(
            name=name, max_hours_day=Decimal(day), max_hours_week=Decimal(week)
        )
        db_session.add(rule)
        db_session.flush()
        return rule

    return _make


@pytest.fixture
def make_employee(db_session):
    def _make(name="Ana", email=None) -> Employee:
        employee = Employee(
            name=name,
            last_name="Test",
            phone_number="+56900000000",
            email=email or f"{name.lower()}.{uuid.uuid4().hex[:8]}@test.cl",
        )
        db_session.add(employee)
        db_session.flush()
        return employee

    return _make


@pytest.fixture
def make_assignment(db_session):
    def _make(employee: Employee, rule: ShiftRule) -> ShiftRuleEmployee:
        assignment = ShiftRuleEmployee(
            employee_id=employee.id, shift_rule_id=rule.shift_rule_id
        )
        db_session.add(assignment)
        db_session.flush()
        return assignment

    return _make


@pytest.fixture
def make_shift(db_session):
    def _make(
        employee_id: int,
        shift_date: date = date(2026, 9, 8),
        start: str = "08:00",
        end: str = "12:00",
    ) -> Shift:
        shift = Shift(
            employee_id=employee_id,
            shift_date=shift_date,
            start_time=time.fromisoformat(start),
            end_time=time.fromisoformat(end),
        )
        db_session.add(shift)
        db_session.flush()
        return shift

    return _make


@pytest.fixture
def any_email() -> str:
    return f"user.{uuid.uuid4().hex[:8]}@test.cl"
