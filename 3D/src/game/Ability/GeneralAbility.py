from game.CardRoles import Creature
from game.Planeswalker import Planeswalker
from game.Player import Player
from EffectsUtilities import do_replace

preventAll = lambda self, amt, source, combat=False: 0

def prevent_all_damage():
    msg = "~ - prevent all damage"
    return (do_replace(Creature, "assignDamage", preventAll, msg=msg),
            do_replace(Player, "assignDamage", preventAll, msg=msg),
            do_replace(Planeswalker, "assignDamage", preventAll, msg=msg))

def prevent_all_combat_damage():
    def condition(self, amt, source, combat=False): return combat
    msg = "~ - prevent all combat damage"
    return (do_replace(Creature, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(Player, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(Planeswalker, "assignDamage", preventAll, msg=msg, condition=condition))

def prevent_all_noncombat_damage():
    def condition(self, amt, source, combat=False): return not combat
    msg = "~ - prevent all noncombat damage"
    return (do_replace(Creature, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(Player, "assignDamage", preventAll, msg=msg, condition=condition),
            do_replace(Planeswalker, "assignDamage", preventAll, msg=msg, condition=condition))
