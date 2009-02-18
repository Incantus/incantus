from game.GameObjects import MtGObject

class Counter(MtGObject):
    def __init__(self, ctype):
        self.ctype = ctype
    def __eq__(self, val):
        return self.ctype == val
    def __ne__(self, val):
        return not self == val
    def __str__(self):
        return "%s"%self.ctype
    def copy(self):
        return Counter(self.ctype)

class PowerToughnessCounter(Counter):
    def __init__(self, power, toughness):
        super(PowerToughnessCounter,self).__init__("%+d%+d"%(power,toughness))
        self.power = power
        self.toughness = toughness
    def __str__(self):
        return "%+d/%+d"%(self.power, self.toughness)
    def copy(self):
        return PowerToughnessCounter(self.power, self.toughness)
