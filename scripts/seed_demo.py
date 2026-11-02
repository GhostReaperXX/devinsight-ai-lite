"""Fill the database with demonstration data.

Run from the project root: python -m scripts.seed_demo --reset
"""

import argparse
import csv
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Issue, Project, User

SEED_FILE = Path("data/issues_seed.csv")

USERS = [
    ("Admin User", "admin@devinsight.example", "admin"),
    ("Lina Haddad", "lina@devinsight.example", "member"),
    ("Omar Saleh", "omar@devinsight.example", "member"),
    ("Sara Nasser", "sara@devinsight.example", "member"),
]

PROJECTS = [
    ("SHOP", "Online Store", "Web shop with catalogue, cart and checkout."),
    ("CARE", "Clinic Booking", "Appointment booking system for a medical clinic."),
    ("LEARN", "Learning Portal", "University portal for courses and grades."),
]


def seed(reset: bool) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.scalar(select(User.id).limit(1)) is not None:
            print("The database already has data. Use --reset to start again.")
            return

        users = {
            email: User(full_name=name, email=email, role=role)
            for name, email, role in USERS
        }
        projects = {
            key: Project(key=key, name=name, description=text)
            for key, name, text in PROJECTS
        }
        db.add_all(users.values())
        db.add_all(projects.values())
        db.flush()

        with SEED_FILE.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        for row in rows:
            assignee = users.get(row["assignee_email"])
            db.add(
                Issue(
                    project_id=projects[row["project_key"]].id,
                    reporter_id=users[row["reporter_email"]].id,
                    assignee_id=assignee.id if assignee else None,
                    title=row["title"],
                    description=row["description"],
                    category=row["category"],
                    priority=row["priority"],
                    status=row["status"],
                )
            )
        db.commit()
        print(f"Seeded {len(users)} users, {len(projects)} projects, {len(rows)} issues.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fill the database with demonstration data."
    )
    parser.add_argument(
        "--reset", action="store_true", help="delete all existing data first"
    )
    seed(parser.parse_args().reset)
