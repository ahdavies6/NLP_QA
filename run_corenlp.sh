#!/usr/bin/env bash

cd stanford-corenlp
java -Xmx4096M -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
            -preload tokenize,ssplit,pos,lemma,ner,parse,depparse \
            -status_port 9000 -port 9000 -timeout 15000 &
