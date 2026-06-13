import subprocess
import json
import datetime
import os
import sqlite3

# Check if running on Render or if team-db is not available
IS_RENDER = os.environ.get("RENDER") == "true" or os.environ.get("USE_SQLITE") == "true"
DB_PATH = os.environ.get("DATABASE_URL", "tradevision.db")

def run_query(sql):
    if IS_RENDER:
        # SQLite implementation for Render/External environments
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # Basic table initialization if not exists
            if "signals" in sql.lower() or "watchlist" in sql.lower():
                cursor.execute("CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, timestamp TEXT, price REAL, verdict TEXT, hc_score INTEGER, status TEXT, exit_price REAL)")
                cursor.execute("CREATE TABLE IF NOT EXISTS watchlist (ticker TEXT PRIMARY KEY, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                conn.commit()

            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return []
        except Exception as e:
            print(f"SQLite Error: {e}")
            return []
        finally:
            conn.close()
    else:
        # Internal team-db implementation
        result = subprocess.run(["team-db", sql], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"DB Error: {result.stderr}")
            return []
        try:
            return json.loads(result.stdout)
        except:
            return []

def log_signal(ticker, price, verdict, hc_score):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Escape single quotes for SQL
    verdict_escaped = verdict.replace("'", "''")
    sql = f"INSERT INTO signals (ticker, timestamp, price, verdict, hc_score, status) VALUES ('{ticker}', '{timestamp}', {price}, '{verdict_escaped}', {hc_score}, 'Open')"
    run_query(sql)

def get_signals():
    return run_query("SELECT * FROM signals ORDER BY timestamp DESC")

def update_signal_status(signal_id, status, exit_price):
    sql = f"UPDATE signals SET status = '{status}', exit_price = {exit_price} WHERE id = {signal_id}"
    run_query(sql)
