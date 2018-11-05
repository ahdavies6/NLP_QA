from parse import *


def formulate_question(question_sentence):
    """
    Formulates a Question object from question_sentence
    :param question_sentence: a string of the question sentence
    :return: a Question object representing the dependency structure of the question
    """
    # find the "question word" (see: "5 W's", "WH word") for the question
    q_parsed = next(CoreNLPParser().raw_parse(question_sentence))
    q_word = None
    for subtree in q_parsed.subtrees():
        if subtree.label() == "SBARQ":
            for sub_subtree in subtree.subtrees():
                assert isinstance(sub_subtree, Tree)
                if sub_subtree.label()[0] == "W" and sub_subtree.label()[0:2] != "WH":
                    q_word = (sub_subtree.leaves()[0], sub_subtree.label())
                    break
            break

    sentence = get_sentence(question_sentence)
    sentence['qword'] = q_word
    sentence.__class__ = Question   # "cast" as a Question

    return sentence


if __name__ == "__main__":
    # a = formulate_question("Did the man in blue overalls give Lisa the memo?")
    # b = formulate_question("Why did the man in blue overalls give Lisa the memo?")
    # c = formulate_question("Why did the man in blue overalls give Lisa the memo on the bus?")
    d = formulate_question("Who is the principal of South Queens Junior High School?")
    # todo: figure out how to deal with a nested clause like this
    # e = formulate_question("If you were a student, how much would a club membership cost you?")
    f = formulate_question("Where is South Queens Junior High School?")
    x = None
