import cPickle as p
f = file("oracle.pkl")

cards = p.load(f)
cardinfo = dict([(c["name"],c) for c in cards])

path = "not_done/"

attributes = ["name", "cardnum", "type", "supertype", "subtypes", "cost", "color", "text"]
characteristics = set(["color", "type", "supertype", "subtypes"])

for card in cards:
    name = card["name"]
    cardfile = open(path+name.replace(' ','_'), 'w')
    lines = []
    
    for k in attributes:
        val = card.get(k, None)
        if val is not None:
            if k in characteristics:
                lines.append("%s = characteristic(%s)"%(k, repr(val)))
            else:
                lines.append("%s = %s"%(k, repr(val)))


    lines.append('')
    # Now the rest of the file
    type = card["type"]
    if type == "Instant" or type == "Sorcery":
        lines.append("out_play_role.abilities = [CastNonPermanentSpell(card, cost,]")
    # Otherwise we have permanents
    else:
        if type == "Creature":
            lines.append("subrole = Creature(%d, %d)"%(card['power'],card['toughness']))
        elif type == "Artifact":
            if "Equipment" in card["subtypes"]:
                lines.append("subrole = Equipment()")
            else:
                lines.append("subrole = Artifact()")
        elif type == "Enchantment":
            if "Aura" in card["subtypes"]:
                lines.append("out_play_role.abilities = [EnchantCreature(cost)]")
                lines.append("target_type = isCreature")
                lines.append("out_play_role.abilities = [CastPermanentSpell(card, cost,")
                lines.append("                               target=Target(target_types=target_type),")
                lines.append("                               effects=AttachToPermanent())]")
                lines.append("subrole = Aura(target_type)")
            else:
                lines.append("subrole = Enchantment()")
        elif type == "Land":
            lines.append("out_play_role = NoRole(card)")
            lines.append("subrole = Land(color)")
            lines.append("subrole.abilities = [ManaAbility(card, TapCost(), effects=AddMana(%s))]"%repr(card["color"][0]))
        lines.append("")
        lines.append("in_play_role = Permanent(card, subrole)")
        lines.append("")
        lines.append("#################################")
        lines.append("")
        if not type == "Land":
            lines.append("subrole.abilities = []")
            lines.append("subrole.triggered_abilities = []")
            lines.append("subrole.static_abilities = []")
        if type == "Aura" or type == "Equipment":
            lines.append("subrole.attached_abilities = []")
        lines.append("")
        lines.append("#################################")
    cardfile.writelines(["%s\n"%l for l in lines])
