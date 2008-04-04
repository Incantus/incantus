#!/bin/sh

rm -rf Incantus
cp -r ~/Projects/Incantus/src Incantus
find ./ | grep ".py[co]" | xargs rm
./run.sh
cp Incantus/main.py .
rm -f Incantus/*.py Incantus/game/*.py Incantus/game/Ability/*.py
rm -f Incantus/*.pyc Incantus/game/*.pyc Incantus/game/Ability/*.pyc
#find ./Incantus | grep ".py$" | xargs rm
mv main.py Incantus
#rm data/card_images.db
tar -zcvhf Incantus.tar.gz Incantus/ data/cards.db
