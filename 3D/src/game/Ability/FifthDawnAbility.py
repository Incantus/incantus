from Counters import PowerToughnessCounter
from CiPAbility import CiP, CiPAbility
from EffectsUtilities import keyword_action

@keyword_action
def scry(player, number):
    cards = player.library.top(number)
    bottom_cards = set(player.choose_from(cards, number=-1, prompt="Pick any number of cards to put on the bottom of your library."))
    for card in cards:
        if card in bottom_cards: position = 'bottom'
        else: position = 'top'
        card.move_to("library", position=position)


# Untested
def sunburst():
    def enterPlayWith(self):
        '''Sunburst'''
        sunburst = 0
        if "W" in self.cost.payment: sunburst == sunburst + 1
        if "U" in self.cost.payment: sunburst == sunburst + 1
        if "B" in self.cost.payment: sunburst == sunburst + 1
        if "R" in self.cost.payment: sunburst == sunburst + 1
        if "G" in self.cost.payment: sunburst == sunburst + 1
        self.add_counters(PowerToughnessCounter(1, 1) if self.types == "Creature" else "charge", number=sunburst)
    def sunburst(source):
        yield CiP(source, enterPlayWith, condition=lambda self, zone, position="top": self.zone == "stack", txt="Sunburst")
    return CiPAbility(sunburst, keyword='sunburst')
