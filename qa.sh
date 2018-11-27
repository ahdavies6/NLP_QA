#!/usr/bin/env bash

export PYTHONPATH=$PYTHONPATH:/scratch/tmp/davies/src/

{
cd stanford-corenlp
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9000 -port 9000 -timeout 15000 &
cd ..
python3 download.py
} &> /dev/null

# give the server time to start up
sleep 40

/home/davies/miniconda3/bin/python3 /scratch/tmp/davies/qa.py $1

exit 0
