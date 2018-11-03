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


# def parse_for(tree, label):
#     if tree.label() == label:
#         return tree
#     else:
#         for child in tree:
#             if child.label() == label:
#                 return child
#             else:
#                 return parse_for(child, label)


tokens = nltk.word_tokenize("Why did George get on the bus?")
parsed = CoreNLPParser().parse(tokens)
constituent_trees = [x for x in parsed][0]

# print(constituent_trees)
# for tree in constituent_trees:
#     assert isinstance(tree, nltk.Tree)
#     # print(tree.label())
#
#     for subtree in tree:
#         # print(subtree.label())
#
#         for x in subtree:
#             if isinstance(x, nltk.Tree):
#                 print(x.label())
#
#                 for y in x:
#                     if isinstance(y, nltk.Tree):
#                         print(y.label())
#
#                         for z in y:
#                             if isinstance(z, nltk.Tree):
#                                 print(z.label())
#
#                                 for w in z:
#                                     if isinstance(w, nltk.Tree):
#                                         assert isinstance(w, nltk.Tree)
#                                         print(w.label())
#                                         print(w.leaves())
