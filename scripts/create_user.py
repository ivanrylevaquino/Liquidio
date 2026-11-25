#!/usr/bin/env python3
"""
CLI Bootstrap Script to create a new user account.
Prompts interactively for username, full name, and password with no defaults.
"""
import sys
import os
import getpass

# Ensure repo root is in python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository

def main():
    print("=" * 60)
    print(" Liquidio - Create User Account CLI")
    print("=" * 60)

    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = UserRepository.get_by_username(db, username)
        if existing:
            print(f"Error: User '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        full_name = input("Enter full name: ").strip()
        if not full_name:
            print("Error: Full name cannot be empty.", file=sys.stderr)
            sys.exit(1)

        email = input("Enter email (optional, press Enter to skip): ").strip() or None

        while True:
            password = getpass.getpass("Enter password (min 8 chars): ")
            if len(password) < 8:
                print("Error: Password must be at least 8 characters long.")
                continue
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match. Please try again.")
                continue
            break

        pwd_hash = hash_password(password)

        user = User(
            username=username,
            password_hash=pwd_hash,
            full_name=full_name,
            role="USER",
            email=email,
            is_active=True
        )
        created = UserRepository.create(db, user)

        # Log CLI action to append-only audit trail
        ActivityLogRepository.insert(
            db=db,
            action_type="USER_CREATE_CLI",
            entity_name="users",
            entity_id=created.id,
            user_id=None,
            details={"username": created.username, "full_name": created.full_name}
        )

        print(f"\n[SUCCESS] User '{username}' successfully created with ID {created.id}.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
