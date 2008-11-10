
class Event(object):
    def __hash__(self):
        return hash(self.__class__)
    def __eq__(self, other):
        return self.__class__ == other.__class__
    def __str__(self): return self.__class__.__name__

class GameOver(Exception):
    def __init__(self, msg):
        self.msg = msg

class GameStartEvent(Event): pass
class GameOverEvent(Event): pass
class HasPriorityEvent(Event): pass
class TimestepEvent(Event): pass
class GameFocusEvent(Event): pass
class LogEvent(Event): pass

class LifeGainedEvent(Event): pass
class LifeLostEvent(Event): pass
class DrawCardEvent(Event): pass
class DiscardCardEvent(Event): pass
class ShuffleEvent(Event): pass
class CardEnteringZone(Event): pass
class CardLeavingZone(Event): pass
class CardEnteredZone(Event): pass
class CardLeftZone(Event): pass
class CardCeasesToExist(Event): pass
class ControllerChanged(Event): pass
class TokenLeavingPlay(Event): pass
class CounterAddedEvent(Event): pass
class CounterRemovedEvent(Event): pass
class MorphEvent(Event): pass
class ClashEvent(Event): pass
class CardCycledEvent(Event): pass

class SubroleModifiedEvent(Event): pass
class TypesModifiedEvent(Event): pass
class ColorModifiedEvent(Event): pass
class SubtypesModifiedEvent(Event): pass
class SupertypesModifiedEvent(Event): pass
class AbilitiesModifiedEvent(Event): pass

class ManaAdded(Event): pass
class ManaSpent(Event): pass
class ManaCleared(Event): pass
class CardTapped(Event): pass
class CardUntapped(Event): pass

class LandPlayedEvent(Event): pass
class AbilityAnnounced(Event): pass
class AbilityCanceled(Event): pass
class AbilityPlacedOnStack(Event): pass
class AbilityRemovedFromStack(Event): pass
class AbilityResolved(Event): pass
class AbilityCountered(Event): pass
class AbilityPlayedEvent(Event): pass
class SpellPlayedEvent(Event): pass
class DeclareAttackersEvent(Event): pass
class DeclareBlockersEvent(Event): pass

class AttackerSelectedEvent(Event): pass
class AttackersResetEvent(Event): pass
class BlockerSelectedEvent(Event): pass
class BlockersResetEvent(Event): pass
class AttackerDeclaredEvent(Event): pass
class BlockerDeclaredEvent(Event): pass
class AttackerBlockedEvent(Event): pass
class AttackerClearedEvent(Event): pass
class BlockerClearedEvent(Event): pass
class CreatureInCombatEvent(Event): pass
class CreatureCombatClearedEvent(Event): pass
class RegenerateEvent(Event): pass
class DamagePreventedEvent(Event): pass
class PlayerDamageEvent(Event): pass
class DealsDamageEvent(Event): pass
class DealsDamageToEvent(Event): pass
class ReceivesDamageEvent(Event): pass
class ReceivesDamageFromEvent(Event): pass
class PermanentSacrificedEvent(Event): pass
class PermanentDestroyedEvent(Event): pass
class AttachedEvent(Event): pass
class UnAttachedEvent(Event): pass
class TargetedByEvent(Event): pass
class InvalidTargetEvent(Event): pass
class PowerToughnessChangedEvent(Event): pass

class NewTurnEvent(Event): pass
class TurnFinishedEvent(Event): pass
class GameStepEvent(Event): pass
class UntapStepEvent(GameStepEvent): pass
class UpkeepStepEvent(GameStepEvent): pass
class DrawStepEvent(GameStepEvent): pass
class MainPhase1Event(GameStepEvent): pass
class MainPhase2Event(GameStepEvent): pass
class EndMainPhaseEvent(GameStepEvent): pass
class BeginCombatEvent(GameStepEvent): pass
class AttackStepEvent(GameStepEvent): pass
class BlockStepEvent(GameStepEvent): pass
class AssignDamageEvent(GameStepEvent): pass
class EndCombatEvent(GameStepEvent): pass
class EndTurnStepEvent(GameStepEvent): pass
class CleanupPhase(GameStepEvent): pass
class CleanupEvent(GameStepEvent): pass
