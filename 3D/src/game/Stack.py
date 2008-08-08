from GameObjects import MtGObject
#from Zone import Zone
from GameEvent import AbilityAnnounced, AbilityCanceled, AbilityPlacedOnStack, AbilityRemovedFromStack

class Stack(MtGObject):
#class Stack(Zone):
    name = "stack"
    def __init__(self, game):
        #super(Stack, self).__init__()
        self.cards = []
        self.pending_triggered = []
        self.game = game
    def add_triggered(self, ability):
        # XXX This is hacky, and is needed for triggered abilities where the target depends on the trigger
        # Since the trigger is a single object, it will have different arguments everytime it triggers
        # so the target will only reference the most recent one. I need to find a better way to bind things together
        for target in ability.targets:
            if hasattr(target, "triggered"): target.get(ability.card)
        self.pending_triggered.append(ability) 
    def process_triggered(self):
        # Check if there are any triggered abilities waiting
        if len(self.pending_triggered) > 0:
            # group all triggered abilities by player
            triggered_sets = dict([(player, []) for player in self.game.players])
            for ability in self.pending_triggered:
                triggered_sets[ability.controller].append(ability)
            # Now ask the player to order them if there are more than one
            for player in self.game.players:
                triggered = triggered_sets[player]
                if len(triggered) > 1:
                    triggered = player.getSelection(triggered, len(triggered), prompt="Drag to reorder triggered abilities(Top ability resolves first)")
                # Now reorder
                for ability in triggered: self.announce(ability)
            self.pending_triggered[:] = []
            return True
        else: return False
    def announce(self, ability):
        # Do all the stuff in rule 409.1 like pick targets, pay
        # costs, etc
        self.send(AbilityAnnounced(), ability=ability)
        #if Match.isSpellAbility(ability): ability.card.current_role = ability.card.stack_role
        success = True
        if hasattr(ability, "cost"):
            success = ability.precompute_cost()
            if success and ability.needs_target(): success = ability.get_target()
            if success: success = ability.compute_cost() and ability.pay_cost()
        else:
            if ability.needs_target(): success = ability.get_target()
        if success: self.push(ability)
        else:
            self.send(AbilityCanceled(), ability=ability)
            #if Match.isSpellAbility(ability): ability.card.current_role = ability.card.out_play_role
            del ability
        return success
    def skip_announce(self, ability):
        self.send(AbilityAnnounced(), ability=ability)
        self.push(ability)
    def stackless(self, ability):
        success = True
        if hasattr(ability, "cost"):
            success = ability.precompute_cost()
            if success and ability.needs_target(): success = ability.get_target()
            if success: success = ability.compute_cost() and ability.pay_cost()
        else:
            if ability.needs_target(): success = ability.get_target()
        if success:
            ability.played()
            ability.do_resolve()
        del ability
        return success
    def push(self, ability):
        self.cards.append(ability)
        self.send(AbilityPlacedOnStack(), ability=ability)
        #self.send(CardEnteredZone(), card=ability.card)
        ability.played()
    def on_stack(self, ability):
        return ability in self.cards
    def resolve(self):
        ability = self.cards.pop()
        ability.do_resolve()
        self.send(AbilityRemovedFromStack(), ability=ability)
        #self.send(CardLeftZone(), card=ability.card)
        del ability
    def counter(self, ability):
        self.cards.remove(ability)
        self.send(AbilityRemovedFromStack(), ability=ability)
    def empty(self): return len(self.cards) == 0
    def find(self, obj): # XXX This is needed for pickling Abilities on the stack (when they are targets of counterspells)
        return self.cards.index(obj)
