from engine.GameEvent import AttackerDeclaredEvent
from ActivatedAbility import ActivatedAbility
from TriggeredAbility import TriggeredAbility
from StaticAbility import ConditionalStaticAbility
from Trigger import Trigger, sender_match
from Target import NoTarget, Target
from Cost import ManaCost
from engine.Match import isPlayer
from Limit import sorcery_limit

def annihilator(number):
    def effects(controller, source):
        yield NoTarget()
        if not isPlayer(source.opponent):
            opponent = source.opponent.controller
        else:
            opponent = source.opponent
        opponent.force_sacrifice(number=number)
        yield
    return TriggeredAbility(Trigger(AttackerDeclaredEvent(), sender_match), effects, txt='Annihilator %i'%number, keyword="annihilator")

def totem_armor():
    def effects(source):
        def replacement(self):
            if isCreature(self):
                self.clearDamage()
            source.destroy()
            return False
        yield replace(source.attached_to, "canDestroy", replacement, txt="Totem armor")
    return CardStaticAbility(effects, keyword="totem armor", zone="attached")

def level_up(cost):
    if isinstance(cost, str): cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield NoTarget()
        source.add_counters("level", 1)
        yield
    return ActivatedAbility(effects, txt='Level up %s'%cost, keyword="level up", limit=sorcery_limit)

def level_between(start, end, txt=''):
    def make_ability(ability):
        condition = lambda source: source.num_counters("level") >= start and source.num_counters("level") <= end
        def effects(card):
            yield card.abilities.add(ability)
        return ConditionalStaticAbility(effects, condition, "battlefield", txt)
    return make_ability

def level_above(start, txt=''):
    def make_ability(ability):
        condition = lambda source: source.num_counters("level") >= start
        def effects(card):
            yield card.abilities.add(ability)
        return ConditionalStaticAbility(effects, condition, "battlefield", txt)
    return make_ability

def level_between_pt(start, end, pt, txt=''):
    condition = lambda source: source.num_counters("level") >= start and source.num_counters("level") <= end
    def effects(card):
        yield card.set_power_toughness(*pt)
    return ConditionalStaticAbility(effects, condition, "battlefield", txt)

def level_above_pt(start, pt, txt=''):
    condition = lambda source: source.num_counters("level") >= start
    def effects(card):
        yield card.set_power_toughness(*pt)
    return ConditionalStaticAbility(effects, condition, "battlefield", txt)
