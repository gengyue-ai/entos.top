"""
Tunnel Server - Polls DB for tasks, relays to connected agent
Run: python tunnel_server.py
"""
import asyncio, json, sqlite3, os, time
import websockets

DB_PATH = os.path.expanduser("~/self-evolving/evolution.db")
agents = set()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id TEXT PRIMARY KEY, progress INTEGER DEFAULT 0,
            message TEXT DEFAULT '', output TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            sent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

async def poll_tasks():
    """Periodically check for unsent tasks and relay to connected agents"""
    while True:
        await asyncio.sleep(2)
        if not agents:
            continue
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM agent_tasks WHERE sent=0 AND progress=0").fetchall()
        for row in rows:
            # Load params stored as JSON in output column
            params = {}
            try:
                stored = row["output"] or "{}"
                params = json.loads(stored)
            except:
                pass
            task = {"type": "task", "task_id": row["id"], "params": params}
            # Send to all connected agents
            dead = set()
            for ws in agents:
                try:
                    await ws.send(json.dumps(task))
                    conn.execute("UPDATE agent_tasks SET sent=1 WHERE id=?", (row["id"],))
                    conn.commit()
                    print(f"[>] Sent task {row['id']}")
                except:
                    dead.add(ws)
            for ws in dead:
                agents.discard(ws)
        conn.close()

async def handler(ws):
    agents.add(ws)
    print(f"[+] Agent connected ({len(agents)})")
    try:
        async for msg in ws:
            data = json.loads(msg)
            if data.get("type") == "task_update":
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT OR REPLACE INTO agent_tasks (id, progress, message, output) VALUES (?,?,?,?)",
                             (data["task_id"], data.get("progress",0), data.get("message",""), data.get("output","")))
                conn.commit()
                conn.close()
                print(f"[<] {data['task_id']}: {data.get('progress',0)}%")
    except:
        pass
    finally:
        agents.discard(ws)
        print(f"[-] Agent disconnected ({len(agents)})")

async def main():
    init_db()
    print(f"Tunnel on 0.0.0.0:8768")
    async with websockets.serve(handler, "0.0.0.0", 8768):
        await poll_tasks()

if __name__ == "__main__":
    asyncio.run(main())
