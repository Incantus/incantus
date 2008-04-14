
class Event(object):
    def __hash__(self):
        return hash(self.__class__)
    def __eq__(self, other):
        return self.__class__ == other.__class__

class GameOver(Exception):
    def __init__(self, msg):
        self.msg = msg

class HasPriorityEvent(Event): pass
class TimestepEvent(Event): pass
class GameFocusEvent(Event): pass

class LifeChangedEvent(Event): pass
class DrawCardEvent(Event): pass
class DiscardCardEvent(Event): pass
class CardEnteringZone(Event): pass
class CardLeavingZone(Event): pass
class CardEnteredZone(Event): pass
class CardLeftZone(Event): pass
class CardControllerChanged(Event): pass
class TokenPlayed(Event): pass
class TokenLeavingPlay(Event): pass
class SubRoleAddedEvent(Event): pass
class SubRoleRemovedEvent(Event): pass
class AddSubRoleEvent(Event): pass
class RemoveSubRoleEvent(Event): pass
class SubtypeModifiedEvent(Event): pass
class SubtypeRestoredEvent(Event): pass
class CounterAddedEvent(Event): pass
class CounterRemovedEvent(Event): pass
class AbilityPlacedOnStack(Event): pass
class AbilityRemovedFromStack(Event): pass
#class AbilityPlayed(Event): pass
#class AbilityProcessed(Event): pass
class AbilityResolved(Event): pass
class AbilityCountered(Event): pass
class MorphEvent(Event): pass

class SacrificeEvent(Event): pass
class ManaEvent(Event): pass
class ManaAdded(Event): pass
class ManaSpent(Event): pass
class ManaCleared(Event): pass
class CardTapped(Event): pass
class CardUntapped(Event): pass

class PlayActionEvent(Event): pass
class PlayLandEvent(Event): pass
class PlaySpellEvent(Event): pass
class PlayAbilityEvent(Event): pass
class DeclareAttackersEvent(Event): pass
class DeclareBlockersEvent(Event): pass

class AttackerDeclaredEvent(Event): pass
class BlockerDeclaredEvent(Event): pass
class AttackerBlockedEvent(Event): pass
class RegenerateEvent(Event): pass
class DamagePreventedEvent(Event): pass
class PlayerDamageEvent(Event): pass
class CombatDamageAssigned(Event): pass
class DealsCombatDamageEvent(Event): pass
class ReceivesCombatDamageEvent(Event): pass
class DealsDamageEvent(Event): pass
class ReceivesDamageEvent(Event): pass
class PermanentDestroyedEvent(Event): pass
class AttachedEvent(Event): pass
class UnAttachedEvent(Event): pass
class TargetedByEvent(Event): pass
class InvalidTargetEvent(Event): pass
class PowerToughnessChangedEvent(Event): pass

class GameStepEvent(Event): pass
class NewTurnEvent(GameStepEvent): pass
class BeginTurnEvent(GameStepEvent): pass
class UntapStepEvent(GameStepEvent): pass
class UpkeepStepEvent(GameStepEvent): pass
class DrawStepEvent(GameStepEvent): pass
class MainPhaseEvent(GameStepEvent): pass
class EndMainPhaseEvent(GameStepEvent): pass
class PreCombatEvent(GameStepEvent): pass
class AttackStepEvent(GameStepEvent): pass
class BlockStepEvent(GameStepEvent): pass
class AssignDamageEvent(GameStepEvent): pass
class EndCombatEvent(GameStepEvent): pass
class EndPhaseEvent(GameStepEvent): pass
class CleanupEvent(GameStepEvent): pass
class EndTurnEvent(GameStepEvent): pass
