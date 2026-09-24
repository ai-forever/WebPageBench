# WebPageBench Client Library

Python client library for interacting with the WebPageBench tracking and event-verification API.

## Installation

```bash
pip install -e lib/
```

## Overview

WebPageBench tests AI agents on de-branded mock web services. Pages emit typed events; `check()` matches them against the task conditions (Event-Match Score). No judge model and no scraping of rendered text.

## Features

- **Track Creation**: Create new tracking sessions with custom configurations
- **Event Retrieval**: Get all events logged during a tracking session
- **Metrics Calculation**: Calculate time durations between target events
- **Condition Checking**: Validate that required conditions were met during a session

## API Reference

### `create_track(name, id, filepath, address, https=False, delete_existing=False)`

Creates a new track with the specified configuration.

**Parameters:**
- `name` (str): Human-readable name for the track
- `id` (str): Unique identifier for the track
- `filepath` (str): Path to the JSON configuration file
- `address` (str): Backend server address (e.g., "localhost:9000")
- `https` (bool, optional): Use HTTPS instead of HTTP. Default: False
- `delete_existing` (bool, optional): Delete existing track with same ID. Default: False

**Returns:**
- `str`: The track ID if successful, None otherwise

**Example:**
```python
track_id = client.create_track(
    name="Test shop basket",
    id="ecommerce_basket_any_product",
    filepath="./tests/bench/build/ecommerce_basket_any_product.json",
    address="localhost:9000",
    delete_existing=True
)
```

---

### `get_track(track_id, address, https=False)`

Retrieves all events logged for a specific track.

**Parameters:**
- `track_id` (str): The unique identifier of the track
- `address` (str): Backend server address (e.g., "localhost:9000")
- `https` (bool, optional): Use HTTPS instead of HTTP. Default: False

**Returns:**
- `list`: List of event dictionaries, each containing:
  - `id` (int): Event database ID
  - `event_id` (str): Unique event identifier
  - `event_name` (str): Type of event (e.g., "state_changed", "submit_login")
  - `event_data` (dict): Event payload with parameters
  - `event_ts` (str): ISO format timestamp

**Example:**
```python
events = client.get_track("ecommerce_basket_any_product", "localhost:9000")
for event in events:
    print(f"{event['event_ts']}: {event['event_name']}")
```

---

### `get_metrics(track_id, address, https=False)`

Calculates time metrics between target events specified in the track configuration.

**Parameters:**
- `track_id` (str): The unique identifier of the track
- `address` (str): Backend server address (e.g., "localhost:9000")
- `https` (bool, optional): Use HTTPS instead of HTTP. Default: False

**Returns:**
- `list`: List of metric dictionaries, each containing:
  - `event_type` (str): The type of event
  - `event_data` (dict): Event payload
  - `duration` (float or None): Time in seconds from previous target event (None for first event)

**How it works:**
1. Retrieves track events and configuration from backend
2. Filters events to only include those in the `target_events` list from config
3. Calculates time duration between consecutive target events
4. Returns metrics with durations in seconds

**Example:**
```python
metrics = client.get_metrics("ecommerce_basket_any_product", "localhost:9000")
total_time = sum(m['duration'] for m in metrics if m['duration'] is not None)
print(f"Total time: {total_time:.2f} seconds")

for metric in metrics:
    print(f"Event: {metric['event_type']}")
    if metric['duration']:
        print(f"  Time from previous: {metric['duration']:.2f}s")
```

**Configuration Example:**
```json
{
  "test_data": {
    "target_events": [
      "submit_login",
      "submit_phone",
      "state_changed",
      "dialog_opened",
      "submit_payment"
    ]
  }
}
```

---

### `check(track_id, address, https=False)`

Validates that all conditions specified in the track configuration were met.

**Parameters:**
- `track_id` (str): The unique identifier of the track
- `address` (str): Backend server address (e.g., "localhost:9000")
- `https` (bool, optional): Use HTTPS instead of HTTP. Default: False

**Returns:**
- `list`: List of condition result dictionaries, each containing:
  - `event_name` (str): The required event name
  - `parameters` (dict): The required parameters
  - `success` (bool): True if condition was met, False otherwise

**How it works:**
1. Retrieves track events and configuration from backend
2. For each condition in the config, checks events:
   - Event name must match
   - All specified parameters must match
   - Parameter comparisons support optional numeric operators (see below)
   - If no parameters specified, just event name match is sufficient
   - **Quantity is the final state, not an intermediate click.** If `basket_add` / `basket_remove` specifies `amount`, the checker uses the last cart quantity for that `item_id` (add and remove share one counter). Adding 3 when the task asks for 2 fails even if quantity 2 appeared in between. The same last-state rule applies to `select_seat.seats_amount` and `bench_hotel_select_guests` counts. Other events (for example `state_changed`) still pass if any historical event matches.
   - Optional `"match": "last"` forces last-state matching; `"match": "any"` restores historical any-event matching.
3. Returns results with success status for each condition

**Supported parameter operators:**
- `equal` (default)
- `greater_than`
- `greater_than_or_equal`
- `less_than`
- `less_than_or_equal`

You can specify an operator **per parameter** by using an object value:
- Scalar values use `equal` (default), for example: `"item_id": "item_1931974549"`
- Object values use the provided operator, for example: `"amount": { "value": 3, "condition": "greater_than" }`

**Example:**
```python
results = client.check("ecommerce_basket_any_product", "localhost:9000")
all_passed = all(r['success'] for r in results)

for result in results:
    status = "✓" if result['success'] else "✗"
    print(f"{status} {result['event_name']}: {result['parameters']}")

print(f"Overall: {'PASSED' if all_passed else 'FAILED'}")
```

**Configuration Example:**
```json
{
  "test_data": {
    "conditions": [
      {
        "event_name": "state_changed",
        "parameters": {
          "new_state": "bench_books_item",
          "state_id": "item_69709285"
        }
      },
      {
        "event_name": "basket_add",
        "parameters": {
          "item_id": "item_1931974549",
          "amount": { "value": 1, "condition": "greater_than" }
        }
      },
      {
        "event_name": "submit_payment",
        "parameters": {}
      }
    ]
  }
}
```

## Complete Workflow Example

```python
from lib.src.agent_bench import client

# Step 1: Create a track
track_id = client.create_track(
    name="My Test",
    id="my_test_1",
    filepath="./config/test.json",
    address="localhost:9000",
    delete_existing=True
)

# Step 2: Agent performs the task on the mock website
# ... agent activity happens here ...

# Step 3: Get metrics after task completion
backend_address = "localhost:9000"
metrics = client.get_metrics(track_id, backend_address)

if metrics:
    print("Performance Metrics:")
    for i, metric in enumerate(metrics, 1):
        print(f"{i}. {metric['event_type']}")
        if metric['duration']:
            print(f"   Duration: {metric['duration']:.2f}s")

# Step 4: Check if task was completed correctly
results = client.check(track_id, backend_address)

if results:
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"\nValidation: {passed}/{total} conditions passed")
    
    for result in results:
        if not result['success']:
            print(f"Failed: {result['event_name']} {result['parameters']}")
```

## Configuration File Structure

The configuration file should be a JSON file with the following structure:

```json
{
  "test_data": {
    "test_name": "Test Name",
    "task": "Task description for the agent",
    "target_events": [
      "event_type_1",
      "event_type_2",
      "event_type_3"
    ],
    "conditions": [
      {
        "event_name": "event_type_1",
        "parameters": {
          "param1": "value1",
          "param2": "value2"
        }
      },
      {
        "event_name": "event_type_2",
        "parameters": {}
      }
    ]
  }
}
```

## Event Types

Common event types tracked by the system:

- `state_changed`: Navigation between pages/states
- `submit_login`: Login form submission
- `submit_phone`: Phone verification submission
- `submit_pass`: Password submission
- `dialog_opened`: Modal/dialog opened
- `select_pay_method`: Payment method selected
- `submit_payment`: Payment form submitted
- `click`: User clicked an element
- `keypress`: User pressed a key
- `scroll`: User scrolled the page

## Error Handling

All functions return `None` on error and print error messages to stdout. Always check for `None` returns:

```python
events = client.get_track(track_id, address)
if events is None:
    print("Error: Failed to retrieve track")
    return

if len(events) == 0:
    print("Warning: No events found in track")
```

## License

See LICENSE file in the project root.

