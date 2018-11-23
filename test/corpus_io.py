import os
import re
import random
from copy import deepcopy


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'
question_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Difficulty:\s*(.*)\s*'
answer_pattern = r'QuestionID:\s*(.*)\s*Question:\s*(.*)\s*Answer:\s*(.*)\s*Difficulty:\s*(.*)\s*'


class Corpus(object):

    def __init__(self):
        all_filenames = []
        for path, dirs, filenames in os.walk(os.getcwd() + '/developset/'):
            all_filenames += ['./developset/' + filename for filename in filenames]
            break
        for path, dirs, filenames in os.walk(os.getcwd() + '/testset1/'):
            all_filenames += ['./testset1/' + filename for filename in filenames]
            break

        all_filenames = sorted(all_filenames)
        self.id_list = []
        for i in range(len(all_filenames)):
            if i % 3 == 0:  # answers file
                self.id_list.append(all_filenames[i].split('.')[1])

    def get_random_stories(self, num_items, random_seed=None):
        if random_seed:
            random.seed(random_seed)

        copied_ids = deepcopy(self.id_list)
        result = []
        for i in range(num_items):
            item_index = random.randrange(len(copied_ids))
            story_id = copied_ids.pop(item_index)

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

            result.append(story_dict)

        return result
