import re
import sys
from ner.text_analyzer import *


headline_pattern = r'HEADLINE:\s*(.*)\n'
date_pattern = r'DATE:\s*(.*)\n'
story_pattern = r'STORYID:\s*(.*)\n'
text_pattern = r'TEXT:\s*([\s\w\d\S\W\D]*)'


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

    pass

