from parse import get_sentence
from question_classifier import formulate_question
from nltk.corpus import stopwords


def calculate_overlap(string1, string2):
    overlap = 0
    for word in string1:
        if word in string2 and word not in stopwords.words('english'):
            overlap += 1
    return overlap


def get_answer_phrase(question_sentence, answer_sentence):
    """
    Extract the narrowest phrase from the answer sentence containing the full answer to the question sentence
    :param question_sentence: an answer sentence
    :param answer_sentence: a question sentence
    :return: the narrowest phrase containing the full answer
    """
    question = formulate_question(question_sentence)
    answer = get_sentence(answer_sentence)

    if question['qword'][0].lower() == "what":
        pass

    elif question['qword'][0].lower() == "when":
        if 'dobj' in question:
            pass

    elif question['qword'][0].lower() == "where":
        pass

    elif question['qword'][0].lower() == "which":
        pass

    elif question['qword'][0].lower() == "who":
        pass

    elif question['qword'][0].lower() == "why":
        pass

    elif question['qword'][0].lower() == "how":
        pass

    # if nothing else worked, just return the whole sentence
    else:
        return answer_sentence


if __name__ == "__main__":
    pass
