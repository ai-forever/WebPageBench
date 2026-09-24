# %%
# pip install agent_bench

import importlib
from lib.src.agent_bench import client
import os
from glob import glob
import json
import copy


importlib.reload(client)

def merge(base, update):
    result = copy.deepcopy(base)
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result

def build_test_configs(tests_dir):
    test_configs = glob(f"{tests_dir}/tasks/*.json")
    mock_config_path = f"{tests_dir}/config.json"
    build_dir = f"{tests_dir}/build"
    mock_config = json.load(open(mock_config_path, encoding="utf-8"))
    extends_rel = mock_config.pop("extends", None)
    if extends_rel:
        base_path = os.path.normpath(os.path.join(tests_dir, extends_rel))
        if not os.path.isfile(base_path):
            raise FileNotFoundError(f"extends: файл не найден: {base_path}")
        base_config = json.load(open(base_path, encoding="utf-8"))
        mock_config = merge(base_config, mock_config)
    os.makedirs(build_dir, exist_ok=True)
    from bench_eval.task_dates import apply_booking_dates

    res = {}
    for file in test_configs:
        test_config_data = json.load(open(file, encoding="utf-8"))
        filename = os.path.basename(file)
        merged_config = merge(mock_config, test_config_data)
        apply_booking_dates(merged_config)
        merged_config["test_data"]["test_name"] = filename.replace(".json", "")
        output_path = os.path.join(build_dir, filename)
        res[output_path] = merged_config
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged_config, f, ensure_ascii=False, indent=2)
    return res

# %%
# TESTS_FOLDER = "./tests/bench"
TESTS_FOLDER = "./tests/bench"

tests = build_test_configs(TESTS_FOLDER)
print("Built tests:", len(tests))
print('='*100)

#dev
host = "localhost:5173"
api_address = "localhost:80"

#docker
# host = "localhost:9000"
# api_address = "localhost:9000"


for filepath, test in tests.items():
    test_name = test["test_data"]["test_name"]
    track_id = test_name.replace(" ", "_").lower()

    full_host = f"http://{host}/{track_id}"
    task = test["test_data"]["task"].replace("%HOST%", full_host)

    # print('\n')
    print("test_name:", test_name)
    print("host:", full_host)
    print('\n')
    print("task:", task)
    print('*'*100)

    res = client.create_track(
        name=test_name,
        id=track_id,
        filepath=filepath,
        address=api_address,
        delete_existing=True,
    )

    #Agent is working...

    # ...

    # Agent is done

    # break

# %%
#2 check results

for filepath, test in tests.items():
    test_name = test["test_data"]["test_name"]
    track_id = test_name.replace(" ", "_").lower()

    print("test_name:", test_name)
    print("track_id:", track_id)

    check_results = client.check(track_id, api_address)
    if check_results:
        print(f"\nCondition checks for {test_name}:")
        all_passed = True
        for i, result in enumerate(check_results):
            status = "✓ PASSED" if result['success'] else "✗ NOT FOUND"
            print(f"  {i+1}. {status}")
            print(f"     Event: {result['event_name']}")
            print(f"     Parameters: {result['parameters']}")
            if not result['success']:
                all_passed = False
        
        print(f"\nOverall result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

    print('*'*100)

    # break
# %%
