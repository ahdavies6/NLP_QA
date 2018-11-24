from nltk import sent_tokenize
from text_analyzer import lemmatize
from answer_identification import calculate_overlap


def get_sentence_with_answer(story, answer):
    if isinstance(answer, list):
        answer = max(answer, key=lambda x: len(x.split()))

    sentences = sent_tokenize(story)
    answer = lemmatize(answer)
    has_answer = []
    for sentence in sentences:
        sentence_lemmas = lemmatize(sentence)
        if set([a.lower() for a in answer]) <= set([s.lower() for s in sentence_lemmas]):
            has_answer.append(sentence)

    if len(has_answer) == 1:
        return has_answer[0]
    elif len(has_answer) > 1:
        return max(has_answer, key=lambda x: calculate_overlap(x, answer))
