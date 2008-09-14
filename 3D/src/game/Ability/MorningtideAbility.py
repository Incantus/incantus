from game.GameEvent import UpkeepStepEvent, ReceivesDamageEvent
from game.Match import isCreature, isPlayer
from ActivatedAbility import ActivatedAbility
from TriggeredAbility import TriggeredAbility
from StaticAbility import CardStaticAbility
from Target import NoTarget, Target
from Cost import ManaCost, DiscardCost
from Trigger import Trigger, EnterTrigger, PhaseTrigger
from Counters import PowerToughnessCounter
from MemoryVariable import MemoryVariable

def reinforce(cost, number=1):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        payment = yield cost+DiscardCost()
        target = yield Target(isCreature)
        target.add_counters(PowerToughnessCounter(1, 1), number)
        yield
    return ActivatedAbility(effects, zone="hand", keyword="Reinforce %d")

class ProwlVariable(MemoryVariable):
    def __init__(self):
        self.reset()
        self.register(self.dealt, event=ReceivesDamageEvent())
        super(ProwlVariable, self).__init__()
    def dealt(self, sender, source, amount, combat):
        if combat and isPlayer(sender):
            self.prowl_damage.add((source.controller, set(source.subtypes)))
    def check(self, card):
        for controller, subtypes in self.prowl_damage:
            if controller == card.controller and card.subtypes.intersects(subtypes):
                return True
        else: return False
    def reset(self): self.prowl_damage = set()

prowl_tracker = ProwlVariable()

# XXX This doesn't work, since by the time it's installed, I'm already running the original play_spell
# Need to redo alternative costs
def prowl(prowl_cost):
    if type(prowl_cost) == str: prowl_cost = ManaCost(prowl_cost)
    # You may play this for its prowl cost if you dealt combat damage to a player this turn with a [card subtypes]
    def prowl_effect(card):
        orig_spell = card.play_spell
        def play_prowl(controller, source):
            play = orig_spell.effect_generator(controller, source)
            cost = play.next()
            prowl_payed = False
            if prowl_tracker.check(source) and controller.you_may("play this spell for it's prowl cost (%s)"%prowl_cost):
                cost = prowl_cost
                prowl_payed = True
            payment = yield cost
            target = yield play.send(payment[:-1])
            play.send(target)
            if prowl_played:
                print "Prowl played!"
            yield
        # Set up a different way to play
        card.play_spell = orig_spell.__class__(play_prowl, limit=orig_spell.limit, txt=orig_spell.txt, keyword=orig_spell.keyword)
        def restore(): card.play_spell = orig_spell
        yield restore

    return CardStaticAbility(effects=prowl_effect, zone="stack", keyword="prowl %s"%prowl_cost)

# Kinship is a decorator for kinship abilities
def kinship(txt=''):
    def wrap(ability):
        effects = ability()
        def condition(source, player):
            controller = source.controller
            if controller == player and controller.you_may("look at the top card of your library"):
                topcard = controller.library.top()
                msg = "Top card of library"
                controller.peek(topcard, title=msg, prompt=msg)
                if source.subtypes.intersects(topcard.subtypes) and controller.getIntention("Reveal card?", "reveal card?"):
                    controller.revealCard(topcard, title=msg, prompt=msg)
                    return True
            return False
        #if not txt: txt = effects.__doc__
        return TriggeredAbility(PhaseTrigger(UpkeepStepEvent()), condition=condition, effects=effects, txt="Kinship - %s"%txt)
    return wrap
