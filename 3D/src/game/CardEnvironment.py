from characteristics import characteristic, all_characteristics, no_characteristic, additional_characteristic
from stacked_function import override, replace, logical_or, logical_and
from Player import Player
from GameKeeper import Keeper
from CardRoles import *
from Planeswalker import Planeswalker
from Match import *
from LazyInt import LazyInt, X
from GameEvent import *

from Ability.Ability import Ability
from Ability.ActivatedAbility import ActivatedAbility, ManaAbility
from Ability.TriggeredAbility import TriggeredAbility
from Ability.StaticAbility import *
from Ability.CastingAbility import *
from Ability.Effects import *
from Ability.Target import *
from Ability.Trigger import *
from Ability.Cost import *
from Ability.Counters import *
from Ability.CreatureAbility import *
from Ability.PermanentAbility import *
from Ability.CyclingAbility import *
from Ability.LorwynAbility import *
from Ability.MorningtideAbility import *
from Ability.ShadowmoorAbility import *
from Ability.EventideAbility import *
from Ability.MemoryVariable import *

damage_tracker = DamageTrackingVariable()
graveyard_tracker = ZoneMoveVariable(from_zone="play", to_zone="graveyard")
