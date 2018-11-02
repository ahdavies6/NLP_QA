import nltk
from nltk.parse.corenlp import CoreNLPParser


# def question_to_proposition(question):
#     subject = None
#     verb = None
#     verb_arg = None
#     for word, tag in tagged:
#         if tag[0] == 'V':
#             assert verb is None
#             verb = word
#         elif (
#             tag[0:2] == 'PR' or     # pronoun
#             tag == "NNP"            # singular proper noun
#         ):
#             if subject is None:
#                 subject = word
#
#     pass


tokens = nltk.word_tokenize("Why did George get on the bus?")
parsed = CoreNLPParser().parse(tokens)
constituent_trees = [x for x in parsed][0]
print(constituent_trees)
