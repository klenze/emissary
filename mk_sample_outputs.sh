#!/bin/bash
mkdir -p sample_outputs/
cp docs/Readme.samples.txt sample_outputs

#turns out that most generators do not have very much interesting output
for i in $( ls generators/*.py | grep -v /generators.py| grep hunting )
do
    echo running $i
    $i | tee sample_outputs/gen_$(basename -s .py $i).out.txt
done

OUT=0

for args in \
    "-g 'Whirring Contraption'"\
    "-g 'Whirring Contraption' -v"\
    "-g 'Whirring Contraption' -b Echo"\
    "-g 'Whirring Contraption' -b Echo -v"\
    "-g 'Echo' -v --max 10"\
    "-g 'Echo' -v --max 10 --favours"\
    "-g 'Echo' -v --max 10 -C"\
    "-g 'Hinterland Scrip' -v --max 10"\
    "-g 'Hinterland Scrip' -v --max 10 --favours"\
    "-g 'Hinterland Scrip' -v --max 10 -C"\
    "-A -b Echo"
do
    FNAME=sample_outputs/sample_${OUT}.txt
    echo Result of running ./emissary.py $args | tee ${FNAME}
    eval ./emissary.py $args | tee -a ${FNAME}
    OUT=$(( $OUT + 1 ))
done
