import Dataclasses


@Dataclasses.dataclass
class WegLocatieData:
    positie: float = 0
    bron: str = ''
    wktPoint: str = ''
