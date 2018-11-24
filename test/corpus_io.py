import re
import os
import random
from copy import deepcopy
from question_classifier import formulate_question
from test_utils import get_sentence_with_answer


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
question_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Difficulty:\s*(.*)\s*'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*Difficulty:\s*(.*)\s*'


class Corpus(object):

    def __init__(self, directories):
        if isinstance(directories, str):
            directories = [directories]

        all_filenames = []
        for directory in directories:
            # for path, dirs, filenames in os.walk(os.getcwd() + '/developset/'):
            for path, dirs, filenames in os.walk('{}/{}/'.format(os.getcwd(), directory)):
                # all_filenames += ['./developset/' + filename for filename in filenames]
                all_filenames += ['./{}/{}'.format(directory, filename) for filename in filenames]
                break

        all_filenames = sorted(all_filenames)
        self.id_list = []
        for i in range(len(all_filenames)):
            if i % 3 == 0:  # answers file
                self.id_list.append(all_filenames[i].split('.')[1])

    def _get_story(self, story_id):
        assert story_id in self.id_list

        with open(os.getcwd() + story_id + '.questions') as question_file:
            question_fulltext = question_file.read()
        question_groups = re.findall(question_pattern, question_fulltext)

        with open(os.getcwd() + story_id + '.answers') as answer_file:
            answer_fulltext = answer_file.read()
        answer_groups = re.findall(answer_pattern, answer_fulltext)

        with open(os.getcwd() + story_id + '.story') as story_file:
            story_fulltext = story_file.read()
        story_text = re.search(text_pattern, story_fulltext).group(1).replace('\n', ' ')

        story_dict = {
            question_id: (
                question,
                [answer.strip() for answer in answer_group.split(r'|')]
            ) for question_id, question, _ in question_groups for question_id2, _, answer_group, _ in answer_groups
            if question_id == question_id2
        }
        story_dict['text'] = story_text
        story_dict['answer_key'] = answer_fulltext

        return story_dict

    @property
    def all(self):
        return [self._get_story(story_id) for story_id in self.id_list]

    @property
    def developset(self):
        return [self._get_story(story_id) for story_id in self.id_list if 'developset' in story_id]

    @property
    def testset1(self):
        return [self._get_story(story_id) for story_id in self.id_list if 'testset1' in story_id]

    def random_stories(self, num_items, random_seed=None):
        if random_seed:
            random.seed(random_seed)

        copied_ids = deepcopy(self.id_list)
        result = []
        for i in range(num_items):
            item_index = random.randrange(len(copied_ids))
            story_id = copied_ids.pop(item_index)
            result.append(self._get_story(story_id))

        return result

    def all_questions_of_type(self, q_type):
        tuples = [s for s in [
            (story[qid][0], get_sentence_with_answer(story['text'], story[qid][1]), story[qid][1]) for story in
            self.all for qid in story
            if qid not in ['text', 'answer_key']
        ] if formulate_question(s[0])['qword'][0].lower() == q_type.lower()]

        return tuples

        # for question, answer_sentence, answer in tuples:
        #     if answer_sentence:
        #         print(question)
        #         print(answer_sentence)
        #         print(answer)


c = Corpus(['developset', 'testset1'])
for question, answer_sentence, answer in c.all_questions_of_type('who'):
    print(question)
    print(answer_sentence)
    print(answer)
    print()
for question, answer_sentence, answer in c.all_questions_of_type('what'):
    print(question)
    print(answer_sentence)
    print(answer)
    print()
for question, answer_sentence, answer in c.all_questions_of_type('when'):
    print(question)
    print(answer_sentence)
    print(answer)
    print()
for question, answer_sentence, answer in c.all_questions_of_type('where'):
    print(question)
    print(answer_sentence)
    print(answer)
    print()
for question, answer_sentence, answer in c.all_questions_of_type('why'):
    print(question)
    print(answer_sentence)
    print(answer)
    print()
for question, answer_sentence, answer in c.all_questions_of_type('how'):
    print(question)
    print(answer_sentence)
    print(answer)
    print()
# for t in c.all_questions_of_type('where'):
#     print(t)
