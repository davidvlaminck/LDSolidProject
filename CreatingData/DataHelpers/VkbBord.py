import dataclasses
from datetime import date


@dataclasses.dataclass
class VkbBord:
    id: int = -1
    aanzicht_hoek: float = -1.0
    external_id: str = ''
    client_id: str = ''
    bord_code: str = ''
    folie_type: str = ''
    parameters: list = None
    x: int = -1
    y: int = -1
    breedte: float = -1.0
    hoogte: float = -1.0
    vorm: str = ''  # {'wwl' wegwijzer links,  'rt' ruit, 'zh' zeshoek,  , 'wwr'  wegwijzer rechts, 'odh' omgekeerde driekhoek}
    plaatsing_datum: date = None
