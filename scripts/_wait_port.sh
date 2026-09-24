# shellcheck shell=bash
# Usage: find_bindable_port HOST START_PORT [SCAN_MAX] [EXCLUDE_PORT ...]
# Prints the first TCP port in [START, START+SCAN_MAX) that can be bound on HOST.
find_bindable_port() {
  local host="${1:?}" start="${2:?}" scan_max="${3:-200}"
  shift 3 || true
  python3 - "$host" "$start" "$scan_max" "$@" <<'PY'
import socket, sys

host, start, scan_max = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
excludes = {int(x) for x in sys.argv[4:] if str(x).isdigit()}

def can_bind(port: int) -> bool:
    if port in excludes:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True

for port in range(start, start + scan_max):
    if can_bind(port):
        print(port)
        raise SystemExit(0)
raise SystemExit(1)
PY
}

# Usage: wait_port HOST PORT [TIMEOUT_SEC]
wait_port() {
  local host="${1:?}" port="${2:?}" timeout="${3:-90}"
  python3 - "$host" "$port" "$timeout" <<'PY'
import socket, sys, time
host, port, timeout = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
for _ in range(timeout):
    try:
        with socket.create_connection((host, port), timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
sys.exit(1)
PY
}
