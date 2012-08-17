from CreatureAbility import KeywordOnlyAbility
from engine.Player import keyword_action

__all__ = ["infect", "proliferate"]

def infect(): return KeywordOnlyAbility("infect")

@keyword_action
def proliferate(player):
    # Players can't have counters yet, so just pick permanents.
    permanents = player.choose_from_zone(number=-1, action="put an extra counter on", required=False, all=True)
    for permanent in permanents:
        sellist = list(set([counter.ctype for counter in permanent.counters]))
        if len(sellist) == 1: counter_type = sellist[0]
        else: counter_type = player.make_selection(sellist, prompt='Choose a counter for %s'%permanent, required=False)
        if counter_type: permanent.add_counters(counter_type.copy(), number=1)
