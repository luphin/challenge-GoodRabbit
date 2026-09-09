import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.models import Employee, ShiftRule, ShiftRuleEmployee

RULES = [
    {"name": "Jornada Completa", "max_hours_day": 8, "max_hours_week": 40},
    {"name": "Media Jornada", "max_hours_day": 5, "max_hours_week": 20},
]

EMPLOYEES = [
    {
        "name": "Ana",
        "last_name": "García",
        "phone_number": "+56911112222",
        "email": "ana.garcia@demo.cl",
        "rule": "Jornada Completa",
    },
    {
        "name": "Bruno",
        "last_name": "Díaz",
        "phone_number": "+56933334444",
        "email": "bruno.diaz@demo.cl",
        "rule": "Jornada Completa",
    },
    {
        "name": "Carla",
        "last_name": "Rojas",
        "phone_number": "+56955556666",
        "email": "carla.rojas@demo.cl",
        "rule": "Media Jornada",
    },
]


def run() -> None:
    with SessionLocal() as db:
        rules_by_name: dict[str, ShiftRule] = {}
        for data in RULES:
            rule = db.query(ShiftRule).filter_by(name=data["name"]).one_or_none()
            if rule is None:
                rule = ShiftRule(**data)
                db.add(rule)
                print(f"[+] ShiftRule creada: {rule.name}")
            rules_by_name[rule.name] = rule

        for data in EMPLOYEES:
            employee = db.query(Employee).filter_by(email=data["email"]).one_or_none()
            if employee is None:
                employee = Employee(
                    name=data["name"],
                    last_name=data["last_name"],
                    phone_number=data["phone_number"],
                    email=data["email"],
                )
                db.add(employee)
                db.flush()
                print(f"[+] Employee creado: {employee.email}")
            if employee.rule_assignment is None:
                db.add(
                    ShiftRuleEmployee(
                        employee_id=employee.id,
                        shift_rule_id=rules_by_name[data["rule"]].shift_rule_id,
                    )
                )
                print(f"[+] Regla '{data['rule']}' asignada a {employee.email}")

        db.commit()
        print("Seed completado.")


if __name__ == "__main__":
    run()
