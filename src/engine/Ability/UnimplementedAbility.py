from StaticAbility import CardStaticAbility

def no_effects(source):
    yield lambda: None

def suspend(number):
    return CardStaticAbility(no_effects, keyword="suspend", zone="non-battlefield")

def intimidate():
    return CardStaticAbility(no_effects, keyword="intimidate", zone="battlefield")

def rampage(n):
    return CardStaticAbility(no_effects, keyword="rampage", zone="battlefield")

def cumulative_upkeep(cost):
    return CardStaticAbility(no_effects, keyword="cumulative upkeep", zone="battlefield")

def phasing(n):
    return CardStaticAbility(no_effects, keyword="phasing", zone="battlefield")

def buyback(cost):
    return CardStaticAbility(no_effects, keyword="buyback", zone="battlefield")

def flashback(cost):
    return CardStaticAbility(no_effects, keyword="flashback", zone="battlefield")

def madness(cost):
    return CardStaticAbility(no_effects, keyword="madness", zone="battlefield")

def morph(cost):
    return CardStaticAbility(no_effects, keyword="morph", zone="battlefield")

def amplify(n):
    return CardStaticAbility(no_effects, keyword="amplify", zone="non-battlefield")

def provoke():
    return CardStaticAbility(no_effects, keyword="provoke", zone="battlefield")

def storm():
    return CardStaticAbility(no_effects, keyword="storm", zone="stack")

def affinity(types):
    return CardStaticAbility(no_effects, keyword="affinity", zone="stack")

def entwine(cost):
    return CardStaticAbility(no_effects, keyword="entwine", zone="stack")

def splice(subtype, cost):
    return CardStaticAbility(no_effects, keyword="splice", zone="hand")

def offering(subtype):
    return CardStaticAbility(no_effects, keyword="offering", zone="non-battlefield")

def ninjutsu(cost):
    return CardStaticAbility(no_effects, keyword="ninjutsu", zone="hand")

def epic():
    return CardStaticAbility(no_effects, keyword="epic", zone="battlefield")

def convoke():
    return CardStaticAbility(no_effects, keyword="convoke", zone="stack")

def dredge(n):
    return CardStaticAbility(no_effects, keyword="dredge", zone="graveyard")

def bloodthirst(n):
    return CardStaticAbility(no_effects, keyword="bloodthirst", zone="non-battlefield")

def bloodthirst_x():
    return CardStaticAbility(no_effects, keyword="bloodthirst", zone="non-battlefield")

def haunt():
    return CardStaticAbility(no_effects, keyword="haunt", zone="battlefield")

def replicate(cost):
    return CardStaticAbility(no_effects, keyword="replicate", zone="stack")

#forecast

def graft(n):
    return CardStaticAbility(no_effects, keyword="graft", zone="non-battlefield")

def ripple(n):
    return CardStaticAbility(no_effects, keyword="ripple", zone="stack")

def split_second():
    return CardStaticAbility(no_effects, keyword="split second", zone="stack")

def aura_swap(cost):
    return CardStaticAbility(no_effects, keyword="aura swap", zone="battlefield")

def delve():
    return CardStaticAbility(no_effects, keyword="delve", zone="stack")

def frenzy(n):
    return CardStaticAbility(no_effects, keyword="frenzy", zone="battlefield")

def gravestorm():
    return CardStaticAbility(no_effects, keyword="gravestorm", zone="stack")

def poisonous(n):
    return CardStaticAbility(no_effects, keyword="poisonous", zone="battlefield")

def transfigure(n):
    return CardStaticAbility(no_effects, keyword="transfigure", zone="battlefield")

def conspire():
    return CardStaticAbility(no_effects, keyword="conspire", zone="stack")
