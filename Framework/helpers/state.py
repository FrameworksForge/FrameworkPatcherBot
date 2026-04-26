import os
import time

user_rate_limits = {}
user_states = {}
connection_retries = {}
last_connection_check = time.time()
bot_process_id = os.getpid()
update_in_progress = False
active_build_jobs = {}

# --- Conversation States (Constants) ---
STATE_NONE = 0
STATE_WAITING_FOR_API = 1
STATE_WAITING_FOR_FEATURES = 2
STATE_WAITING_FOR_FILES = 3
STATE_WAITING_FOR_DEVICE_CODENAME = 4
STATE_WAITING_FOR_VERSION_SELECTION = 5
STATE_WAITING_FOR_MANUAL_ROM_VERSION = 6
STATE_WAITING_FOR_MANUAL_ANDROID_VERSION = 7


def reserve_active_build_slot(user_id: int, meta: dict | None = None) -> None:
	"""Reserve a global active build slot for a user."""
	active_build_jobs[user_id] = {
		"reserved_at": time.time(),
		**(meta or {}),
	}


def release_active_build_slot(user_id: int) -> None:
	"""Release a global active build slot for a user."""
	active_build_jobs.pop(user_id, None)
