from engine.symbols import Forest, Island, Plains, Mountain, Swamp
from ActivatedAbility import ManaAbility
from Target import NoTarget
from Cost import TapCost

__all__ = ["basic_mana_ability"]

def basic_mana_ability(subtype, subtype_to_mana=dict(zip([Plains,Island,Swamp,Mountain,Forest],
 "WUBRG"))):
    color = subtype_to_mana[subtype]
    def effects(controller, source):
        payment = yield TapCost()
        yield NoTarget()
        controller.add_mana(color)
        yield
    return ManaAbility(effects, txt="T: Add %s to your mana pool"%color)
