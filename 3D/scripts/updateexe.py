
import os, sys, zipfile

pathdir = sys.argv[1]
lenpathdir = len(pathdir)

exe = zipfile.PyZipFile("Incantus.exe", 'a')
#exe.writepy(pathdir)
for root, dirs, files in os.walk(pathdir, topdown=True):
    if ".svn" in dirs: dirs.remove(".svn")
    for fname in files:
        if fname[0] == '.': continue
        if os.path.splitext(fname)[1] != ".pyo": continue
        fullpath = os.path.join(root, fname)
        archivename = fullpath[lenpathdir:]
        print archivename
        exe.write(fullpath, archivename)

exe.close()

