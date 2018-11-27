import sys
import heapq
from text_analyzer import *
from answer_identification import get_answer_phrase
from wordnet_experiments import LSAnalyzer
from word2vec_experiments import vector_sequence_similarity


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
story_pattern = r'STORYID:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
question_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Difficulty:\s*(.*)\s*'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*'


def form_output(story, inquiry, question_id):
    question = LSAnalyzer(inquiry)
    if question.qword == 'where':
        feedback = get_prospects_for_where_ner(story, inquiry)
    elif question.qword == 'who':
        feedback = get_prospects_for_who_ner(story, inquiry)
    elif question.qword == 'why':
        feedback = get_prospects_with_lemmatizer2(story, inquiry)
    elif question.qword == 'when':
        feedback = get_prospects_with_lemmatizer2(story, inquiry)
    elif question.qword == 'how':
        feedback = get_prospects_for_how_regex(story, inquiry)
    elif question.qword == 'what':
        feedback = get_prospects_for_what(story, inquiry)
    else:
        feedback = get_prospects_with_lemmatizer2(story, inquiry)

    output = 'QuestionID: ' + question_id + '\n'
    output += 'Answer: '
    heapq.heapify(feedback)

    alternatives = []
    while len(feedback) > 0 and len(alternatives) < 11:
        alternatives.append(heapq.heappop(feedback)[1])

    if alternatives:
        best_sentence = max(
            alternatives,
            key=lambda x: vector_sequence_similarity(inquiry, x)
        )
        answer = get_answer_phrase(inquiry, best_sentence)
        if answer:
            output += answer
        else:
            output += best_sentence

    output += '\n\n'

    return output


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('QA requires one argument, but you provided ' + str(len(sys.argv) - 1))
        sys.exit()

    input_file = ''
    try:
        input_file = open(sys.argv[1], 'r+')
    except IOError:
        print('Could not open ' + str(sys.argv[1]))
        sys.exit()

    stories_filename = input_file.readline().strip()
    story_ids = []
    story_files = {}

    for line in input_file.readlines():
        story_ids.append(line.strip())

    for story_id in story_ids:
        story_filename = stories_filename + story_id + '.story'
        with open(story_filename, 'r+') as story_file:
            story = story_file.read()
        headline = re.search(headline_pattern, story).group(1)
        date = re.search(date_pattern, story).group(1)
        text = re.search(text_pattern, story).group(1)
        story_files[story_id] = (headline, date, text.replace('\n', ' '))

    for story_id in story_ids:
        question_filename = stories_filename + story_id + '.questions'
        with open(question_filename, 'r+') as questions_file:
            text = questions_file.read()
        question = re.findall(question_pattern, text)
        for match in question:  # match[1] is question itself, match[0] is questionID
            print(form_output(story_files[story_id][2], match[1], match[0]))
