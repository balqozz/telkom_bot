import os
import logging
import pytz
from dotenv import load_dotenv

# --- Konfigurasi ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
LOOKER_STUDIO_MSA_WSA_URL = os.getenv("LOOKER_STUDIO_MSA_WSA_URL")
LOOKER_STUDIO_PILATEN_URL = os.getenv("LOOKER_STUDIO_PILATEN_URL")
TIMEZONE = pytz.timezone("Asia/Jakarta")

# === Logging ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === Section Coordinates ===
# SECTION_COORDINATES = {
#     "fulldashboard": (10, 10, 1234, 974),
#     "fulfillmentfbb": (34, 36, 334, 293),
#     "assurancefbb": (351, 114, 724, 453),
#     "scorecredit": (772, 117, 1222, 267),
#     "fulfillmentbges": (34, 301, 333, 551),
#     "assurancebges": (34, 559, 333, 913),
#     "msaassurance": (743, 268, 1219, 622),
#     "msacnop": (349, 458, 722, 911),
#     "msaquality": (743, 635, 1212, 911)
# }

# SECTION_LABELS = {
#     "fulldashboard": "FULL DASHBOARD",
#     "fulfillmentfbb": "FULFILLMENT FBB",
#     "assurancefbb": "ASSURANCE FBB",
#     "scorecredit": "SCORE CREDIT",
#     "fulfillmentbges": "FULFILLMENT BGES",
#     "assurancebges": "ASSURANCE BGES",
#     "msaassurance": "MSA ASSURANCE",
#     "msacnop": "MSA CNOP",
#     "msaquality": "MSA QUALITY"
# }
