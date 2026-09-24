"""Main module"""

import json
import logging
import os
import uuid
import glob

import config
import constants as con
import db_helper
import helper
from flask import Flask, request, send_file
from flask_cors import CORS


helper.configure_logging()
db_helper.init_main_db()

app = Flask(__name__)
CORS(app)


def get_grocery_category_data(category_id):
    base_folder = os.path.join(app.static_folder, "data", "grocery", "categories")
    requested_filename = f"{category_id}.json" if category_id else ""
    requested_path = os.path.join(base_folder, requested_filename)

    if not requested_filename or not os.path.exists(requested_path):
        requested_path = os.path.join(base_folder, "tantsuyut_vse.json")

    with open(requested_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/grocery/category", methods=["POST"])
def grocery_category_get():
    category_id = request.form.get("category_id", None)
    try:
        category_json = get_grocery_category_data(category_id)
    except Exception as e:
        logging.exception("Failed to load grocery category data")
        return ("Failed to load category", 500)

    return {"category": json.dumps(category_json, ensure_ascii=False)}


@app.route("/kv/get", methods=["POST"])
def get_kv_store():
    """Return KV store JSON by path under static/kv"""
    kv_path = request.form.get("kv_path", None)
    if not kv_path:
        return ("Missing kv_path", 400)

    # Build absolute path under static/kv and prevent path traversal
    base_folder = os.path.join(app.static_folder, "kv")
    requested_path = os.path.normpath(os.path.join(base_folder, kv_path))
    if not requested_path.startswith(os.path.abspath(base_folder)):
        return ("Invalid path", 400)
    if not os.path.exists(requested_path):
        return (f"KV file not found: {kv_path}", 404)

    with open(requested_path, "r", encoding="utf-8") as f:
        kv_json = json.load(f)

    # Return as string to be consistent with existing config response pattern
    return {"kv_store": json.dumps(kv_json, ensure_ascii=False)}


@app.route("/track/create", methods=["POST"])
def create_track():
    """Add track config to database"""
    track_id = request.form.get("track_id", None)
    user_guid = request.form.get("user_guid", None)
    delete_existing = request.form.get("delete_existing", False)
    if not track_id:
        return ("Missing track_id", 400)
    upload_folder = os.path.join(con.DATA_FOLDER, track_id)
    helper.check_folder(upload_folder)
    db_path = os.path.join(upload_folder, f"{track_id}.db")

    if os.path.exists(db_path) and not delete_existing:
        print(f"Track with id {track_id} already exists, choose another")
        return (f"Track with id {track_id} already exists, choose another", 400)
    elif os.path.exists(db_path) and delete_existing:
        delete_track(track_id)

    if not request.files:
        return ("Missing config file", 400)

    for config in request.files:
        file = request.files[config]
        filename = file.filename

        logging.info(f"Loading document {filename}.")
        upload_path = os.path.join(upload_folder, filename)

        file.save(upload_path)

        logging.info(f"Success. {filename} is loaded.")
    
    config_json = json.load(open(upload_path, 'r', encoding='utf-8'))

    db_helper.register_track(track_id, config_json, user_guid)
    db_helper.init_track_db(db_path)
    db_helper.update_track(db_path, config_json)

    return {"track_id": track_id}


@app.route("/track/get", methods=["POST"])
def get_track():
    """Get track config"""
    # if not authorized(request):
    #     return ("Not authorized", 403)

    track_id = request.form.get("track_id", None)

    print(f"track_id: {track_id}")

    if not track_id:
        return ("Missing track_id", 400)
    db_path = os.path.join(con.DATA_FOLDER, track_id, f"{track_id}.db")
    if not os.path.exists(db_path):
        return (f"Track with id {track_id} doesn't exist", 400)
    
    #debug
    upload_folder = os.path.join(con.DATA_FOLDER, track_id)
    config_file = glob.glob(os.path.join(upload_folder, '*.json'))[0]
    config_data = json.load(open(config_file, 'r', encoding='utf-8'))

    # config_data = json.dumps(db_helper.get_track(db_path))
    config_data = json.dumps(config_data)

    return {"config": config_data, "track_mtime": os.path.getmtime(config_file)}


def delete_track(track_id):
    """Delete track"""
    if not track_id:
        return ("Missing track_id", 400)
    db_path = os.path.join(con.DATA_FOLDER, track_id, f"{track_id}.db")
    try:
        os.remove(db_path)
    except Exception as e:
        print(f"Can't delete track DB file, cleaning DB tables instead.")
        db_helper.clean_track_db(track_id)

    # delete track from main db regardless
    db_helper.delete_track(track_id)

    return {"track_id": track_id}


@app.route("/event/add", methods=["POST"])
def add_activity():
    """Log event"""
    # if not authorized(request):
    #     return ("Not authorized", 403)

    track_id = request.form.get("track_id", None)
    if not track_id:
        return ("Missing track_id", 400)
    event_id = str(uuid.uuid4())
    event_name = request.form.get("event_name", None)
    event_data = request.form.get("event_data", None)

    db_path = os.path.join(con.DATA_FOLDER, track_id, f"{track_id}.db")

    if not os.path.exists(db_path):
        print(f"Track with id {track_id} doesn't exist")
        return (f"Track with id {track_id} doesn't exist", 400)

    db_helper.add_event(db_path, event_id, event_name, event_data)

    logging.info(
        "Added event: track_id=%s event_id=%s event_name=%s",
        track_id,
        event_id,
        event_name,
    )

    return {"event_id": event_id}


@app.route("/event/get", methods=["POST"])
def get_events():
    """Get events from track"""
    # if not authorized(request):
    #     return ("Not authorized", 403)

    track_id = request.form.get("track_id", None)
    if not track_id:
        return ("Missing track_id", 400)
    db_path = os.path.join(con.DATA_FOLDER, track_id, f"{track_id}.db")

    if not os.path.exists(db_path):
        print(f"Track with id {track_id} doesn't exist")
        return (f"Track with id {track_id} doesn't exist", 400)

    events = db_helper.get_events(db_path)
    
    return {"events": events}


# Not API calls treated like static queries
@app.route("/<path:path>")
def route_frontend(path):
    """Route static requests"""
    # ...could be a static file needed by the front end that
    # doesn't use the `static` path (like in `<script src="bundle.js">`)
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_file(file_path)
    # ...or should be handled by the SPA's "router" in front end
    else:
        index_path = os.path.join(app.static_folder, "index.html")
        return send_file(index_path)


@app.route("/user/authorized", methods=["POST"])
def is_authorized():
    """Is user authorized"""
    if not authorized(request):
        return ("Not authorized", 403)

    return {"authorized": True}


def authorized(request):
    user_token = request.form.get("token", None)
    return helper.token_is_valid(user_token)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=config.API_PORT)