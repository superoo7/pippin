# server.py

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import shared_data
from threading import Thread

app = FastAPI()

# Mount the 'static' directory for static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the index.html template
@app.get("/")
async def get():
    return HTMLResponse(open("templates/index.html").read())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    memory = Memory()
    while True:
        # Fetch the last 10 activity logs from the database
        async with memory.get_db_connection() as db:
            cursor = await db.execute('''
                SELECT timestamp, activity, result, duration, state_changes
                FROM activity_logs
                ORDER BY id DESC
                LIMIT 10
            ''')
            rows = await cursor.fetchall()
            activity_history = []
            for row in rows:
                timestamp, activity, result, duration, state_changes_str = row
                # Parse state_changes JSON string
                state_changes = json.loads(state_changes_str) if state_changes_str else {}
                activity_history.append({
                    'timestamp': timestamp,
                    'activity': activity,
                    'result': result,
                    'duration': duration,
                    'state_changes': state_changes
                })

        # Prepare data to send
        data = {
            'current_activity': shared_data.current_activity,
            'state': shared_data.state.to_dict(),
            'activity_history': activity_history
        }
        await websocket.send_json(data)
        await asyncio.sleep(1)
        await asyncio.sleep(1)

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Run the FastAPI server in a separate thread
server_thread = Thread(target=run_server, daemon=True)
server_thread.start()