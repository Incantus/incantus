
from CardRoles import SubRole
from GameEvent import ReceivesDamageEvent, CounterRemovedEvent

class Planeswalker(SubRole):
    def loyalty():
        def fget(self):
            base = self.base_loyalty
            return base
        return locals()
    loyalty = property(**loyalty())
    def __init__(self, loyalty):
        super(Planeswalker,self).__init__()
        # These are immutable and come from the card
        self.base_loyalty = loyalty
        self.abilities = []
        self.redirect_ability = None
    def enteringPlay(self, perm):
        from Player import Player
        from Ability.StaticAbility import CardStaticAbility
        from Ability.Effect import GlobalReplacementEffect
        from Ability.Counters import Counter
        super(Planeswalker, self).enteringPlay(perm)
        self.perm.counters.extend([Counter("loyalty") for i in range(self.base_loyalty)])
        card = perm.card
        def condition(self, amt, source, combat, card=card):
            return not (combat or source.controller == card.controller)
        def redirectDamage(self, amt, source, combat=False, card=card):
            opponent = source.controller
            redirect = opponent.getIntention("", "Redirect %d damage to %s?"%(amt, card))
            if redirect: func = card.assignDamage
            else: func = self.assignDamage
            return func(amt, source, combat)
        self.redirect_ability = CardStaticAbility(card, GlobalReplacementEffect(redirectDamage, "assignDamage", Player, expire=False, condition=condition, txt='Redirect to planeswalker'))
        self.redirect_ability.enteringPlay()
    def leavingPlay(self):
        super(Planeswalker, self).leavingPlay()
        self.redirect_ability.leavingPlay()
    def assignDamage(self, amt, source, combat=False):
        if amt > 0:
            loyalty = [counter for counter in self.perm.counters if counter == "loyalty"]
            for counter in loyalty[:amt]:
                self.send(CounterRemovedEvent(), counter=counter)
                self.perm.counters.remove(counter)
            self.send(ReceivesDamageEvent(), source=source, amount=amt, combat=combat)
        return amt
    def shouldDestroy(self):
        return len([counter for counter in self.perm.counters if counter == "loyalty"]) <= 0
