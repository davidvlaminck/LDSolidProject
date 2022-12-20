import dataclasses
from datetime import date


@dataclasses.dataclass
class VkbBevestiging:
    id: int = -1
    bord_id: int = -1
    steun_ids: [str] = None

