from stacked_function import logical_or, logical_and, modify_args, last_only, replacement
from characteristics import characteristic, all_characteristics, no_characteristic, additional_characteristic
from Player import Player
from GameKeeper import Keeper
from CardRoles import *
from Planeswalker import Planeswalker
from Match import *
from Cost import *
from LazyInt import LazyInt, X
from GameEvent import *

from Ability import *
from Ability.Counters import *
from Ability.CreatureAbility import *
from Ability.PermanentAbility import *
from Ability.LorwynAbility import *
from Ability.MorningtideAbility import *
from Ability.ShadowmoorAbility import *

damage_tracker = DamageTrackingVariable()
graveyard_tracker = ZoneMoveVariable(from_zone="play", to_zone="graveyard")
