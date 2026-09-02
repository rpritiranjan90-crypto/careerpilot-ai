"""Cloud Database Migration & Health Verification Script.

Usage:
  python scripts/migrate_cloud_db.py --url="postgresql://postgres:password@db.project.supabase.co:5432/postgres"
"""

import argparse
import os
import subprocess
import sys
import sqlalchemy
from sqlalchemy import text


def main():
    parser = argparse.ArgumentParser(description="Migrate and verify Cloud PostgreSQL database.")
    parser.add_argument("--url", help="Database connection URL", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()

    db_url = args.url
    if not db_url:
        print("[ERROR] DATABASE_URL is not set. Provide --url or set the DATABASE_URL environment variable.")
        sys.exit(1)

    print(f"\n[INFO] Connecting to Cloud PostgreSQL: {db_url.split('@')[-1] if '@' in db_url else '...'}")

    try:
        engine = sqlalchemy.create_engine(db_url, connect_args={"connect_timeout": 10})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
            print(f"[OK] Database connection successful!\n     Version: {result}\n")
    except Exception as e:
        print(f"[ERROR] Could not connect to database: {e}")
        sys.exit(1)

    print("[INFO] Running Alembic migrations to latest schema (001 -> 002 -> 003)...")
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url

    res = subprocess.run(["alembic", "upgrade", "head"], cwd=backend_dir, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Migration failed:\n{res.stderr}")
        sys.exit(1)

    print(f"[OK] Migrations applied successfully!\n{res.stdout}")
    print("[SUCCESS] Cloud database is 100% synchronized and ready for production!")


if __name__ == "__main__":
    main()
