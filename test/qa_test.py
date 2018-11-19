import heapq
import subprocess
import os
from sys import argv
from requests.exceptions import ConnectionError
from text_analyzer import *
from src.question_classifier import formulate_question
from answer_identification import get_answer_phrase
from test_answer_id import get_all_ids, get_random_items


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
story_pattern = r'STORYID:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
question_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Difficulty:\s*(.*)\s*'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*'


def form_output(story, inquiry, question_id):
    q_inquiry = formulate_question(inquiry)
    qword = q_inquiry['qword'][0].lower()
    if qword == 'who':
        feedback = get_prospects_for_who_ner(story, inquiry)
    elif qword == 'how':
        feedback = get_prospects_for_how_regex(story, inquiry)
    elif qword == 'when':
        feedback = get_prospects_for_when_regex(story, inquiry)
    elif qword == 'where':
        feedback = get_prospects_for_where_ner(story, inquiry)
    elif qword == 'why':
        feedback = get_prospects_for_why(story, inquiry)
    elif qword == 'what':
        feedback = get_prospects_with_wordnet(story, inquiry)
    else:
        feedback = get_prospects_with_lemmatizer2(story, inquiry)

    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    if len(feedback) > 0:
        best_sentence = heapq.heappop(feedback)[1]
        if qword == 'what':
            answer = best_sentence
        else:
            answer = get_answer_phrase(inquiry, best_sentence)
        if answer:
            output += answer
    output += '\n\n'

    return output


def main(random_seed, num_tests):
    story_ids = get_random_items(get_all_ids(), num_tests, random_seed)
    story_files = {}

    for story_id in story_ids:
        story_filename = story_id + '.story'
        with open(story_filename, 'r+') as story_file:
            story = story_file.read()
        headline = re.search(headline_pattern, story).group(1)
        date = re.search(date_pattern, story).group(1)
        text = re.search(text_pattern, story).group(1)
        story_files[story_id] = (headline, date, text.replace('\n', ' '))

    with open('output', 'w+') as output_file:
        for story_id in story_ids:
            question_filename = story_id + '.questions'
            with open(question_filename, 'r+') as questions:
                text = questions.read()
            question_tuples = re.findall(question_pattern, text)
            for question_id, question, _ in question_tuples:
                try:
                    output = form_output(story_files[story_id][2], question, question_id)
                except ConnectionError:
                    print('Server was inaccessible.')
                    raise SystemExit
                output_file.write(output)

    with open('key', 'w+') as answer_key_file:
        for story_id in story_ids:
            answers_filename = story_id + '.answers'
            answer_text = open(answers_filename, 'r+')
            text = answer_text.read()
            answer_key_file.write(text)

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