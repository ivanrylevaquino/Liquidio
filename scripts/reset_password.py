#!/usr/bin/env python3
"""
CLI Script to reset a user's password.
Prompts interactively for username and new password with no defaults.
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
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository

def main():
    print("=" * 60)
    print(" Liquidio - Reset User Password CLI")
    print("=" * 60)

    username = input("Enter username: ").strip()
    if not username:
        print("Error: Username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        user = UserRepository.get_by_username(db, username)
        if not user:
            print(f"Error: User '{username}' does not exist.", file=sys.stderr)
            sys.exit(1)

        while True:
            new_password = getpass.getpass("Enter new password (min 8 chars): ")
            if len(new_password) < 8:
                print("Error: Password must be at least 8 characters long.")
                continue
            confirm = getpass.getpass("Confirm new password: ")
            if new_password != confirm:
                print("Error: Passwords do not match. Please try again.")
                continue
            break

        pwd_hash = hash_password(new_password)
        UserRepository.update_password(db, user, pwd_hash)

        # Log CLI action to append-only audit trail
        ActivityLogRepository.insert(
            db=db,
            action_type="PASSWORD_RESET_CLI",
            entity_name="users",
            entity_id=user.id,
            user_id=None,
            details={"username": user.username}
        )

        print(f"\n[SUCCESS] Password for user '{username}' has been successfully reset.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
