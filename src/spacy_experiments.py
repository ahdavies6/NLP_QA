import spacy


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


def main():
    # nlp = spacy.load('en_core_web_sm')
    # dependency(nlp)
    # similarity(nlp)

    nlp = spacy.load('en_core_web_lg')
    integrative(nlp)


if __name__ == '__main__':
    main()
