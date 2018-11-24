import spacy
from spacy.lemmatizer import Lemmatizer
import sys


def get_all_dependents(doc, dep):
    for token in doc:
        if token.dep_ == dep and token.head.pos_ == 'VERB':
            return [sub for sub in token.subtree]


def get_dependency(doc, dep):
    return [token for token in doc if token.dep_ == dep]


def dependency(nlp):
    doc = nlp(u"The man in blue overalls gave his coworker a gift on the bus.")
    print(get_all_dependents(doc, 'nsubj'))
    print(get_dependency(doc, 'ROOT'))
    print(get_all_dependents(doc, 'dative'))
    print(get_all_dependents(doc, 'dobj'))


def similarity(nlp):
    dog, _, cat, _, apples = nlp(u"dogs and cats and apples")
    print(dog.similarity(cat))
    print(dog.similarity(apples))
    print(cat.similarity(apples))


def word_similarity(nlp, word1, word2):
    word1, word2 = nlp(' '.join([word1, word2]))
    return word1.similarity(word2)


def integrative(nlp):
    question = nlp(u"What did Bill buy?")
    answer1 = nlp(u"Bill purchased a new pair of shoes.")
    answer2 = nlp(u"Bill ate the last piece of pizza.")

    q_verb = get_dependency(question, 'ROOT')[0]

    print(get_all_dependents(
        max(
            # [get_all_dependents(a, 'dobj') for a in (answer1, answer2)],
            (answer1, answer2),
            key=lambda x: q_verb.similarity(get_dependency(x, 'ROOT')[0])
        ), 'dobj'
    ))

def entities(nlp, sent, word):
    sent = nlp(sent)

    root = get_dependency(sent, 'ROOT')[0]
    ents = []
    for ent in sent.ents:
        ents.append((ent.text, ent.label_))
    print(sent)
    print(ents)
    print(root)
    for w in sent:
        print(w, end=': ')
        print(word_similarity(nlp, w, word))
    print()


def main():
    # nlp = spacy.load('en_core_web_sm')      # alt: en_core_web_md, en_core_web_lg
    # dependency(nlp)
    #
    # nlp = spacy.load('en_vectors_web_lg')   # identical to en_core_web_lg, but only looks at vectors (no parse)
    # similarity(nlp)
    #
    # nlp = spacy.load('en_core_web_lg')
    # integrative(nlp)

    nlp = spacy.load('en_core_web_sm')
    while(True):
        sent = input("Enter sentence: ")
        if sent is None or sent.lower() == 'quit':
            break
        word = input("Enter word: ")
        if word is None:
            break
        entities(nlp, sent, word)


if __name__ == '__main__':
    main()
