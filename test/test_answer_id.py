import re
import subprocess
import os
from sys import argv
from nltk import sent_tokenize
from answer_identification import calculate_overlap, get_answer_phrase


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
real_answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*Difficulty:\s*(.*)\s*'


def get_sentence_with_answer(story, answer):
    sentences = sent_tokenize(story)
    has_answer = []
    for sentence in sentences:
        if answer in sentence:
            has_answer.append(sentence)

    if len(has_answer) == 1:
        return has_answer[0]
    elif len(has_answer) > 1:
        return max(has_answer, key=lambda x: calculate_overlap(x, answer))
    else:
        return max(sentences, key=lambda x: calculate_overlap(x, answer))


def form_output(story, inquiry, answer, question_id):
    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    best_sentence = get_sentence_with_answer(story, answer)
    answer = get_answer_phrase(inquiry, best_sentence)
    if answer:
        output += answer
    output += '\n\n'

    return output


def get_all_ids():
    all_filenames = []
    for dirpath, dirnames, filenames in os.walk(os.getcwd() + './developset'):
        all_filenames.extend(filenames)
        break
    for dirpath, dirnames, filenames in os.walk(os.getcwd() + './testset1'):
        all_filenames.extend(filenames)
        break

    id_list = []
    for i in range(len(all_filenames)):
        if i % 3 == 0:  # answers file
            id_list.append(all_filenames[i][:-8])

    return id_list


def main(stories_directory, story_ids):
    story_files = {}

    for story_id in story_ids:
        story_filename = stories_directory + story_id + '.story'
        with open(story_filename, 'r+') as story_file:
            story = story_file.read()
        headline = re.search(headline_pattern, story).group(1)
        date = re.search(date_pattern, story).group(1)
        text = re.search(text_pattern, story).group(1)
        story_files[story_id] = (headline, date, text.replace('\n', ' '))

    with open('output', 'w+') as output_file:
        for story_id in story_ids:
            answer_filename = stories_directory + story_id + '.answers'
            with open(answer_filename, 'r+') as answers:
                text = answers.read()
            answer_tuples = re.findall(real_answer_pattern, text)
            for question_id, question, answer, _ in answer_tuples:
                try:
                    output = form_output(story_files[story_id][2], question, answer, question_id)
                except ConnectionError:
                    print('Server was inaccessible.')
                    raise SystemExit
                output_file.write(output)

    with open('key', 'w+') as answer_key_file:
        for story_id in story_ids:
            answers_filename = stories_directory + story_id + '.answers'
            answer_text = open(answers_filename, 'r+')
            text = answer_text.read()
            answer_key_file.write(text)

    subprocess.run(['perl', 'score_answers.pl', 'output', 'key'])
    os.remove('output')
    os.remove('key')


if __name__ == '__main__':
    if len(argv) != 2:
        print('Requires 1 argument (test suite); you provided ' + str(len(argv) - 1))
        exit()

    try:
        with open(argv[1], 'r+') as input_file:
            story_dir = input_file.readline().strip()
            stories = [line.strip() for line in input_file.readlines()]
    except IOError:
        print('Failed to open ' + str(argv[1]))
        raise SystemExit

    main(story_dir, stories)
