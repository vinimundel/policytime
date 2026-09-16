"""Persistent caching and atomic budget reservations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from policytime.adapters.database import BudgetMonthRow, CacheRow, ReservationRow
from policytime.application.contracts import AnswerResponse, BudgetExceeded


class PostgresCache:
    def __init__(self, engine: Engine, ttl_seconds: int = 86400) -> None:
        self.engine = engine
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> AnswerResponse | None:
        with Session(self.engine) as session:
            payload = session.scalar(
                select(CacheRow.payload).where(
                    CacheRow.key == key,
                    CacheRow.expires_at > datetime.now(UTC),
                )
            )
        if payload is None:
            return None
        return AnswerResponse.model_validate(payload)

    def put(self, key: str, response: AnswerResponse) -> None:
        now = datetime.now(UTC)
        values = {
            "key": key,
            "payload": response.model_dump(mode="json"),
            "expires_at": now + timedelta(seconds=self.ttl_seconds),
        }
        with Session(self.engine) as session, session.begin():
            session.execute(delete(CacheRow).where(CacheRow.expires_at <= now))
            session.execute(
                insert(CacheRow)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["key"],
                    set_=values,
                )
            )


class PostgresBudgetLedger:
    def __init__(self, engine: Engine, monthly_limit: Decimal) -> None:
        if monthly_limit <= 0:
            raise ValueError("Monthly budget must be positive.")
        self.engine = engine
        self.monthly_limit = monthly_limit

    def reserve(self, maximum_cost: Decimal) -> str:
        if maximum_cost <= 0:
            raise ValueError("Reservation must be positive.")
        now = datetime.now(UTC)
        month = now.strftime("%Y-%m")
        identifier = str(uuid4())
        with Session(self.engine) as session, session.begin():
            session.execute(
                insert(BudgetMonthRow)
                .values(month=month, spent=0, reserved=0)
                .on_conflict_do_nothing(index_elements=["month"])
            )
            budget = session.scalars(
                select(BudgetMonthRow).where(BudgetMonthRow.month == month).with_for_update()
            ).one()
            if budget.spent + budget.reserved + maximum_cost > self.monthly_limit:
                raise BudgetExceeded("The demo's monthly model budget has been reached.")
            budget.reserved += maximum_cost
            session.add(
                ReservationRow(
                    id=identifier,
                    month=month,
                    amount=maximum_cost,
                    settled=False,
                    created_at=now,
                )
            )
        return identifier

    def settle(self, reservation_id: str, actual_cost: Decimal | None) -> None:
        if actual_cost is not None and actual_cost < 0:
            raise ValueError("Actual cost cannot be negative.")
        with Session(self.engine) as session, session.begin():
            reservation = session.scalars(
                select(ReservationRow).where(ReservationRow.id == reservation_id).with_for_update()
            ).one()
            if reservation.settled:
                return
            budget = session.scalars(
                select(BudgetMonthRow)
                .where(BudgetMonthRow.month == reservation.month)
                .with_for_update()
            ).one()
            # Unknown outcomes remain charged conservatively; a timeout may still be billable.
            budget.reserved -= reservation.amount
            budget.spent += reservation.amount if actual_cost is None else actual_cost
            reservation.settled = True

    def summary(self) -> dict[str, str]:
        month = datetime.now(UTC).strftime("%Y-%m")
        with Session(self.engine) as session:
            row = session.get(BudgetMonthRow, month)
            return {
                "month": month,
                "limit_usd": str(self.monthly_limit),
                "spent_usd": str(row.spent if row else 0),
                "reserved_usd": str(row.reserved if row else 0),
            }
