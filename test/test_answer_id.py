import re
import subprocess
import os
import random
from sys import argv
from test_utils import get_sentence_with_answer
from question_classifier import formulate_question
from answer_identification import get_answer_phrase
from corpus_io import Corpus


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*Difficulty:\s*(.*)\s*'


def form_output(story, inquiry, answer, question_id):
    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    best_sentence = get_sentence_with_answer(
        story,
        max(answer, key=lambda x: len(x.split()))
    )
    if best_sentence:
        answer = get_answer_phrase(inquiry, best_sentence)
        if answer:
            output += answer
    output += '\n\n'

    return output


def right_answer(exact_answer, question_id):
    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    output += exact_answer
    output += '\n\n'

    return output


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


def main(random_seed, num_stories):
    # story_ids = get_random_items(get_all_ids(), num_stories, random_seed)
    # story_files = {}
    #
    # for story_id in story_ids:
    #     story_filename = story_id + '.story'
    #     with open(story_filename, 'r+') as story_file:
    #         story = story_file.read()
    #     headline = re.search(headline_pattern, story).group(1)
    #     date = re.search(date_pattern, story).group(1)
    #     text = re.search(text_pattern, story).group(1)
    #     story_files[story_id] = (headline, date, text.replace('\n', ' '))
    #
    # with open('output', 'w+') as output_file:
    #     for story_id in story_ids:
    #         answer_filename = story_id + '.answers'
    #         with open(answer_filename, 'r+') as answer_file:
    #             text = answer_file.read()
    #         answer_tuples = re.findall(answer_pattern, text)
    #         for question_id, question, answers, _ in answer_tuples:
    #             try:
    #                 output = form_output(
    #                     story_files[story_id][2],
    #                     question,
    #                     [a.strip() for a in answers.split(r'|')],
    #                     question_id
    #                 )
    #             except ConnectionError:
    #                 print('Server was inaccessible.')
    #                 raise SystemExit
    #             output_file.write(output)
    #
    # with open('key', 'w+') as answer_key_file:
    #     for story_id in story_ids:
    #         answers_filename = story_id + '.answers'
    #         answer_text = open(answers_filename, 'r+')
    #         text = answer_text.read()
    #         answer_key_file.write(text)
    #
    # subprocess.run(['perl', 'score_answers.pl', 'output', 'key'])
    # os.remove('output')
    # os.remove('key')

    corpus = Corpus(['testset1'])
    # corpus = Corpus(['developset', 'testset1'])
    output = ''
    key = ''
    # todo: test out every single type of question, and see what the precision looks like for each
    for story in corpus.all:
    # for story in corpus.random_stories(num_stories, random_seed):
        story_text = story['text']
        for question_id in story:
            if question_id not in ['text', 'answer_key']:
                question = story[question_id][0]
                answers = story[question_id][1]
                # output += form_output(story_text, question, answers, question_id)
                if formulate_question(question)['qword'][0].lower() == 'what':
                    output += form_output(story_text, question, answers, question_id)
                    # output += 'QuestionID: ' + question_id + '\n'
                    # output += 'Answer: '
                    # output += '\n\n'
                else:
                    output += right_answer(answers[0], question_id)
        key += story['answer_key']

    with open('output', 'w') as output_file:
        output_file.write(output)
    with open('key', 'w') as answer_key:
        answer_key.write(key)

    subprocess.run(['perl', 'score_answers.pl', 'output', 'key'])
    os.remove('output')
    os.remove('key')


if __name__ == '__main__':
    if len(argv) == 1:
        main(None, 25)
    elif len(argv) == 2:
        main(argv[1], 25)
    elif len(argv) == 3:
        main(argv[1], int(argv[2]))
