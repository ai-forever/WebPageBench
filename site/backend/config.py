"""App config"""

import os

# Default 9000 — no root/sudo; set DAB_API_PORT=80 for legacy deployments.
API_PORT = int(os.environ.get("DAB_API_PORT", "9000"))
