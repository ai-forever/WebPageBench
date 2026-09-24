import logging
import os
import pathlib
import json
from warnings import simplefilter
import constants as con
import sys
import datetime


def check_folder(folder):
    """Check if folder exists"""
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)


def create_folders(hash):
    """Create folders for a new user"""
    if hash:
        pathlib.Path(os.path.join(con.DATA_FOLDER, hash)).mkdir(
            parents=True, exist_ok=True
        )


def get_curr_time():
    """Get formatted time"""
    return datetime.datetime.utcnow().strftime("%Y-%m-%d_%H:%M:%S")


# def get_path(guid):
#     """Get DB path"""
#     return os.path.join(con.DATA_FOLDER, guid, f"{guid}.db")


def try_parse_int(value):
    """Try parse int"""
    try:
        return int(value), True
    except ValueError:
        return value, False


def parse_json_array(json_str):
    """Parse JSON string array"""
    if not json_str:
        return []
    try:
        return json.loads(json_str)
    except:
        return []


def configure_logging(level=logging.INFO):
    """ "Configure logging module"""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    simplefilter(action="ignore", category=FutureWarning)
    # logging.basicConfig(level=level, filename='app.log', filemode='a', format='%(asctime)s [%(levelname)s] - %(process)d: %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.basicConfig(
        stream=sys.stdout,
        level=level,
        filemode="a",
        format="%(asctime)s [%(levelname)s] - %(process)d: %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
    logging.getLogger("matplotlib.font_manager").disabled = True


def get_tokens(file="./.tokens"):
    """Return tokens for validation"""
    tokens = open(file, "r", encoding="utf8").read().splitlines()
    tokens = [x.split()[0] for x in tokens if not x.startswith("#")]
    return tokens


def token_is_valid(user_token):
    """Check user token"""
    return user_token in get_tokens()


def lazy_property(func):
    """ "Lazy initialization attribute"""
    attr_name = "_lazy_" + func.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return _lazy_property
