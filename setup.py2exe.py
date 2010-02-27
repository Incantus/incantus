from distutils.core import setup
import py2exe
import os, glob

# py2exe setup script.
# http://starship.python.net/crew/theller/py2exe/
# tested with py2exe 0.5.4 python2.4.1
# python setup.py py2exe --bundle 1

# usage:
# python setup.py py2exe


import sys

sys.path.append("src")
sys.argv.extend(["py2exe", "--bundle", "1"])

dist_dir = "dist/Incantus"
opts = {"py2exe": {
           "optimize": 1,
           "dist_dir": dist_dir,
           #"excludes": ["encodings"],
           "includes": ["pyglet.media.drivers.directsound", "pyglet.resource"],
           "dll_excludes": ["MSVCR71.dll"],
         }
}

setup(
    # The first three parameters are not required, if at least a
    # 'version' is given, then a versioninfo resource is built from
    # them and added to the executables.
    version = "1.0",
    description = "Open source MtG game",
    name = "Incantus",

    # targets to build.  name of your exe here.
    windows = [{
               "script":"src/main.py",
               "icon_resources":[(1,'data/Incantus-win.ico')],
               "dest_base": "Incantus",
               }],
    options = opts,
    zipfile = None, #"library.zip", #None, # This places the python zip library into the executable
    data_files=[],
)

def copy_data_dirs():
    import shutil
    shutil.copytree("data", os.path.join(dist_dir, "data"))
    shutil.copytree("decks", os.path.join(dist_dir, "decks"))
    #shutil.copy("incantus.ini", os.path.join(dist_dir, "incantus.ini"))

print "-" * 40
print "copying files"
print "-" * 40
copy_data_dirs()

