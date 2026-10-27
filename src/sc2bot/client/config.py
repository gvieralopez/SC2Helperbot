import logging
import os

logger = logging.getLogger(__name__)

try:
    realm_id = int(os.environ.get("REALM_ID", "1"))
except ValueError:
    realm_id = 1
    logger.warning(f"REALM_ID could not be parsed. Defaulted to {realm_id}.")
REALM_ID = realm_id
BLIZZARD_CLIENT_ID = os.environ.get("BLIZZARD_CLIENT_ID", "")
BLIZZARD_CLIENT_SECRET = os.environ.get("BLIZZARD_CLIENT_SECRET", "")
