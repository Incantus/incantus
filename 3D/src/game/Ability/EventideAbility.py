from game.Match import isLandType
from StaticAbility import CardStaticAbility
from Cost import DiscardCost

def retrace():
    def retrace_effect(card):
        orig_spell = card.play_spell
        def play_retrace(source):
            play = orig_spell.effect_generator(source)
            payment = yield play.next()+DiscardCost(cardtype=isLandType)
            target = yield play.send(payment[:-1])
            yield play.send(target)
        # Set up a different way to play
        card.play_spell = orig_spell.__class__(play_retrace, limit=orig_spell.limit, zone="graveyard", txt=orig_spell.txt, keyword=orig_spell.keyword)
        def restore(): card.play_spell = orig_spell
        yield restore

    return CardStaticAbility(effects=retrace_effect, zone="graveyard", keyword="retrace")
