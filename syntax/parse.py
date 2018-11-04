from enum import Enum
from nltk import Tree
from nltk.parse.corenlp import CoreNLPParser, CoreNLPDependencyParser
from nltk.parse.dependencygraph import DependencyGraph
# from nltk.parse.bllip import BllipParser
import nltk


# todo: try this out
# from nltk.stem.wordnet import WordNetLemmatizer


# class WhQuestions(Enum):
#     WHO = 0     # also includes "whom", "whose"
#     WHAT = 1
#     WHERE = 2
#     WHEN = 3
#     WHY = 4
#     HOW = 5
#     WHICH = 6


class Question(object):

    # def __init__(self, q_class, q_word, verb, subj, iobj, dobj):
    # todo: set this constructor up to accept an initial dictionary
    def __init__(self):
        # self.q_class = q_class
        # self.q_word = q_word
        # self.verb = verb
        # self.subj = subj
        # self.iobj = iobj
        # self.dobj = dobj
        self._dependents = {}

    def __getitem__(self, item):
        return self._dependents[item]

    def __setitem__(self, key, value):
        self._dependents[key] = value


def parse_for(tree, label):
    """
    :param tree: The parse tree (typically beginning at ROOT)
    :param label: The non-terminal label
    :return: Returns a list of Tree representations of all non-terminals in the tree with the specified label.
        If none can be found, returns None
    """
    # trees = []
    # if tree.label() == label:
    #     trees.append(tree)
    # else:
    #     for child in tree:
    #         if isinstance(child, Tree):
    #             grandchildren = parse_for(child, label)
    #             if grandchildren is not None:
    #                 for grandchild in grandchildren:
    #                     trees.append(grandchild)
    # return trees if trees else None

    # trees = []
    # assert isinstance(tree, Tree)
    # for tree in tree.subtrees():
    #     if tree.label() == label:
    #         trees.append(tree)
    # return trees if trees else None

    subtrees = [x for x in tree.subtrees(filter=lambda f: f.label() == label)]
    return subtrees if subtrees else None


def get_all_dependents(graph, node):
    dependents = []
    for key in node['deps']:
        second_order_dependents = []
        for i in node['deps'][key]:
            third_order_dependents = get_all_dependents(graph, graph.nodes[i])
            if third_order_dependents:
                second_order_dependents.append((graph.nodes[i], third_order_dependents))
            else:
                second_order_dependents.append(graph.nodes[i])
        if second_order_dependents:
            dependents.append((node, second_order_dependents))
        else:
            dependents.append(node)
    return dependents


def put_in_order(dependents, sentence):
    """
    :param dependents: (unordered) set of dependents in the sentence
    :param sentence: (ordered) list of tuples of word tokens [(word1, tag1), (word2, tag2), ...]
    :return: the dependents, in the order they appear in the sentence
    """

    # # transform SVO chunks into contiguous strings of words from sentence
    # subj_ordered = []
    # iobj_ordered = []
    # dobj_ordered = []
    # for word, tag in sentence:
    #     if word in subj and len([x[0] for x in subj_ordered if x[0] == word]) < len([x for x in subj if x == word]):
    #         subj_ordered.append((word, tag))
    #     elif word in iobj and len([x[0] for x in iobj_ordered if x[0] == word]) < len([x for x in iobj if x == word]):
    #         iobj_ordered.append((word, tag))
    #     elif word in dobj and len([x[0] for x in dobj_ordered if x[0] == word]) < len([x for x in dobj if x == word]):
    #         dobj_ordered.append((word, tag))

    potential_order = []
    for word, tag in sentence:
        if word in dependents:
            potential_order.append((word, tag))
            if len(potential_order) == len(dependents):
                return potential_order
        else:
            potential_order = []


# def flatten(monstrosity):
#     order = {}
#     for monster in monstrosity:
#         if isinstance(monster, dict):
#             order[monster['address']] = monster['word']
#         elif isinstance(monster, list):
#             pass


def traverse_dep_tree(tree):
    nodes = [tree.label()]
    for subtree in tree:
        if isinstance(subtree, Tree):
            nodes.extend(traverse_dep_tree(subtree))
        elif isinstance(subtree, str):
            nodes.append(subtree)
    return nodes


def formulate_question(question):
    # gather syntactic data from parse
    q_parsed = next(CoreNLPParser().raw_parse(question))
    q_class = None
    q_word = None
    for subtree in q_parsed.subtrees():
        if subtree.label() == "SQ":
            # q_class = QuestionClass.POLAR
            q_word = next(subtree.subtrees())[0].leaves()[0]
            break
        elif subtree.label() == "SBARQ":
            # q_class = QuestionClass.WH
            for sub_subtree in subtree.subtrees():
                if sub_subtree.label()[0:2] == "WH":
                    q_word = sub_subtree.leaves()[0]
                    break
            break

    # gather SVO data from dependency parse
    q_dependencies = next(CoreNLPDependencyParser().raw_parse(question))
    assert isinstance(q_dependencies, DependencyGraph)
    t_dependencies = list(q_dependencies.triples())
    verb = q_dependencies.root['word']
    subj = None
    iobj = None
    dobj = None
    extra = []
    # TODO: get dependents of subj, dobj, iobj, etc.
    for (head, head_pos), relationship, (dependent, dependent_pos) in t_dependencies:
        # item 1: (head, POS); item 2: relationship; item 3: (dependent, POS)
        if relationship == "nsubj" and head == verb:
            subj = dependent
        elif relationship == "iobj" and head == verb:
            iobj = dependent
        elif relationship == "dobj" and head == verb:
            dobj = dependent

    # dobjs = get_all_dependents(q_dependency, q_dependency.nodes[q_dependency.root['deps']['dobj'][0]])
    for dependency in q_dependencies.tree():
        if isinstance(dependency, Tree):
            if dependency.label() == subj:
                # subj = dependency.leaves() + [dependency.label()]
                subj = traverse_dep_tree(dependency)
            elif dependency.label() == iobj:
                # iobj = dependency.leaves() + [dependency.label()]
                iobj = traverse_dep_tree(dependency)
            elif dependency.label() == dobj:
                # dobj = dependency.leaves() + [dependency.label()]
                dobj = traverse_dep_tree(dependency)
            # # TODO: integrate this somehow (would include adverbs, prep phrases, etc.)
            # else:
            #     extra.append(dependency.flatten())
        else:
            if dependency == subj:
                subj = [dependency]
            elif dependency == iobj:
                iobj = [dependency]
            elif dependency == dobj:
                dobj = [dependency]

    # get full sentence as S = [(word1, tag1), ...]
    sentence = []
    for i in range(1, len(q_dependencies.nodes)):
        sentence.append((q_dependencies.nodes[i]['word'], q_dependencies.nodes[i]['tag']))

    # # get phrase from "argument" (e.g. subj, iobj, etc.)
    # for subtree in q_parsed.subtrees():
    #     assert isinstance(subtree, Tree)
    #     if {*subtree.leaves()} == {*subj}:
    #         subj = subtree
    #     elif {*subtree.leaves()} == {*iobj}:
    #         iobj = subtree
    #     elif {*subtree.leaves()} == {*dobj}:
    #         dobj = subtree
    #     # TODO: integrate this somehow (would include adverbs, prep phrases, etc.)
    #     else:
    #         pass

    # TODO: try this!
    # temp = CoreNLPParser().make_tree(q_thing)

    # # get full sentence as S = [(word1, tag1), ...]
    # sentence = []
    # for i in range(1, len(q_dependencies.nodes)):
    #     sentence.append(q_dependencies.nodes[i]['word'])

    subj_final = put_in_order(subj, sentence)
    iobj_final = put_in_order(iobj, sentence)
    dobj_final = put_in_order(dobj, sentence)

    q_final = Question()
    q_final['wh'] = q_word
    q_final['verb'] = (q_dependencies.root['word'], q_dependencies.root['tag'])
    q_final['subj'] = subj_final
    q_final['iobj'] = iobj_final
    q_final['dobj'] = dobj_final

    return q_final

    # todo: remove deprecated
    # # transform SVO chunks into contiguous strings of words from sentence
    # subj_ordered = []
    # iobj_ordered = []
    # dobj_ordered = []
    # for word, tag in sentence:
    #     if word in subj and len([x[0] for x in subj_ordered if x[0] == word]) < len([x for x in subj if x == word]):
    #         subj_ordered.append((word, tag))
    #     elif word in iobj and len([x[0] for x in iobj_ordered if x[0] == word]) < len([x for x in iobj if x == word]):
    #         iobj_ordered.append((word, tag))
    #     elif word in dobj and len([x[0] for x in dobj_ordered if x[0] == word]) < len([x for x in dobj if x == word]):
    #         dobj_ordered.append((word, tag))

    # # todo: transform sentence into pieces of parse tree
    # subj_phrases = []
    # iobj_phrases = []
    # dobj_phrases = []
    # for subtree in q_parsed.subtrees():
    #     assert isinstance(subtree, Tree)
    #     for i in range(min(len(subtree.leaves()), len(subj_ordered))):
    #         if subtree.leaves()[i] != subj_ordered:
    #             break
    #     subj_phrases.append(subtree)
    #     for i in range(min(len(subtree.leaves()), len(subj_ordered))):
    #         subj_ordered.pop(0)

    # return Question(
    #     q_class,
    #     q_word,
    #     verb,
    #     subj_ordered,
    #     iobj_ordered,
    #     dobj_ordered
    # )


if __name__ == "__main__":
    # a = formulate_question("Did the man in blue overalls give Lisa the memo?")
    # b = formulate_question("Why did the man in blue overalls give Lisa the memo?")
    c = formulate_question("Why did the man in blue overalls give Lisa the memo on the bus?")
    x = None
