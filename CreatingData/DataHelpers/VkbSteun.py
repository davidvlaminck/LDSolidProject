import dataclasses


@dataclasses.dataclass
class VkbSteun:
    id: int = -1
    client_id: str = ''
    x: int = -1
    lengte: int = -1
    breedte: int = -1
    diameter: int = -1
    kleur_key: int = -1
    sokkel_key: int = -1
    type_key: int = -1


