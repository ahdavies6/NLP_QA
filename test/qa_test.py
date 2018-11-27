import heapq
import subprocess
import os
from sys import argv
from requests.exceptions import ConnectionError
from text_analyzer import *
from wordnet_experiments import LSAnalyzer
from answer_identification import get_answer_phrase
from corpus_io import Corpus


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
    if len(feedback) > 0:
        best_sentence = heapq.heappop(feedback)[1]
        answer = get_answer_phrase(inquiry, best_sentence)

        if len(feedback) > 0:
            second_best_sentence = heapq.heappop(feedback)[1]
            if question.sentence_match(best_sentence) < question.sentence_match(second_best_sentence):
                best_sentence = second_best_sentence
                answer = get_answer_phrase(inquiry, best_sentence)

        if answer:
            output += answer
        else:
            output += best_sentence
    output += '\n\n'
    return output


def main(random_seed=None, num_stories=None):
    if random_seed or num_stories:
        corpus = Corpus(['developset', 'testset1'])
        stories = corpus.random_stories(num_stories, random_seed)
    else:
        corpus = Corpus(['testset1'])
        stories = corpus.all

    output = ''
    key = ''
    for story in stories:
        story_text = story['text']
        for question_id in story:
            if question_id not in ['text', 'answer_key']:
                question = story[question_id][0]
                try:
                    output += form_output(story_text, question, question_id)
                except ConnectionError:
                    print('Server was inaccessible.')
                    raise SystemExit
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
        main()
    elif len(argv) == 2:
        main(argv[1], 25)
    elif len(argv) == 3:
        main(argv[1], int(argv[2]))
