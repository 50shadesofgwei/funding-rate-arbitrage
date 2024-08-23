from FlaskServer import create_app
from flask_socketio import SocketIO, emit

(sio, app) = create_app()

# SocketIO event handlers
@sio.on('connect')
def handle_connect():
    print('Client connected')

@sio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@sio.on('log')
def handle_log(data):
    print(data)
    emit('log', data)

# Socket IO events
@sio.event
def log(data):
    """Emits log data to the client.
    Client should listen for 'log' event.
    Log data should be popped on LogsTable component in front-end.
    """
    emit('log', data)
    


def run():
    sio.run(app)

if __name__ == "__main__":
    run()