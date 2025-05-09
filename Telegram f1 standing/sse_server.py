from flask import Flask, Response
from threading import Thread
import json
from datetime import datetime
import time
import uuid
from models import MessageContext, F1Standings, Driver

app = Flask(__name__)
latest_standings = None

def event_stream():
    global latest_standings
    while True:
        if latest_standings:
            data = latest_standings.model_dump_json()
            yield f"data: {data}\n\n"
        time.sleep(60)

@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/standings')
def get_standings():
    global latest_standings
    return latest_standings.model_dump_json() if latest_standings else '{}'

def update_standings(message_context: MessageContext):
    global latest_standings
    latest_standings = message_context
    return latest_standings

def start_sse_server():
    def run_server():
        app.run(host='localhost', port=5000, threaded=True)
    
    thread = Thread(target=run_server)
    thread.daemon = True
    thread.start()