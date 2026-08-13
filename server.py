# server.py
from flask import Flask, request
from flask_socketio import SocketIO, join_room, emit
import logging

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {}  # maps session ID to client_id

@app.route("/")
def index():
    return "SocketIO Real-time Server"

@socketio.on('connect')
def handle_connect():
    print("Client connected:", request.sid)

@socketio.on('register')
def handle_register(data):
    client_id = data
    join_room(client_id)
    clients[request.sid] = client_id
    print(f"Client {request.sid} registered as {client_id}")

@socketio.on('disconnect')
def handle_disconnect():
    client_id = clients.pop(request.sid, None)
    print(f"Client {request.sid} ({client_id}) disconnected")

@socketio.on('processed_data')
def handle_processed_data(data):
    client_id = data.get('client_id')
    print(client_id,"=================")
    emit('processed_data', data, room=client_id)

@socketio.on('progress')
def handle_processed_data(data):
    print(data,"---------------")
    emit('progress', data, room=data)

if __name__ == "__main__":
    socketio.run(app, port=5000,debug=False)
