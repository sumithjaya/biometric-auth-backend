from .db import SessionLocal, engine, Base
from . import models

def seed_employees():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if not db.query(models.Employee).first():
            employees = [
                models.Employee(employee_id="E1001", name="Alice Perera", pin="1234"),
                models.Employee(employee_id="E1002", name="Sumith Jayasuriya", pin="5678"),
                models.Employee(employee_id="E1003", name="Rushan Silva", pin="4321"),
            ]
            db.add_all(employees)
            db.commit()
            print("✅ Test employees inserted")
        else:
            print("⚠️ Employees already exist — skipping insert")
    finally:
        db.close()

if __name__ == "__main__":
    seed_employees()
