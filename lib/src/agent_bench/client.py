from .helper import log
import requests
import os
import json
import re
from datetime import datetime

BASKET_QTY_EVENTS = ("basket_add", "basket_remove")
# Event families whose quantity must match the final logged state, not an
# intermediate click. Basket add/remove share one per-item quantity.
_LAST_QTY_FAMILIES = {
    "basket_add": BASKET_QTY_EVENTS,
    "basket_remove": BASKET_QTY_EVENTS,
    "select_seat": ("select_seat",),
    "bench_hotel_select_guests": ("bench_hotel_select_guests",),
}
_LAST_QTY_KEYS = {
    "basket_add": ("amount",),
    "basket_remove": ("amount",),
    "select_seat": ("seats_amount",),
    "bench_hotel_select_guests": ("guestsCount", "roomsCount"),
}


def create_track(
    name,
    id,
    filepath,
    address,
    https=False,
    delete_existing=False
):
    """Create track"""
    if not name:
        print("Please, provide track name.")
        return
    if not id:
        print("Please, provide track id.")
        return
    if not filepath:
        print("Please, provide path to the file.")
        return

    form = {"name": name, "track_id": id, "delete_existing": delete_existing}

    with open(filepath, "rb") as file:
        files = {os.path.basename(filepath): file}

        # print("os.path.basename(data)", os.path.basename(filepath))
        # print("data", form)

        response = requests.post(
            f"http{'s' if https else ''}://{address}/track/create",
            data=form,
            files=files,
        )

    try:
        res = json.loads(response.content.decode("utf-8"))
    except Exception as e:
        print("Exception occured:", str(e))
        return

    res = res["track_id"]

    # print(f"Done.\n\nSBS run: http://{address}/sbs/run/{sbs_id}")
    # print(f"SBS progress: http://{address}/sbs/show/{sbs_id}")

    return res


def get_track(track_id, address, https=False):
    """Get track events from backend by track_id"""
    if not track_id:
        print("Please, provide track_id.")
        return None
    
    try:
        response = requests.post(
            f"http{'s' if https else ''}://{address}/event/get",
            data={"track_id": track_id}
        )
        response.raise_for_status()
        
        result = json.loads(response.content.decode("utf-8"))
        events = result.get("events", [])
        
        for event in events:
            if isinstance(event.get("event_data"), str):
                try:
                    event["event_data"] = json.loads(event["event_data"])
                except:
                    pass
        
        return events
    
    except Exception as e:
        print(f"Exception occurred while getting track: {str(e)}")
        return None


def get_metrics(track_id, address, https=False):
    """
    Get metrics from track by track_id.
    Retrieves track events and config from backend, filters target events,
    and calculates durations between consecutive target events.
    
    Returns a list of objects with event_type, event_data, and duration (in seconds).
    """
    if not track_id:
        print("Please, provide track_id.")
        return None
    
    try:
        events = get_track(track_id, address, https)
        if events is None:
            print("Failed to get track events.")
            return None
        
        response = requests.post(
            f"http{'s' if https else ''}://{address}/track/get",
            data={"track_id": track_id}
        )
        response.raise_for_status()
        
        result = json.loads(response.content.decode("utf-8"))
        config_str = result.get("config", "{}")
        config = json.loads(config_str)
        
        target_event_types = config.get("test_data", {}).get("target_events", [])
        
        if not target_event_types:
            print("No target_events found in config.")
            return []
        
        target_events = []
        for event in events:
            if event["event_name"] in target_event_types:
                target_events.append(event)
        
        if not target_events:
            print("No target events found in track.")
            return []
        
        metrics = []
        for i in range(len(target_events)):
            event = target_events[i]
            
            duration = None
            if i > 0:
                prev_event = target_events[i - 1]
                try:
                    curr_time = datetime.fromisoformat(event["event_ts"])
                    prev_time = datetime.fromisoformat(prev_event["event_ts"])
                    duration = (curr_time - prev_time).total_seconds()
                except Exception as e:
                    print(f"Error calculating duration: {str(e)}")
                    duration = None
            
            metrics.append({
                "event_type": event["event_name"],
                "event_data": event["event_data"],
                "duration": duration
            })
        
        return metrics
    
    except Exception as e:
        print(f"Exception occurred while getting metrics: {str(e)}")
        return None


def _event_data(event):
    data = event.get("event_data") if isinstance(event, dict) else None
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return {}
    return data if isinstance(data, dict) else {}


def _to_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except Exception:
            return None
    return None


def _matches_wildcard(actual, pattern: str) -> bool:
    parts = pattern.split("*")
    regex_pattern = ".*".join(re.escape(part) for part in parts)
    return bool(re.match("^" + regex_pattern + "$", str(actual) if actual is not None else "", re.DOTALL))


def _compare(actual, expected, op: str) -> bool:
    if not op or op == "equal":
        if isinstance(expected, str) and "*" in expected:
            return _matches_wildcard(actual, expected)
        return actual == expected

    a = _to_number(actual)
    b = _to_number(expected)
    if a is None or b is None:
        return False

    if op == "greater_than":
        return a > b
    if op == "greater_than_or_equal":
        return a >= b
    if op == "less_than":
        return a < b
    if op == "less_than_or_equal":
        return a <= b
    return False


def _param_spec(param_value):
    if isinstance(param_value, dict) and "value" in param_value:
        return param_value.get("value"), param_value.get("condition") or "equal"
    return param_value, "equal"


def _parameters_match(parameters, event_data) -> bool:
    if not parameters:
        return True
    for param_key, param_value in parameters.items():
        expected_value, op = _param_spec(param_value)
        if not _compare(event_data.get(param_key), expected_value, op):
            return False
    return True


def _uses_last_quantity_match(condition) -> bool:
    match_mode = condition.get("match")
    if match_mode == "any":
        return False
    if match_mode == "last":
        return True
    event_name = condition.get("event_name")
    parameters = condition.get("parameters") or {}
    qty_keys = _LAST_QTY_KEYS.get(event_name)
    return bool(qty_keys) and any(key in parameters for key in qty_keys)


def _identity_item_id(parameters):
    if "item_id" not in (parameters or {}):
        return None
    expected, op = _param_spec(parameters["item_id"])
    if op != "equal":
        return None
    return expected


def find_matching_event(condition, events):
    """
    Return the event that satisfies the condition, or None.

    Quantity conditions (`amount` on basket_add/remove, `seats_amount`,
    guest counts) match the **last** logged state, not an intermediate click.
    Other conditions still pass if any historical event matches.
    """
    event_name = condition.get("event_name")
    parameters = condition.get("parameters") or {}

    if _uses_last_quantity_match(condition):
        family = _LAST_QTY_FAMILIES.get(event_name) or (event_name,)
        item_id = _identity_item_id(parameters) if event_name in BASKET_QTY_EVENTS else None
        last = None
        for event in events:
            if event.get("event_name") not in family:
                continue
            data = _event_data(event)
            if item_id is not None and data.get("item_id") != item_id:
                continue
            last = event
        if last is None:
            return None
        if _parameters_match(parameters, _event_data(last)):
            return last
        return None

    for event in events:
        if event.get("event_name") != event_name:
            continue
        data = _event_data(event)
        if not parameters or _parameters_match(parameters, data):
            return event
    return None


def condition_matches_events(condition, events) -> bool:
    """True if the condition is satisfied by the event list."""
    return find_matching_event(condition, events) is not None


def _check_condition_against_events(condition, events):
    return condition_matches_events(condition, events)


def check(track_id, address, https=False):
    """
    Check if conditions from config are met in the track events.

    Supports grouped conditions: conditions with the same 'group' field are treated
    as alternatives (OR logic) - at least one must pass for the group to pass.
    Conditions without 'group' field must each pass individually.

    Returns a list of conditions with 'success' field indicating if each condition was met,
    and 'group_success' field for grouped conditions indicating if the group passed.
    """
    if not track_id:
        print("Please, provide track_id.")
        return None

    try:
        events = get_track(track_id, address, https)
        if events is None:
            print("Failed to get track events.")
            return None

        response = requests.post(
            f"http{'s' if https else ''}://{address}/track/get",
            data={"track_id": track_id}
        )
        response.raise_for_status()

        result = json.loads(response.content.decode("utf-8"))
        config_str = result.get("config", "{}")
        config = json.loads(config_str)

        conditions = config.get("test_data", {}).get("conditions", [])

        if not conditions:
            print("No conditions found in config.")
            return []

        # First pass: check each condition individually
        results = []
        for condition in conditions:
            condition_result = condition.copy()
            condition_result["success"] = condition_matches_events(condition, events)
            results.append(condition_result)

        # Second pass: calculate group success for grouped conditions
        groups = {}
        for i, condition in enumerate(results):
            group = condition.get("group")
            if group:
                if group not in groups:
                    groups[group] = []
                groups[group].append(i)

        # Calculate group success (OR logic - at least one must pass)
        group_success = {}
        for group, indices in groups.items():
            group_success[group] = any(results[i]["success"] for i in indices)

        # Add group_success field to grouped conditions
        for i, condition in enumerate(results):
            group = condition.get("group")
            if group:
                results[i]["group_success"] = group_success[group]

        return results

    except Exception as e:
        print(f"Exception occurred while checking conditions: {str(e)}")
        return None

