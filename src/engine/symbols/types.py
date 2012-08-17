from _symbols import Symbol

Land = Symbol("Land", __name__)
Creature = Symbol("Creature", __name__)
Enchantment = Symbol("Enchantment", __name__)
Artifact = Symbol("Artifact", __name__)
Sorcery = Symbol("Sorcery", __name__)
Instant = Symbol("Instant", __name__)
Planeswalker = Symbol("Planeswalker", __name__)
Tribal = Symbol("Tribal", __name__)

Plane = Symbol("Plane", __name__)
Vanguard = Symbol("Vanguard", __name__)

all_types = set([Land, Creature, Enchantment, Artifact, Sorcery, Instant, Planeswalker, Tribal])
