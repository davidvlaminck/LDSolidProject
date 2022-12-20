import dataclasses

from CreatingData.DataHelpers.VkbBevestiging import VkbBevestiging
from CreatingData.DataHelpers.VkbBord import VkbBord
from CreatingData.DataHelpers.VkbSteun import VkbSteun


@dataclasses.dataclass
class VkbFeature:
    id: int = -1
    wktPoint: str = ''
    coords: list = None
    external_id: str = ''
    client_id: str = ''
    borden: [VkbBord] = None
    bevestigingen: [VkbBevestiging] = None
    steunen: [VkbSteun] = None
    beheerder_key: int = -1
    beheerder_code: str = ''
    beheerder_naam: str = ''
    wegsegment_ids: [str] = None
