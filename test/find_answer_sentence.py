from nltk import sent_tokenize
from answer_identification import calculate_overlap


def get_sentence_with_answer(story, answer):
    sentences = sent_tokenize(story)
    has_answer = []
    for sentence in sentences:
        if answer in sentence:
            has_answer.append(sentence)

    if len(has_answer) == 1:
        return has_answer[0]
    elif len(has_answer) > 1:
        return max(has_answer, key=lambda x: calculate_overlap(x, answer))
    else:
        return max(sentences, key=lambda x: calculate_overlap(x, answer))


def main():
    pass


if __name__ == '__main__':
    main()
