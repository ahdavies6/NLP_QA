import re
import subprocess
import os
import random
import heapq
from sys import argv
from question_classifier import formulate_question
from answer_identification import get_answer_phrase
from corpus_io import Corpus
from text_analyzer import *
from test_utils import get_sentence_with_answer


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*Difficulty:\s*(.*)\s*'


def form_answer(story, inquiry, answers, question_id):
    is_answer = True
    output = 'QuestionID: ' + question_id + '\n'
    output += 'Question: ' + inquiry + '\n'
    output += 'Answer: '
    best_sentence = get_sentence_with_answer(
        story,
        # max(answer, key=lambda x: len(x.split()))
        answers
    )
    if best_sentence:
        output += best_sentence
    else:
        is_answer = False
    output += "\nDifficulty: N/A\n"

    return output, is_answer, best_sentence


def form_dummy_output(question_id):
    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    output += '\n\n'
    return output


def form_output(story, inquiry, question_id):
    q_inquiry = formulate_question(inquiry)
    qword = q_inquiry['qword'][0].lower()
    if qword == 'where':
        feedback = get_prospects_for_where_ner(story, inquiry)
    elif qword == 'who':
        feedback = get_prospects_for_who_ner(story, inquiry)
    elif qword == 'why':
        feedback = get_prospects_with_lemmatizer2(story, inquiry)
    elif qword == 'when':
        feedback = get_prospects_with_lemmatizer2(story, inquiry)
    elif qword == 'how':
        feedback = get_prospects_for_how_regex(story, inquiry)
    elif qword == 'what':
        feedback = get_prospects_for_what(story, inquiry)
    else:
        feedback = get_prospects_with_lemmatizer2(story, inquiry)

    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    heapq.heapify(feedback)
    answer = None
    if len(feedback) > 0:
        answer = heapq.heappop(feedback)[1]

    if answer:
        output += answer
    output += '\n\n'

    return output, answer


def get_all_ids():
    all_filenames = []
    for path, dirs, filenames in os.walk(os.getcwd() + '/developset/'):
        all_filenames += ['./developset/' + filename for filename in filenames]
        break
    for path, dirs, filenames in os.walk(os.getcwd() + '/testset1/'):
        all_filenames += ['./testset1/' + filename for filename in filenames]
        break

    all_filenames = sorted(all_filenames)
    id_list = []
    for i in range(len(all_filenames)):
        if i % 3 == 0:  # answers file
            id_list.append(all_filenames[i][:-8])

    return id_list


def get_random_items(iterable, num_items=25, seed=None):
    if seed:
        random.seed(seed)

    items = []
    for i in range(num_items):
        item_index = random.randrange(len(iterable))
        items.append(iterable.pop(item_index))

    return items


def main(story_id):
    corpus = Corpus(['testset1'])
    output = ''
    key = ''
    story = corpus._get_story('/testset1/' + story_id)
    story_text = story['text']
    for question_id in story:
        if question_id not in ['text', 'answer_key']:
            question = story[question_id][0]
            answers = story[question_id][1]
            a = form_answer(story_text, question, answers, question_id)
            if a[1]:
                o = form_output(story_text, question, question_id)
                key += a[0]
                if a[2] == o[1]:
                    output += o[0]
                else:
                    output += form_dummy_output(question_id)

    with open('output', 'w') as output_file:
        output_file.write(output)
    with open('key', 'w') as answer_key:
        answer_key.write(key)

    subprocess.run(['perl', 'score_answers.pl', 'output', 'key'])
    os.remove('output')
    os.remove('key')


if __name__ == '__main__':
    if len(argv) == 1:
        while(True):
            story_id = input("Enter id: ")
            if story_id == 'quit':
                quit()
            main(story_id)
    elif len(argv) == 2:
        main(argv[1])

