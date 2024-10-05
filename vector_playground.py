# vector_playground.py (main script)

import io
import os
import sys
import traceback

import cv2
from anki_vector import Robot
from anki_vector.exceptions import VectorNotFoundException

from lib.config_handler import load_config_file, load_sdk_configuration, module_logger
from lib.intent_controller import IntentLoader
from lib.logging_handler import CustomLogger
from lib.robot_controller import RobotController
from flask import Flask, jsonify, request, render_template, session, redirect, url_for, send_file
from flask_session import Session
import uuid
import time
import threading

app_name = "vector_playground"

log_level = 1
shutdown = False

root_path = os.getcwd()
config_file = 'config.json'
sdk_config_file = 'sdk_config.ini'
log_path = os.path.join(root_path, 'log')
log_file_name = f"{app_name}.log"
config_path = os.path.join(root_path, 'etc')
var_path = os.path.join(root_path, 'var')

if not os.path.exists(log_path):
    os.makedirs(log_path)

if not os.path.exists(config_path):
    os.makedirs(config_path)

if not os.path.exists(var_path):
    os.makedirs(var_path)

logging_instance = CustomLogger(log_level, app_name, os.path.join(log_path, log_file_name))

try:
    config_data = load_config_file(os.path.join(config_path, config_file))
    logging_instance.set_log_level(config_data["log_level"])
    logger = logging_instance.logger
    logger.info("Loaded Config File")
except FileNotFoundError as fnfe:
    print(f"Error: {fnfe}")
    sys.exit(1)
except ValueError as ve:
    print(f"Configuration error: {ve}")
    sys.exit(1)
except RuntimeError as re:
    print(f"Runtime error: {re}")
    sys.exit(1)
except Exception as e:
    print(f'Unexpected error while loading configuration: {e}')
    sys.exit(1)

try:
    sdk_config_data = load_sdk_configuration(os.path.join(config_data.get("sdk_config_path", config_path), sdk_config_file))
    logger.info("Loaded Vector SDK Configration")
except FileNotFoundError as e:
    logger.error(e)
    sys.exit(1)
except ValueError as e:
    logger.error(e)
    sys.exit(1)
except Exception as e:
    logger.error(f'Unexpected error while <<loading>> Vector SDK configuration : {e}')
    sys.exit(1)

try:
    intent_loader = IntentLoader()
    logger.warning(intent_loader.user_intents)
except Exception as e:
    logger.error(e)
app = Flask(__name__, template_folder='templates', static_folder='static')

if not os.getenv('SECRET_KEY'):
    try:
        with open(os.path.join(config_path, 'secret_key'), 'rb') as f:
            app.config['SECRET_KEY'] = f.read()
    except FileNotFoundError:
        secret_key = os.urandom(24)
        with open(os.path.join(config_path, 'secret_key'), 'wb') as f:
            f.write(secret_key)
            app.config['SECRET_KEY'] = secret_key
else:
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Session Configuration
app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_PERMANENT'] = False
# app.config['SESSION_USE_SIGNER'] = True

# Cookie Configuration
# app.config['SESSION_COOKIE_SECURE'] = config_data["general"]["cookie_secure"]
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_DOMAIN'] = config_data["general"]["cookie_domain"]
# app.config['SESSION_COOKIE_NAME'] = config_data["general"]["cookie_name"]
# app.config['SESSION_COOKIE_PATH'] = config_data["general"]["cookie_path"]
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initializing the session
sess = Session()
sess.init_app(app)

# Global dictionary of controllers
controllers = {}
controllers_lock = threading.Lock()

def heartbeat_monitor():
    global shutdown
    while True:
        logger.debug(f'Running Heartbeat Loop')
        current_time = time.time()
        for serial, info in controllers.items():
            if info['status'] == 'controlled' and info['user_id']:
                if current_time - info['last_heartbeat'] > 10:  # Timeout in seconds
                    logger.debug(f"Releasing robot {serial} due to inactivity")
                    info['status'] = 'available'
                    info['user_id'] = None
        if shutdown:
            break
        time.sleep(5)

def robot_reconnector():
    global shutdown
    logger.info("Starting Robot Reconnector")
    while True:
        with controllers_lock:
            for serial, info in controllers.items():
                if info['status'] == 'disconnected':
                    if info.get("connect_tries") >= 5 and (time.time() - info.get("last_connect_try", time.time()) > 120):
                        controllers[serial]['connect_tries'] = 0
                        controllers[serial]['last_connect_try'] = 0
                        try_connection = True
                    elif info.get("connect_tries") <= 5 and (time.time() - info.get("last_connect_try", time.time()) > 30):
                        try_connection = True
                    else:
                        try_connection = False

                    if try_connection:
                        module_logger.info(f"Trying to reconnect to {info.get('name')} {info.get('serial')}")
                        threading.Thread(target=connect_robot, args=(info.get('bot_config', {}),)).start()

        if shutdown:
            break
        time.sleep(5)

def handle_control_lost(serial):
    logger.warning(f"Handling control lost for robot {serial}")
    with controllers_lock:
        robot_info = controllers.get(serial)
        if robot_info:
            # Update robot status to unavailable
            robot_info['status'] = 'disconnected'
            robot_info['user_id'] = None
            controllers[serial]['connect_tries'] = 0
            controllers[serial]['last_connect_try'] = 0

            # Stop the robot controller and disconnect the robot
            controller = robot_info['controller']
            if controller:
                controller.stop()
                logger.info(f"Controller stopped and robot disconnected for robot {serial}")
        else:
            logger.error(f"No robot info found for serial {serial}")

def connect_robot(bot_config):
    global shutdown

    if shutdown:
        return

    robot_serial = bot_config.get("serial")
    robot_name = bot_config.get("name")

    logger.info(f"Connecting robot {robot_name} {robot_serial}")
    robot = Robot(serial=robot_serial, config=bot_config)
    robot.serial = robot_serial
    robot.name = robot_name
    try:
        robot.connect()
        controller = RobotController(robot, config_data, intent_loader, on_control_lost_callback=handle_control_lost)

        controllers[robot_serial] = {
            'controller': controller,
            'serial': robot_serial,
            'name': robot_name,
            'status': 'available',
            'user_id': None,
            'connect_tries': 0,
            'last_connect_try': time.time(),
            'last_heartbeat': time.time(),
            'bot_config': bot_config
        }
        controller.start()
        logger.info(f"Connected to robot {robot_name} {robot_serial}")
    except VectorNotFoundException as e:
        if 'Unable to establish a connection to Vector.' in str(e):
            e = 'Unable to establish a connection to Vector.'
        logger.error(f"Could not connect to robot {robot_name} {robot_serial}: {e}")
        if robot_serial in controllers:
            controllers[robot_serial]['status'] = 'disconnected'
            controllers[robot_serial]['user_id'] = None
            controllers[robot_serial]['connect_tries'] += 1
            controllers[robot_serial]['last_connect_try'] = time.time()
        else:
            controllers[robot_serial] = {
                'controller': None,
                'serial': robot_serial,
                'name': robot_name,
                'status': 'disconnected',
                'user_id': None,
                'last_heartbeat': None,
                'connect_tries': 0,
                'last_connect_try': time.time(),
                'bot_config': bot_config
            }
    except Exception as e:
        if 'Failed to get control of Vector.' in str(e):
            message = f'Failed to get control of Vector: {robot.name} {robot_serial}'
        else:
            message = f"An unexpected error occurred while connecting to robot {robot.name} {robot_serial}: {e}"
        logger.error(message)
        if robot_serial in controllers:
            controllers[robot_serial]['status'] = 'disconnected'
            controllers[robot_serial]['user_id'] = None
            controllers[robot_serial]['connect_tries'] += 1
            controllers[robot_serial]['last_connect_try'] = time.time()
        else:
            controllers[robot_serial] = {
                'controller': None,
                'serial': robot_serial,
                'name': robot_name,
                'status': 'disconnected',
                'user_id': None,
                'last_heartbeat': None,
                'connect_tries': 0,
                'last_connect_try': time.time(),
                'bot_config': bot_config
            }

def initialize_robots():

    # Initialize each robot and its controller
    for bot_config in sdk_config_data:
        threading.Thread(target=connect_robot, args=(bot_config,)).start()

@app.before_request
def ensure_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())  # Generate a new UUID for the session
        logger.info(f"New session started with user_id: {session['user_id']}")
    else:
        logger.debug(f"Session already has user_id: {session['user_id']}")
@app.route('/')
def index():
    robot_list = []
    for serial, info in controllers.items():
        robot_list.append({
            'serial': serial,
            'status': info['status']
        })
    return render_template('index.html', robots=robot_list)

@app.route('/control/<serial>', methods=['GET'])
def control_robot(serial):
    robot_info = controllers.get(serial)
    if not robot_info:
        return "Robot not found", 404

    logger.debug(robot_info)

    if robot_info['status'] == 'controlled' and robot_info['user_id'] != session.get('user_id'):
        return "Robot is currently controlled by another user", 403

    if robot_info['status'] == 'disconnected' or robot_info["status"] == "unavailable":
        return "Robot is currently disconnected.", 404

    # Assign robot to the user
    session['user_id'] = session.get('user_id') or str(uuid.uuid4())
    robot_info['status'] = 'controlled'
    robot_info['user_id'] = session['user_id']
    robot_info['last_heartbeat'] = time.time()

    return render_template('control.html', serial=serial)

@app.route('/heartbeat/<serial>', methods=['POST'])
def heartbeat(serial):
    robot_info = controllers.get(serial)
    if not robot_info:
        return jsonify({'error': 'Robot not found'}), 404

    if robot_info['user_id'] != session.get('user_id'):
        return jsonify({'error': 'You are not controlling this robot'}), 403

    # Update the last heartbeat time
    robot_info['last_heartbeat'] = time.time()
    return jsonify({'status': 'ok'})

@app.route('/release/<serial>', methods=['POST'])
def release_robot(serial):
    robot_info = controllers.get(serial)
    if not robot_info:
        return jsonify({'error': 'Robot not found'}), 404

    if robot_info['user_id'] == session.get('user_id'):
        robot_info['status'] = 'available'
        robot_info['user_id'] = None
    return jsonify({'status': 'released'})

@app.route('/robots', methods=['GET'])
def get_robots():
    robot_list = list(controllers.keys())
    return jsonify({'robots': robot_list})

@app.route('/robots/<serial>/status', methods=['GET'])
def get_robot_status(serial):
    robot_info = controllers.get(serial)
    if not robot_info:
        return "Robot not found", 404

    controller = robot_info['controller']
    # Check if the user controls this robot
    if robot_info['user_id'] != session.get('user_id'):
        return "You are not controlling this robot", 403

    if controller:
        status = controller.status_handler.current_statuses
        return jsonify(status)
    else:
        return jsonify({'error': 'Robot not found'}), 404

@app.route('/robots/<serial>/camera_feed')
def camera_feed(serial):
    robot_info = controllers.get(serial)
    if not robot_info:
        return "Robot not found", 404

    controller = robot_info['controller']
    # Check if the user controls this robot
    if robot_info['user_id'] != session.get('user_id'):
        return "You are not controlling this robot", 403

    # Get the latest image from the camera stream
    image = controller.camera_stream.latest_image
    if image is not None:
        # Encode the image as JPEG
        ret, jpeg = cv2.imencode('.jpg', image)
        if ret:
            img_io = io.BytesIO(jpeg.tobytes())
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
        else:
            return "Failed to encode image", 500
    else:
        return "No image available", 503

@app.route('/robots/<serial>/user_intent', methods=['GET'])
def api_user_intent(serial):
    intent_to_run = None
    robot_info = controllers.get(serial)
    intent = request.args.get('intent')
    user_query = request.args.get('query')

    if not robot_info:
        return jsonify({'error': 'Robot not found'}), 404

    if robot_info['user_id'] != session.get('user_id'):
        return jsonify({'error': 'You are not controlling this robot'}), 403

    controller = robot_info['controller']

    # Check if query parameters exist
    if intent is None or user_query is None:
        return jsonify({'success': False, 'message': 'Missing required parameters.'}), 400

    try:
        for user_intent in intent_loader.user_intents:
            if user_intent.get('name') == intent:
                intent_to_run = user_intent
                break

        if intent_to_run:
            controller.intent_controller.run_user_intent(intent_to_run, user_query)
            return jsonify({'success': True}), 200
    except Exception as e:
        module_logger.exception(e)
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/robots/<serial>/intent_request', methods=['POST'])
def api_intent_request(serial):
    robot_info = controllers.get(serial)
    if not robot_info:
        return jsonify({'error': 'Robot not found'}), 404

    intent_data = request.get_json()
    if not intent_data:
        return jsonify({'error': 'Invalid or missing JSON data'}), 400



@app.route('/robots/<serial>/move_wheels', methods=['GET'])
def api_move_wheels(serial):
    robot_info = controllers.get(serial)
    left_wheel = request.args.get('left')
    right_wheel = request.args.get('right')

    if not robot_info:
        return jsonify({'success': False, 'message': 'Robot not found.'}), 404

    if robot_info['user_id'] != session.get('user_id'):
        return jsonify({'success': False, 'message': 'You are not controlling this robot'}), 403

    controller = robot_info['controller']

    # Check if both query parameters exist
    if left_wheel is None or right_wheel is None:
        return jsonify({'success': False, 'message': 'Missing required parameters.'}), 400

    try:
        # Convert query parameters to integers and validate their range
        left_wheel = int(left_wheel)
        right_wheel = int(right_wheel)

        if not (-200 <= left_wheel <= 200) or not (-200 <= right_wheel <= 200):
            return jsonify({'success': False, 'message': 'Malformed request.'}), 400
    except ValueError:
        # If conversion to integer fails
        return jsonify({'success': False, 'message': 'Malformed request.'}), 400


    controller.movement_controller.control_move_wheels(left_wheel, right_wheel)
    return jsonify({'success': False, 'message': f'Moving Wheels L{left_wheel} R{right_wheel}.'}), 200

@app.route('/robots/<serial>/move_lift', methods=['GET'])
def api_move_lift(serial):
    robot_info = controllers.get(serial)
    speed = request.args.get('speed')

    if not robot_info:
        return jsonify({'success': False, 'message': 'Robot not found.'}), 404

    if robot_info['user_id'] != session.get('user_id'):
        return jsonify({'success': False, 'message': 'You are not controlling this robot'}), 403

    controller = robot_info['controller']

    # Check if both query parameters exist
    if speed is None:
        return jsonify({'success': False, 'message': 'Missing required parameters.'}), 400

    try:
        # Convert query parameters to integers and validate their range
        speed = int(speed)

        if not (-10 <= speed <= 10):
            return jsonify({'success': False, 'message': 'Malformed request.'}), 400
    except ValueError:
        # If conversion to integer fails
        return jsonify({'success': False, 'message': 'Malformed request.'}), 400


    controller.movement_controller.control_move_lift(speed)
    return jsonify({'success': False, 'message': f'Moving Lift {speed}.'}), 200

@app.route('/robots/<serial>/move_head', methods=['GET'])
def api_move_head(serial):
    robot_info = controllers.get(serial)
    speed = request.args.get('speed')

    if not robot_info:
        return jsonify({'success': False, 'message': 'Robot not found.'}), 404

    if robot_info['user_id'] != session.get('user_id'):
        return jsonify({'success': False, 'message': 'You are not controlling this robot'}), 403

    controller = robot_info['controller']

    # Check if both query parameters exist
    if speed is None:
        return jsonify({'success': False, 'message': 'Missing required parameters.'}), 400

    try:
        # Convert query parameters to integers and validate their range
        speed = int(speed)

        if not (-10 <= speed <= 10):
            return jsonify({'success': False, 'message': 'Malformed request.'}), 400
    except ValueError:
        # If conversion to integer fails
        return jsonify({'success': False, 'message': 'Malformed request.'}), 400


    controller.movement_controller.control_move_head(speed)
    return jsonify({'success': False, 'message': f'Moving Head {speed}.'}), 200


def main():
    global shutdown

    initialize_robots()

    threading.Thread(target=heartbeat_monitor, daemon=True).start()
    threading.Thread(target=robot_reconnector, daemon=True).start()

    try:
        # Run the Flask app
        app.run(host='0.0.0.0', port=8012, threaded=True)
    except KeyboardInterrupt:
        shutdown = True
        pass
    finally:
        # Stop all robots gracefully
        for controller in controllers.values():
            robot_controller = controller["controller"]
            if robot_controller:
                threading.Thread(target=robot_controller.stop).start()

if __name__ == '__main__':
    main()