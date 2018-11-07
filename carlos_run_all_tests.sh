#!/usr/bin/env bash
/anaconda2/envs/NLP_QA/bin/python /Users/agustin/Classes/CS5340/NLP_QA/qa_test.py test_suite_1.txt
perl score_answers.pl test_output_1.txt answer_key_1.txt
rm -r test_output_1.txt answer_key_1.txt
