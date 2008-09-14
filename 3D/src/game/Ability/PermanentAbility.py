from game.pydispatch import dispatcher
from game.Match import isCreature, isLand
from game.GameEvent import TimestepEvent
from ActivatedAbility import ActivatedAbility, ManaAbility
from Target import NoTarget, Target
from Cost import ManaCost, TapCost
from Effects import do_override, override, replace, do_all
from Limit import no_limit, sorcery

#def flash(card):
#    casting_ability = card.play_spell
#    if isinstance(casting_ability.limit, SorceryLimit):
#        casting_ability.limit = Unlimited(card)
#    elif isinstance(casting_ability.limit, MultipleLimits):
#        for i, limit in enumerate(casting_ability.limit):
#            if isinstance(limit, SorceryLimit): break
#        casting_ability.limit.limits.pop(i)

def basic_mana_ability(subtype, subtype_to_mana=dict(Forest='G',Island='U',Plains='W',Mountain='R',Swamp='B')):
    color = subtype_to_mana[subtype]
    def effects(controller, source):
        payment = yield TapCost()
        yield NoTarget()
        controller.add_mana(color)
        yield
    return ManaAbility(effects, txt="T: Add %s"%color)

def equip(cost, target_type=isCreature, limit=no_limit):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(target_type)
        source.set_target_type(target_type)
        source.attach(target)
        yield
    return ActivatedAbility(effects, limit=limit+sorcery, txt='Equip %s'%target_type)

def fortify(cost, target_type=isLand, limit=no_limit):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(target_type)
        source.set_target_type(target_type)
        source.attach(target)
        yield
    return ActivatedAbility(effects, limit=limit+sorcery, txt='Fortify %s'%target_type)

# Comes into play functionality
def enter_play_tapped(self):
    '''Card comes into play tapped'''
    self.tapped = True

no_before = lambda source: None
def CiP(obj, during, before=no_before, condition=None, txt=''):
    if not txt and hasattr(during, "__doc__"): msg = during.__doc__
    else: msg = txt
    def move_to(self, zone, position="top"):
        # Add the entering function to the in_play_role
        remove_entering = override(self.in_play_role, "enteringZone", lambda self, zone: during(self), combiner=do_all)
        # Now move to play
        before(self)
        print "Moving %s with %s"%(self, msg)
        self.move_to(zone, position)
        # Remove the entering function from the in_play_role
        # XXX There might be timing issue, since we want to remove the override after the card is put into play
        dispatcher.connect(remove_entering, signal=TimestepEvent(), weak=False)
    play_condition = lambda self, zone, position="top": str(zone) == "play"
    if condition: cond = lambda self, zone, position="top": play_condition(self,zone,position) and condition(self,zone,position)
    else: cond = play_condition

    return replace(obj, "move_to", move_to, msg=msg, condition=cond)

# Optionally untapping during untap step
def untapDuringUntapStep(self):
    msg = "Untap %s"%self
    return self.canUntap() and self.controller.getIntention(msg, msg)
def optionally_untap(target):
    return do_override(target, "untapDuringUntapStep", untapDuringUntapStep)

# Cloning
#def clone(card, cloned):
#    # XXX This is ugly,
#    role = card.current_role
#    for subrole in role.subroles: subrole.leavingPlay()
#    reverse = CiP_as_cloned(card, cloned)
#    for subrole in role.subroles: subrole.enteringPlay(role)
#    def reversal():
#        for subrole in role.subroles: subrole.leavingPlay()
#        reverse()
#        for subrole in role.subroles: subrole.enteringPlay(role)
#    return reversal
#
#def CiP_as_cloned(card, cloned):
#    text = cloned.text
#    obj = CardDatabase.execCode(GameObject(card.controller), text)
#    role = card.current_role
#    role.cost = obj.base_cost
#    reverse = [getattr(role, attr).set_copy(getattr(obj, "base_"+attr)) for attr in ("name", "text", "color", "types", "subtypes", "supertypes", "abilities")]
#    # XXX Instead of this, i should reset the power/toughness value that the creature subrole will refer to
#    # That way i keep the same subrole
#    role.subroles = obj.in_play_role.subroles
#    def reversal():
#        role.name = card.base_name
#        role.cost = card.base_cost
#        role.text = card.base_text
#        for r in reverse: r()
#        role.subroles = card.in_play_role.subroles
#    return reversal



#class ThresholdAbility(ActivatedAbility):
#    def __init__(self, card, cost="0", target=None, effects=[], copy_targets=True, limit=None, zone="play"):
#        if limit: limit += ThresholdLimit(card)
#        else: limit = ThresholdLimit(card)
#        super(ThresholdAbility,self).__init__(card, cost=cost, target=target, effects=effects, copy_targets=copy_targets, limit=limit, zone=zone)
#
#def vanishing(card, number):
#    for i in range(number): card.counters.append(Counter("time"))
#    remove_counter = TriggeredAbility(card, trigger=PlayerTrigger(event=UpkeepStepEvent()),
#                        match_condition = lambda player, card=card: player == card.controller,
#                        ability=Ability(card, target=Target(targeting="self"), effects=RemoveCounter("time")))
#    def check_time(sender, counter):
#        counters = [c for c in sender.counters if c == "time"]
#        print sender, counter, len(counters)
#        return sender == card and counter == "time" and len(counters) == 0
#
#    sacrifice = TriggeredAbility(card, trigger=Trigger(event=CounterRemovedEvent()),
#                        match_condition = check_time,
#                        ability=Ability(card, effects=SacrificeSelf()))
#    return card.abilities.add([remove_counter, sacrifice])
#
#def dredge(card, number):
#    condition = lambda self: len(self.graveyard) >= number
#    def draw(self):
#        if self.getIntention("Would you like to dredge %s?"%card, "Dredge %s"%card):
#            top_N = self.library.top(number)
#            for c in top_N: c.move_to(self.graveyard)
#            card.move_to(self.hand)
#        else:
#            self.draw()
#
#    dredge_ability = GlobalStaticAbility(card,
#      effects=ReplacementEffect(draw, "draw", txt='%s - dredge?'%card, expire=False, condition=condition), zone="graveyard")
#    card.abilities.add(dredge_ability)

#def suspend(card, number):
#    pass

#def echo(card, cost="0"):
#    #At the beginning of your upkeep, if this came under your control since the beginning of your last upkeep, sacrifice it unless you pay its echo cost.
#    # XXX This doesn't work when the controller is changed
#    # need to reset the triggered ability somehow or implement the intervening if properly
#    echo_ability = [TriggeredAbility(card,
#                       trigger = PlayerTrigger(event=UpkeepStepEvent()),
#                       match_condition = lambda player: player == card.controller,
#                       ability = Ability(card,
#                                        target=Target(targeting="you"),
#                                        effects=DoOr(PayExtraCost(cost), failed=SacrificeSelf())),
#                       expiry=1)]
#    return card.abilities.add(echo_ability)
