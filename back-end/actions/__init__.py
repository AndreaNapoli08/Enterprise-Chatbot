import warnings
import logging
import os

# 🔇 Disattiva warning e log rumorosi
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("langchain.utils.math").setLevel(logging.ERROR)
os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"

from .actions_documents import (
    ActionSendLocalPDF,
    ActionListAvailableDocuments,
    ActionAnswerFromChroma,
)

from .actions_context import (
    ActionSaveContext,
    ActionQueryContext,
)

from .actions_users import (
    ActionCheckUserRole,
    ActionChangePassword,
)

from .actions_meetings import (
    ActionAvailabilityCheckRoom,
    ActionGetReservation,
    ActionDeleteReservation,
)

from .actions_fallback import (
    ActionHandleFallback,
    ActionResetFallbackCount,
)