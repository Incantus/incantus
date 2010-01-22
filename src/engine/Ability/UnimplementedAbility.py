from StaticAbility import CardStaticAbility

__all__ = ["suspend"]

def suspend(number):
    def effects(source):
        yield lambda: None
    return CardStaticAbility(effects, keyword="suspend", zone="non-battlefield")
