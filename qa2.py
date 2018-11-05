import re
import sys
import heapq
import nltk
from ner.text_analyzer import *
from syntax import parse


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
story_pattern = r'STORYID:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
question_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Difficulty:\s*(.*)\s*'


def print_answer(story, inquiry, questionID):
    # inquiry = parse.formulate_question(inquiry)
    feedback = get_prospects_with_lemmatizer2(story, inquiry)
    # if inquiry[0].lower() == 'where':
    #     feedback = get_prospects_for_where(story, inquiry)
    # elif inquiry[0].lower() == 'who':
    #     feedback = get_prospects_for_who(story, inquiry)
    # else:
    #     feedback = get_prospects_with_stemmer(story, inquiry)
    heapq.heapify(feedback)

    print('QuestionID: ' + questionID)
    if len(feedback) > 0:
        best_sentence = ''.join(heapq.heappop(feedback)[1])
        print('Answer: ' + best_sentence)

    if len(feedback) > 0:
        best_sentence2 = ''.join(heapq.heappop(feedback)[1])
        print('Answer2: ' + best_sentence2)

    if len(feedback) > 0:
        best_sentence3 = ''.join(heapq.heappop(feedback)[1])
        print('Answer3: ' + best_sentence3)
    x=1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('qa requires 1 argument, you provided ' + str(len(sys.argv) - 1))
        sys.exit()

    input_file = ''
    try:
        input_file = open(sys.argv[1], 'r+')
    except IOError:
        print('Failed to open ' + str(sys.argv[1]))
        sys.exit()

    stories_filename = input_file.readline().strip()
    story_ids = []
    story_files = {}

    for line in input_file.readlines():
        story_ids.append(line.strip())

    for id in story_ids:
        story_filename = stories_filename + id + '.story'
        story = open(story_filename, 'r+')
        story = story.read()
        headline = re.search(headline_pattern, story).group(1)
        date = re.search(date_pattern, story).group(1)
        text = re.search(text_pattern, story).group(1)
        story_files[id] = (headline, date, text.replace('\n', ' '))

    for id in story_ids:
        question_filename = stories_filename + id + '.questions'
        questions = open(question_filename, 'r+')
        text = questions.read()
        question = re.findall(question_pattern, text)
        for match in question:
            print('Question: ' + match[1])
            print_answer(story_files[id][2], match[1], match[0])        # match[1] is question itself, match[0] is questionID
            print()

    x = 100

