from game.pydispatch import dispatcher
from game.Match import isCard, isCreature, isLand
from game.GameEvent import TimestepEvent
from ActivatedAbility import ActivatedAbility, ManaAbility
from Target import NoTarget, Target
from Cost import ManaCost, TapCost
from EffectsUtilities import override, replace, combine, do_all
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

def attach_artifact(cost, target_type, keyword, limit=no_limit):
    if type(cost) == str: cost = ManaCost(cost)
    def effects(controller, source):
        yield cost
        target = yield Target(target_type, player='you')
        source.set_target_type(target_type)
        source.attach(target)
        yield
    return ActivatedAbility(effects, limit=limit+sorcery, txt='%s %s'%(keyword, cost))

equip = lambda cost, target_type=isCreature, limit=no_limit: attach_artifact(cost, target_type, "Equip", limit)
fortify = lambda cost, target_type=isLand, limit=no_limit: attach_artifact(cost, target_type, "Fortify", limit)

# Comes into play functionality
def enter_play_tapped(self):
    '''Card comes into play tapped'''
    self.tapped = True

# CiP functionality for auras
def attach_on_enter(self):
    self.target_type = self.play_spell.target_type
    if hasattr(self, "attaching_target"): card = self.attaching_target
    else:
        # Ask to select target
        card = self.controller.getTarget(self.target_type, zone="play", from_player=None, required=True, prompt="Select %s to attach %s"%(self.target_type, self))
        if not card: #move me to the graveyard
            pass
    self.attach(card)

no_before = lambda source: None
def CiP(obj, during, before=no_before, condition=None, txt=''):
    if not txt and hasattr(during, "__doc__"): msg = during.__doc__
    else: msg = txt

    def move_to(self, zone, position="top"):
        # Now move to play
        before(self.current_role)
        perm = self.move_to(zone, position)
        # At this point the card hasn't actually moved (it will on the next timestep event), so we can modify it's enteringZone function. This basically relies on the fact that entering play is batched and done on the timestep.
        remove_entering = override(perm, "modifyEntering", during, combiner=do_all)
        # XXX There might be timing issue, since we want to remove the override after the card is put into play
        dispatcher.connect(remove_entering, signal=TimestepEvent(), weak=False, expiry=1)
        return perm

    play_condition = lambda self, zone, position="top": str(zone) == "play"
    if condition: cond = lambda self, zone, position="top": play_condition(self,zone,position) and condition(self,zone,position)
    else: cond = play_condition

    if isCard(obj): obj = obj._cardtmpl # If we are changing a specific card, make sure to modify the card move_to_play
    return replace(obj, "move_to", move_to, msg=msg, condition=cond)

# Untapping abilities

optionallyUntap = lambda self: self.canUntap() and self.controller.getIntention("Untap %s"%self)
def optionally_untap(target):
    return do_override(target, "canUntapDuringUntapStep", optionallyUntap)
def doesnt_untap_controllers_next_untap_step(target):
    def cantUntap(self):
        cantUntap.expire()
        return False
    return do_override(target, "canUntapDuringUntapStep", cantUntap)
def doesntUntapAbility(txt):
    return CardStaticAbility(effects=override_effect("canUntapDuringUntapStep", lambda self: False), txt=txt)

# Cloning
def clone(source, cloned):
    from game import CardDatabase
    from game.GameObjects import GameObject
    clone = CardDatabase.execCode(GameObject(source.controller), cloned.text)
    source.cost = clone.base_cost
    expire1 = combine(*[getattr(source, attr).set_copy(getattr(clone, "base_"+attr)) for attr in ("name", "text", "color", "types", "subtypes", "supertypes", "abilities")])
    expire2 = combine(*[getattr(source, attr).set_copy(getattr(clone, attr)) for attr in ("base_power", "base_toughness", "base_loyalty")])
    def restore():
        source.cost = source._cardtmpl.base_cost
        expire1()
        expire2()
    del clone
    return restore


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
