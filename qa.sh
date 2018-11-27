#!/usr/bin/env bash

export PYTHONPATH=$PYTHONPATH:/home/u1200220/Desktop/NLP_QA/src/

{
cd stanford-corenlp
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -preload tokenize,ssplit,pos,lemma,ner,parse,depparse -status_port 9000 -port 9000 -timeout 15000 &
cd ..
python3 download.py
} &> /dev/null

# give the server time to start up
sleep 40

#python3 /home/davies/Documents/QA/qa.py $1
/home/u1200220/miniconda3/envs/NLP_QA/bin/python /home/u1200220/Desktop/NLP_QA/qa.py $1
exit
