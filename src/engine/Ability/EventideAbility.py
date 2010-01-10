from engine.Util import isiterable
from engine.Match import isLandCard
from StaticAbility import CardStaticAbility
from Cost import DiscardCost

# XXX These are currently incorrect - fix this with new spell playing
def retrace():
    def retrace_effect(card):
        orig_spell = card.play_spell
        def play_retrace(controller, source):
            play = orig_spell.effect_generator(controller, source)
            payment = yield play.next()+DiscardCost(cardtype=isLandCard)
            target = yield play.send(payment[:-1])
            yield play.send(target)
        # Set up a different way to play
        card.play_spell = orig_spell.__class__(play_retrace, limit=orig_spell.limit, zone="graveyard", txt=orig_spell.txt, keyword=orig_spell.keyword)
        def restore(): card.play_spell = orig_spell
        yield restore

    return CardStaticAbility(effects=retrace_effect, zone="graveyard", keyword="retrace")

def chroma(selection, mana_color):
    if not isiterable(selection): selection = (selection,)
    return sum([sum([1 for symbol in obj.cost if symbol == mana_color]) for obj in selection if obj.cost.is_mana_cost()])
