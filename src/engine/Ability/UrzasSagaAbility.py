from engine.pydispatch import dispatcher
from engine.GameEvent import UpkeepStepEvent, ControllerChanged
from Trigger import PhaseTrigger
from Target import NoTarget
from TriggeredAbility import SpecialTriggeredAbility

def echo(cost):
    #At the beginning of your upkeep, if this came under your control since the beginning of your last upkeep, sacrifice it unless you pay its echo cost.
    def buildup(source):
        def controller_changed(sender, original):
            if sender == source: source._echo_controller = sender.controller
        dispatcher.connect(controller_changed, signal=ControllerChanged(), weak=False)
        source._echo_controller = source.controller
        source._echo_func = controller_changed
    def teardown(source):
        source._echo_controller = None
        dispatcher.disconnect(source._echo_func, signal=ControllerChanged(), weak=False)

    def condition(source, player):
        return source.controller == player and source.controller == source._echo_controller
    def effects(controller, source, player):
        yield NoTarget()
        source._echo_controller = None
        if not controller.you_may_pay(source, cost):
            controller.sacrifice(source)
        yield
    return SpecialTriggeredAbility(PhaseTrigger(UpkeepStepEvent()),
            condition=condition,
            effects=effects,
            special_funcs=(buildup, teardown),
            txt="echo %s"%cost, keyword="echo")
