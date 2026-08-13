import os, re, importlib, time, string, random, sys
import json  # Import json for proper JSON serialization
from celery import Celery
from flask import Flask, request, Response, jsonify, send_from_directory, abort
from celery.events import EventReceiver
from kombu import Connection
import redis
import mysql.connector
from datetime import datetime
from kombu.utils.json import loads
import pymysql
from pymysql.cursors import DictCursor
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# CORS(app, origins=["http://localhost:3000", "null"])

#Configuration
SERVER_IP_ADDRESS = "144.126.136.20"
SERVER_PORT = "5000"
BASE_SCREENSHOTS_DIR = os.path.join(os.getcwd(), 'ScreenShot')

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(
    app.name,  # The first argument should match your module name
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)

celery.conf.update(app.config)

if not os.path.exists(BASE_SCREENSHOTS_DIR):
    os.makedirs(BASE_SCREENSHOTS_DIR)

def generate_random_id(length=8) :
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_mysql_connection():
    return pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="removal",
            cursorclass=DictCursor
        )

def get_website_name(filename):
    replacements = {
        r"(comus|comeu|com)$": ".com",
        r"(neteu|netus|net)$": ".net",
        r"(orgeu|orgus|org)$": ".org",
        r"(gov)$": ".gov",
        r"(io)$": ".io",
        r"(info)$": ".info",
        r"(ai)$": ".ai",
        r"(us)$": ".us",
        r"(run)$": ".run",
        r"(pro)$": ".pro",
        r"(co)$": ".co"
    }
    for pattern, replacement in replacements.items():
        if re.search(pattern, filename):
            return re.sub(pattern, replacement, filename)
    return filename

def take_screenshot_link(screenshot_path):
    try:
        if screenshot_path is None:
            return ""
        
        parts = screenshot_path.split("ScreenShot\\", 1)[-1]
        formatted_path = parts.replace("\\", "/")

        screenshot_url = f"http://{SERVER_IP_ADDRESS}:{SERVER_PORT}/ScreenShot/{formatted_path}"
        print("screenshot-link ---------------------------------" + screenshot_url)
        return screenshot_url

    except Exception as e:
        return ""

@celery.task(bind=True)
def run_modules(self, dataRow, in_user_email, name):
    print("---------------------celery starting-----------------")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)  # Insert at start for priority
    results = []

    self.update_state(state='PENDING')
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(1, 11) :
        time.sleep(30)
        results.append(i + "website is finished!")
        self.update_state(state='PROGRESS', meta={'current': len(results), 'results' : results})
    # for filename in os.listdir(current_dir):
    #     if filename.endswith(".py") and filename not in ["app.py", "__init__.py"]:
    #         module_name = filename[:-3]
    #         module = importlib.import_module(module_name)
    #         website_name = get_website_name(module_name)
            
    #         result = {
    #             "website": website_name,
    #             "status": "Processing...",
    #             "screenshot_path": None,
    #             "screenshot_link": None
    #         }

    #         try:
    #             # Run module function dynamically
    #             print("-------------start-----------------------")
    #             screenshot_path = getattr(module, module_name)(dataRow, website_name, in_user_email, run_mode="non-headless")
                
    #             # Assume module returns a screenshot URL (modify as needed)
    #             result["status"] = "Success"
    #             result["screenshot_path"] = screenshot_path
    #             if screenshot_path is not None:
    #                 result["screenshot_link"] = take_screenshot_link(screenshot_path)

    #         except Exception as e:
    #             result["status"] = f"Error: {str(e)}"

    #         results.append(result)
    #         self.update_state(state='PROGRESS', meta={'current': len(results), 'total': len(os.listdir(current_dir)), 'results' : results})
    #         # Stream JSON response
    #         # yield f"data: {json.dumps(result)}\n\n"  # Use json.dumps to ensure proper JSON formatting
    #         time.sleep(5)  # Simulate processing delay

    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(end_time)
    self.update_state(state='SUCCESS', meta={'results' : results})
    conn = get_mysql_connection()
    cursor = conn.cursor()

    
    cursor.execute("INSERT INTO removal_status (task_id, task_status, person_name, person_email, start_time, end_time) VALUES (%s, %s, %s, %s, %s, %s)", (self.request.id, "SUCCESS", name, in_user_email, start_time, end_time))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    print("------------------celery ending--------------------------")
    return results

@app.route('/api/removeperson', methods=['POST', 'GET'])
def start_removal():
    verification_email = request.args.get("verification_email")
    user_email = request.args.get("user_email")
    title = request.args.get("title")
    name = request.args.get("name")
    age = request.args.get("age")
    birth_day = request.args.get("birth_day")
    birth_month = request.args.get("birth_month")
    birth_year = request.args.get("birth_year")
    address = request.args.get("address")
    area_code = request.args.get("area_code")
    phone_number = request.args.get("phone_number")
    street = request.args.get("street")
    apartment = request.args.get("apartment")
    city = request.args.get("city")
    state = request.args.get("state")
    zip_code = request.args.get("zip_code")
    county = request.args.get("county")
    advertising_id = request.args.get("advertising_id")
    job_title = request.args.get("job_title")
    business_name = request.args.get("business_name")
    linkedin_profile = request.args.get("linkedin_profile")
    status = request.args.get("status")

    dataRow = {
        "Verification Email": verification_email,
        "User Email": user_email,
        "Title": title,
        "Name": name,
        "Age": age,
        "Birth Day": birth_day,
        "Birth Month": birth_month,
        "Birth Year": birth_year,
        "Address": address,
        "Area Code": area_code,
        "Phone Number": phone_number,
        "Street": street,
        "Apartment": apartment,
        "City": city,
        "State": state,
        "Zipcode": zip_code,
        "County": county,
        "Advertising Id": advertising_id,
        "Job Title": job_title,
        "Business Name": business_name,
        "LinkedIn Profile": linkedin_profile,
        "Status": status
    }

    in_user_email = user_email

    #Generate a unique task ID
    task_id = generate_random_id()

    #Start background task
    task = run_modules.apply_async(args=[dataRow, in_user_email, name], task_id=task_id)

    return jsonify({"task_id" : task_id}), 202

    # return Response(run_modules_and_stream_results(dataRow, in_user_email), content_type="text/event-stream")

@app.route('/api/removalstatus/<task_id>', methods=['GET'])
def get_removal_status(task_id) :
    task = run_modules.AsyncResult(task_id)

    if task.state == 'PENDING' :
        return jsonify({'status' : 'Pending', 'message' : 'Task is waiting to start.'}), 202
    elif task.state == 'PROGRESS' :
        return jsonify({'status' : 'In Progress', "progrss": task.info}), 202
    elif task.state == 'SUCCESS' :
        return jsonify({"status" : 'Completed', 'results': task.result}), 200

@app.route('/api/tasklist', methods=['GET'])
def get_task_list():

    task_list = {
        "completed": {"count": 0, "tasks": []},
        "running": {"count": 0, "tasks": []},
        "pending": {"count": 0, "tasks": []}
    }

     # Get Celery inspector
    inspector = celery.control.inspect()

    active_tasks = inspector.active() or {}
    reserved_tasks = inspector.reserved() or {}
    scheduled_tasks = inspector.scheduled() or {}

    for worker, tasks in active_tasks.items():
        for task in tasks:
            task_id = task["id"]
            task_args = task["args"]  # Extract arguments
            
            task_item = {
                "task_id" : task_id,
                "task_status_link" : f"http://{SERVER_IP_ADDRESS}:{SERVER_PORT}/api/removalstatus/{task["id"]}",
                "person_email" : task_args[1] if len(task_args) > 1 else "N/A",
                "person_name" : task_args[2] if len(task_args) > 2 else "N/A"
            }
       
            task_list["running"]["tasks"].append(task_item)
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    queue_name = "celery"
    pending_tasks = redis_client.lrange(queue_name, 0, -1)
    print(len(pending_tasks))

    for task in pending_tasks:
        try:
            task_data = loads(task)
            if "headers" in task_data and "id" in task_data["headers"]:
                task_list["pending"]["tasks"].append(task_data["headers"]["id"])
        except Exception as e:
            print(f"Error processing task: {e}")

    # Completed tasks
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM removal_status WHERE task_status = %s", ("SUCCESS", ))
    completed_tasks = cursor.fetchall()

    for task in completed_tasks:
        task_item = {
            "task_id": task["task_id"],
            "person_email": task["person_email"],
            "person_name": task["person_name"],
            "start_time": task["start_time"],
            "end_time": task["end_time"]
        }

        task_list["completed"]["tasks"].append(task_item)

    cursor.close()
    conn.close()

    # Update counts
    task_list["completed"]["count"] = len(task_list["completed"]["tasks"])
    task_list["running"]["count"] = len(task_list["running"]["tasks"])
    task_list["pending"]["count"] = len(task_list["pending"]["tasks"])
    
    total_tasks = sum([task_list[state]["count"] for state in task_list])

    return jsonify({
        "task_list": task_list,
        "total_tasks": total_tasks
    })

@app.route("/ScreenShot/<date>/<filename>")
def serve_screenshot(date, filename):
    date_dir = os.path.join(BASE_SCREENSHOTS_DIR, date)
    # Check if the date directory exists
    if not os.path.exists(date_dir):
        abort(404, description="Date directory not found.")

    file_path = os.path.join(date_dir, filename)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        abort(404, description="Screenshot file not found.")

    return send_from_directory(date_dir, filename)

# Custom error handler for 404
@app.errorhandler(404)
def not_found_error(error):
    return {
        "error": "Not Found",
        "message": str(error.description)
    }, 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)