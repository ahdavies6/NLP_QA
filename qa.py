import re
import sys
import heapq
import nltk
from ner.text_analyzer import *
from question_classifier import formulate_question
from answer_identification import get_answer_phrase


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
story_pattern = r'STORYID:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
question_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Difficulty:\s*(.*)\s*'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*'


def form_output(story, inquiry, questionID):
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
    else:
        feedback = get_prospects_with_lemmatizer2(story, inquiry)

    output = 'QuestionID: ' + questionID + '\n'
    output += 'Answer: '
    if len(feedback) > 0:
        best_sentence = heapq.heappop(feedback)[1]
        answer = get_answer_phrase(inquiry, best_sentence)
        if answer:
            output += answer
    output += '\n\n'
    # for x in range(0, 3):
    #     if len(feedback) > 0:
    #         best_sentence = ''.join(heapq.heappop(feedback)[1])
    #         print('Answer: ' + best_sentence)

    return output


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

    output_file = open('test_output_1.txt', 'w+')
    for id in story_ids:
        question_filename = stories_filename + id + '.questions'
        questions = open(question_filename, 'r+')
        text = questions.read()
        question = re.findall(question_pattern, text)
        for match in question:
            output = form_output(story_files[id][2], match[1], match[0])        # match[1] is question itself, match[0] is questionID
            output_file.write(output)

    output_file.close()

    answer_key_file = open('answer_key_1.txt', 'w+')
    for id in story_ids:
        answers_filename = stories_filename + id + '.answers'
        answer_text = open(answers_filename, 'r+')
        text = answer_text.read()
        answer_key_file.write(text)
    answer_key_file.close()
