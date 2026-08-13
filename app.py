# app.py
import sys
import mysql.connector
import socketio
import json
import time
import sys

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mattrhorn'
}
sio = socketio.Client()
sio.connect('http://localhost:5000')

def process_element(request_id, client_id, filename, info):
    result = {
        'request_id': request_id,
        'client_id': client_id,
        'filename': filename,
        'info': info
    }

    # conn = mysql.connector.connect(**db_config)
    # cursor = conn.cursor()
    # cursor.execute("INSERT INTO results (request_id, original, processed) VALUES (%s, %s, %s)",
    #                (request_id, element_data, result['processed']))
    # conn.commit()
    # cursor.close()
    # conn.close()
    # print(result)
    time.sleep(5)
    sio.emit('processed_data', result)

if __name__ == "__main__":
    request_id = sys.argv[1]
    client_id = sys.argv[2]
    filenames = json.loads(sys.argv[3])  # Decode the JSON string
    info = json.loads(sys.argv[4])       # Decode the JSON string

    for filename in filenames:
        process_element(request_id, client_id, filename,info)
    
