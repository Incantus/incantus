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
