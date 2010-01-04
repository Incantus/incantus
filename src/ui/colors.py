dark_yellow = (196, 160, 0, 255)
yellow = (237, 212./255, 0, 255)
light_yellow = (252, 233, 79, 255)

dark_orange = (206, 92, 0, 255)
orange = (245./255, 121./255, 0, 1)
light_orange = (252./255, 175/255., 62./255, 1)

dark_brown = (143./255, 89./255, 2./255, 1)
brown = (193./255, 125./255, 17./255, 1)
light_brown = (233./255, 185./255, 110./255, 1)

dark_green = (78./255, 154./255, 6./255, 1)
green = (115./255, 210./255, 22./255, 1)
light_green = (138./255, 226./255, 52./255, 1)

dark_blue = (32./255, 74./255, 135./255, 1)
blue = (52./255, 101./255, 164./255, 1)
light_blue = (114./255, 159./255, 207./255, 1)

dark_purple = (92./255, 53./255, 102./255, 1)
purple = (117./255, 80./255, 123./255, 1)
light_purple = (173./255, 127./255, 168./255, 1)

dark_red = (164./255, 41./255, 41./255, 1)
red = (204./255, 51./255, 51./255, 1)
light_red = (239./255, 100./255, 100./255, 1)

black = (46, 52, 54, 255)
grey = (163, 163, 163, 255)
white = (238, 238, 236, 255)

def cnormalize(color):
    return (color[0]/255., color[1]/255., color[2]/255., color[3]/255.)

default_table = {
        'red': 'ff0000',
        'orange': 'ff8800',
        'yellow': 'ffff00',
        'green': '00ff00',
        'blue': '0000ff',
        'purple': 'ff00ff',
        'black': '000000',
        'white': 'ffffff',
        'gray': '888888',
        'grey': '888888',
        'silver': 'cccccc',
        }

def hexconvert(hexstr):
    if hexstr.lower() in default_table: hexstr = default_table[hexstr.lower()]
    elif not len(hexstr) == 6 or set(hexstr).difference(set("abcdefABCDEF0123456789")): hexstr = default_table['blue']
    final = [0, 0, 0]
    for i in [0, 1, 2]: final[i] = eval('0x' + hexstr[i*2:i*2+2]) / 255.0
    return tuple(final)

# In case we ever save information back into the INI file...
def listconvert(intlist):
    rawlist = [intlist[0], intlist[1], intlist[2]]
    rawlist[0] = rawlist[0]*256*256
    rawlist[1] = rawlist[1]*256
    return hex(sum(rawlist))[-6:]
