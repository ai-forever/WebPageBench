import logging
import os
import sqlite3
import constants as con
import helper
import json


def init_main_db():
    """Init main database"""
    db_path = os.path.join(con.DATA_FOLDER, con.MAIN_DB)
    helper.check_folder(con.DATA_FOLDER)

    if not os.path.isfile(db_path):
        logging.info(f"Creating main db: {db_path}")
        with sqlite3.connect(db_path) as db:
            db.execute(
                """create table tracks(
                        id integer primary key,
                        track_id text UNIQUE,
                        track_config text,
                        user_guid text,
                        is_active integer default 1 NOT NULL,
                        create_ts text
                    )"""
            )

            db.execute("create table version(id integer primary key, version text)")
            db.execute("insert into version(version) values (?)", (con.DB_VERSION,))


def ensure_track_schema(db_path):
    """Ensure track DB has required tables: config and events.
    Creates DB file and tables if missing.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        helper.check_folder(db_dir)

    with sqlite3.connect(db_path) as db:
        db.execute(
            """create table if not exists config(
                        id integer primary key,
                        track_config text
                    )"""
        )
        db.execute(
            """create table if not exists events(
                        id integer primary key,
                        event_id text,
                        event_name text,
                        event_data text,
                        event_ts text
                    )"""
        )


def get_track_from_main_db(track_id):
    """Get track from main database by id"""
    db_path = os.path.join(con.DATA_FOLDER, con.MAIN_DB)

    with sqlite3.connect(db_path) as db:
        data = db.execute(
            """select
                        track_id,
                        track_config,
                        user_guid,
                        is_active
                    from
                        tracks
                    where
                        track_id = ?""",
            (track_id,),
        ).fetchone()

    if data:
        return {
            "track_id": data[0],
            "track_config": data[1],
            "user_guid": data[2],
            "is_active": data[3],
        }
    else:
        return None


def init_track_db(db_path):
    """Init track database"""
    helper.check_folder(con.DATA_FOLDER)

    if not os.path.isfile(db_path):
        logging.info(f"Creating track db: {db_path}")
        ensure_track_schema(db_path)


def register_track(track_id, track_config, user_guid):
    """Register track in main database"""
    db_path = os.path.join(con.DATA_FOLDER, con.MAIN_DB)
    curr_time = helper.get_curr_time()

    with sqlite3.connect(db_path) as db:
        db.execute(
            """insert into tracks(track_id, track_config, user_guid, create_ts) values (?, ?, ?, ?)""",
            (track_id, json.dumps(track_config, ensure_ascii=False), user_guid, curr_time),
        )


def get_track(db_path):
    """Get track from track database"""
    with sqlite3.connect(db_path) as db:
        data = db.execute(
            """select
                        track_config
                    from
                        config"""
        ).fetchone()

    return json.loads(data[0])


def update_track(db_path, track_config):
    """Insert or update track"""
    ensure_track_schema(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            """insert or replace into config(track_config) values (?)""",
            (json.dumps(track_config, ensure_ascii=False),),
        )

def delete_track(track_id):
    """Delete track from main db"""
    db_path = os.path.join(con.DATA_FOLDER, con.MAIN_DB)
    with sqlite3.connect(db_path) as db:
        db.execute("delete from tracks where track_id = ?", (track_id,))


def clean_track_db(track_id):
    """Clean track database"""
    db_path = os.path.join(con.DATA_FOLDER, track_id, f"{track_id}.db")
    ensure_track_schema(db_path)

    with sqlite3.connect(db_path) as db:
        try:
            db.execute("delete from config")
        except sqlite3.OperationalError as e:
            if "no such table: config" not in str(e):
                raise

        try:
            db.execute("delete from events")
        except sqlite3.OperationalError as e:
            if "no such table: events" not in str(e):
                raise


def add_event(db_path, event_id, event_name, event_data):
    """Add event to track"""
    curr_time = helper.get_curr_time()

    ensure_track_schema(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute(
            """insert into events(event_id, event_name, event_data, event_ts) values (?, ?, ?, ?)""",
            (event_id, event_name, json.dumps(event_data, ensure_ascii=False), curr_time),
        )


def get_events(db_path):
    """Get events from track"""
    try:
        with sqlite3.connect(db_path) as db:
            rows = db.execute(
                """select
                            id,
                            event_id,
                            event_name,
                            event_data,
                            event_ts
                        from
                            events"""
            ).fetchall()
    except sqlite3.OperationalError as e:
        if "no such table: events" in str(e):
            ensure_track_schema(db_path)
            return []
        raise

    return [
        {
            "id": row[0],
            "event_id": row[1],
            "event_name": row[2],
            "event_data": json.loads(row[3]),
            "event_ts": row[4],
        }
        for row in rows
    ]


def get_version():
    """Get DB version"""
    db_path = os.path.join(con.DATA_FOLDER, con.MAIN_DB)

    with sqlite3.connect(db_path) as db:
        data = db.execute("select version from version").fetchall()

    return float(data[0])
