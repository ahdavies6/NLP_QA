from parse import DependencyNode, get_sentence
from nltk import Tree
from nltk.parse.corenlp import CoreNLPParser


class Question(object):

    def __init__(self, sentence_structure, question_word):
        self._root_node = sentence_structure
        self._q_pair = question_word

    def __str__(self):
        return self._root_node.__str__()

    def __getitem__(self, item):
        if item == 'qword':
            # todo: get the actual structure (and then remove self._q_word)
            return self._q_pair
        else:
            return self._root_node.__getitem__(item)

    def __contains__(self, item):
        return self._root_node.__contains__(item)


def formulate_question(question_sentence):
    """
    Formulates a Question object from question_sentence
    :param question_sentence: a string of the question sentence
    :return: a Question object representing the dependency structure of the question
    """
    # find the "question word" (see: "5 W's", "WH word") for the question
    q_parsed = next(CoreNLPParser().raw_parse(question_sentence))
    q_word = None
    # try out the normal constructions to find a question
    for subtree in q_parsed.subtrees():
        if subtree.label() in ["SBARQ", "SBAR", "SINV"]:
            for sub_subtree in subtree.subtrees():
                if sub_subtree.label()[0] == "W" and sub_subtree.label()[0:2] != "WH":
                    q_word = (sub_subtree.leaves()[0], sub_subtree.label())
                    break
            break
    # the normal constructions didn't work; just grab the first question word
    if q_word is None:
        for subtree in q_parsed.subtrees():
            if subtree.label()[0] == "W" and subtree.label()[0:2] != "WH":
                q_word = (subtree.leaves()[0], subtree.label())

    return Question(get_sentence(question_sentence), q_word)


if __name__ == "__main__":
    # b = formulate_question("Why did the man in blue overalls give Lisa the memo?")
    # c = formulate_question("Why did the man in blue overalls give Lisa the memo on the bus?")
    # d = formulate_question(
    #     "Why does Carole Mills think it is more of a health risk not to eat country food than to eat it?"
    # )
    # e = formulate_question(
    #     "According to Bushie , what should the schools do to combat racism?"
    # )
    # f = formulate_question(
    #     " Of which province in Canada was Stanley Faulder a native?"
    # )
    g = formulate_question(
        "Besides being very strong , what are the advantages of BioSteel?"
    )
    h = formulate_question(
        "According to NATO spokesman Jamie Shea , how is troop deployment going?"
    )
    i = formulate_question(
        "According to their Quebec office , how did McDonald 's feel about the vote to unionize the Montreal franchise?"
    )
    x = None
