"""Reproduce the fictional Northstar Works policy fixture; contains no real company data."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOPICS = {
    "lodging": ("Hotel and lodging", "per_night", (180, 220), (140, 180)),
    "meals": ("Meals", "per_day", (80, 100), (50, 65)),
    "transport": ("Ground transport", "per_trip", (120, 150), (60, 75)),
    "airfare": ("Airfare", None, (), ()),
    "approvals": ("Travel approvals", None, (), ()),
    "submission": ("Expense submission", None, (), ()),
}
DETAILS = {
    "lodging": "Hotel reimbursement covers the room charge and mandatory taxes. "
    "An itemized hotel receipt is required; minibar and personal entertainment are excluded.",
    "meals": "Meals require an itemized receipt with the business purpose. "
    "Alcohol and meals already provided by the host are excluded.",
    "transport": "Ground transport requires a dated taxi or rideshare receipt "
    "and the business route. "
    "Personal detours are excluded.",
    "airfare": "Airfare reimbursement requires the airline invoice and boarding confirmation. "
    "Personal upgrades are excluded.",
    "approvals": "Travel approval must be recorded before booking. "
    "A policy limit alone does not constitute approval for a purchase.",
    "submission": "Submit expenses with receipts, the business purpose, and the expense date. "
    "The submission date never changes which policy applied when the expense occurred.",
}


def main_rule(topic: str, country: str, edition: int) -> tuple[dict, str]:
    title, unit, br, us = TOPICS[topic]
    if unit is not None:
        amount = (br if country == "BR" else us)[edition - 1]
        currency = "BRL" if country == "BR" else "USD"
        unit_label = unit.replace("_", " ")
        value = {"kind": "money", "amount": amount, "currency": currency, "unit": unit}
        return value, f"{title} reimbursement is limited to {currency} {amount} {unit_label}."
    if topic == "submission":
        days = 30 if edition == 1 else 45
        return {"kind": "days", "days": days}, (
            f"Submit an expense claim within {days} calendar days after the expense date."
        )
    if topic == "airfare":
        value = "Economy class only" if edition == 1 else "Economy or premium economy with approval"
        return {"kind": "requirement", "value": value}, f"Airfare eligibility: {value.lower()}."
    value = "Written manager approval" if edition == 1 else "Written manager and finance approval"
    return {
        "kind": "requirement",
        "value": value,
    }, f"Travel requires {value.lower()} before booking."


def make_document(topic: str, country: str, edition: int) -> str:
    identifier = f"{topic}-{country.lower()}-v{edition}"
    start = "2026-01-01" if edition == 1 else "2026-07-01"
    end = "2026-07-01" if edition == 1 else None
    scope = {"countries": [country], "employment_types": ["employee", "contractor"]}
    period = {"start": start, "end": end}
    value, main_text = main_rule(topic, country, edition)
    clauses = []
    passages = {}
    for suffix, rule_value, text in (
        ("main", value, main_text),
        ("documentation", {"kind": "requirement", "value": DETAILS[topic]}, DETAILS[topic]),
    ):
        clause_id = f"{identifier}.{suffix}"
        links = (
            []
            if edition == 1
            else [
                {
                    "kind": "supersedes",
                    "target_id": f"{topic}-{country.lower()}-v1.{suffix}",
                }
            ]
        )
        clauses.append(
            {
                "id": clause_id,
                "document_id": identifier,
                "rule_key": f"{topic}.{suffix}",
                "topic": topic,
                "period": period,
                "scope": scope,
                "value": rule_value,
                "relationships": links,
            }
        )
        passages[clause_id] = text
    if edition == 2 and topic in {"lodging", "meals"}:
        clause_id = f"{identifier}.contractor"
        amount = value["amount"] - (40 if country == "BR" else 20)
        contractor_value = {**value, "amount": amount}
        clauses.append(
            {
                "id": clause_id,
                "document_id": identifier,
                "rule_key": f"{topic}.main",
                "topic": topic,
                "period": period,
                "scope": {"countries": [country], "employment_types": ["contractor"]},
                "value": contractor_value,
                "relationships": [{"kind": "overrides", "target_id": f"{identifier}.main"}],
            }
        )
        passages[clause_id] = (
            f"For contractors, {topic} reimbursement is limited to "
            f"{value['currency']} {amount} {value['unit'].replace('_', ' ')}. "
            "This exception replaces the general limit only; "
            "documentation requirements still apply."
        )
    if edition == 2 and topic == "meals" and country == "US":
        clause_id = f"{identifier}.unresolved-bulletin"
        clauses.append(
            {
                "id": clause_id,
                "document_id": identifier,
                "rule_key": "meals.main",
                "topic": topic,
                "period": {"start": "2026-09-01", "end": None},
                "scope": {"countries": ["US"], "employment_types": ["employee"]},
                "value": {"kind": "money", "amount": 90, "currency": "USD", "unit": "per_day"},
                "relationships": [],
            }
        )
        passages[clause_id] = (
            "A September operations bulletin lists the employee meals limit "
            "as USD 90 per day. It provides no authority to replace the existing meals limit. "
            "The policy owner has not resolved the discrepancy."
        )
    metadata = {
        "id": identifier,
        "title": f"{TOPICS[topic][0]} · {country} · H{edition} 2026",
        "version": f"v{edition}",
        "published_on": "2025-12-15" if edition == 1 else "2026-06-15",
        "topic": topic,
        "clauses": clauses,
    }
    body = "\n\n".join(f"## {key}\n\n{text}" for key, text in passages.items())
    return (
        f"---\n{yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)}---\n\n"
        f"# {metadata['title']}\n\nSynthetic Northstar Works policy. "
        "For demonstration only; this is not a real employer's policy.\n\n" + body + "\n"
    )


def main() -> None:
    destination = ROOT / "corpus"
    destination.mkdir(exist_ok=True)
    for topic in TOPICS:
        for country in ("BR", "US"):
            for edition in (1, 2):
                path = destination / f"{topic}-{country.lower()}-v{edition}.md"
                path.write_text(make_document(topic, country, edition), encoding="utf-8")


if __name__ == "__main__":
    main()
