import os
# Disable auto-loading of external pytest plugins that may be blocked (e.g., langsmith)
os.environ.setdefault('PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1')
# Manually enable essential built‑in plugins if needed
# (none required for this project)

# Tests must be deterministic and offline: force the in-memory mock KIT API.
# Must be set BEFORE backend.config is imported (config.py gives environment
# variables priority over .env via os.environ.setdefault, so this wins over
# a developer's local .env with KIT_USE_MOCK=false).
os.environ["KIT_USE_MOCK"] = "true"

