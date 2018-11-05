from parse import *


class Sentence(object):

    def __init__(self, dependents=None):
        self._dependents = dependents if dependents else {}

    def __getitem__(self, item):
        return self._dependents[item]

    def __setitem__(self, key, value):
        self._dependents[key] = value


def get_answer_phrase(question_sentence, answer_sentence):
    """
    Extract the narrowest phrase from the answer sentence containing the answer to the question sentence
    :param question_sentence: an answer sentence
    :param answer_sentence: a question sentence
    :return: the narrowest phrase containing the answer
    """
    question = formulate_question(question_sentence)

    # q_dependencies = next(CoreNLPDependencyParser().raw_parse(question_sentence))
    # assert isinstance(q_dependencies, DependencyGraph)
    # t_dependencies = list(q_dependencies.triples())
    # # verb = q_dependencies.root['word']
    # verb_new = (q_dependencies.root['word'], q_dependencies.root['tag'])
    # # subj = None
    # # iobj = None
    # # dobj = None
    # # extra = []
    # dependent_heads = {"root": verb_new}
    # for head, relationship, dependent in t_dependencies:
    #     # item 1: (head, POS); item 2: relationship; item 3: (dependent, POS)
    #     # if relationship == "nsubj" and head == verb:
    #     #     subj = dependent
    #     # elif relationship == "iobj" and head == verb:
    #     #     iobj = dependent
    #     # elif relationship == "dobj" and head == verb:
    #     #     dobj = dependent
    #     if head == verb_new:
    #         dependent_heads[relationship] = dependent

    a_dependency_graph = next(CoreNLPDependencyParser().raw_parse(answer_sentence))
    assert isinstance(a_dependency_graph, DependencyGraph)
    root = (a_dependency_graph.root['word'], a_dependency_graph['tag'])
    a_dependency_list = list(a_dependency_graph.triples())
    # a_heads =


if __name__ == "__main__":
    pass
