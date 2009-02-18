
import glob, os

not_done = [os.path.basename(d) for d in glob.glob("not_done/*")]

lines = file("oracle.txt").readlines()

cards = {}
cardtext = []
for l in lines:
    if not l == '\n':
        cardtext.append(l)
    else:
        cards[cardtext[0].strip()] = cardtext
        cardtext = []

f = file("not_done_oracle.txt", 'w')
for n in not_done:
    f.writelines(cards[n.replace("_", " ")])
    f.write("\n")
f.close()

