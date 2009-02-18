
import string

def load_set(edition, nummap):
    lines = file("%s/%s_checklist.txt"%(edition,edition)).readlines()
    lines = [l.strip().split("\t") for l in lines if l[0] != "#"]
    lines = [[int(l[0]), l[1]] for l in lines]
    nummap.update(dict([(l[1], (l[0], edition)) for l in lines]))
    return set([l[1] for l in lines])

def write_overlap(edition, nummap):
    import operator
    ed = [(number, name) for name, (number, edtn) in nummap.items() if edtn == edition]
    ed.sort(key=operator.itemgetter(0))
    f = file("%s/checklist.txt"%edition,'w')
    f.writelines(["%s\t%s\n"%tuple(a) for a in ed])
    f.close()

nummap = {}
for edition in ["8e", "9e", "10e"]:
    load_set(edition, nummap)

for edition in ["8e", "9e"]:
    write_overlap(edition, nummap)

