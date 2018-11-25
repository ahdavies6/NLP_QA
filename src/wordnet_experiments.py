from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError, Synset
from text_analyzer import lemmatize


d = wn.synsets('doctor', 'n')[0]
p = wn.synsets('person', 'n')[0]
c = wn.synsets('cat', 'n')[0]
assert p in d.closure(lambda x: x.hypernyms())
assert d in p.closure(lambda x: x.hyponyms())
assert p not in c.closure(lambda x: x.hypernyms())

assert d in wn.synsets('MD', 'n') and d in wn.synsets('Dr.', 'n')
assert d.shortest_path_distance(p) < d.shortest_path_distance(c)


def to_wordnet_tag(tag):
    if tag in ['NOUN', 'PRON', 'PROPN', 'n']:
        return 'n'
    elif tag in ['VERB', 'HVS', 'MD', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'v']:
        return 'v'
    elif tag in ['ADJ', 'JJ', 'JJR', 'JJS', 'a']:
        return 'a'
    elif tag in ['ADV', 'RB', 'RBR', 'RBS', 'RP', 'r']:
        return 'r'


def best_synset(word_str, pos_tag='n'):
    lemma = lemmatize(word_str.lower())[0]
    tag = to_wordnet_tag(pos_tag)

    try:
        if lemma and pos_tag:
            synset = wn.synset('{}.{}.{}'.format(lemma, tag, '01'))
            if synset:
                return synset
            raise WordNetError
    except WordNetError:
        try:
            synset = wn.lemmas(lemma)[0].synset()
            if synset:
                return synset
        except WordNetError:
            pass


def get_lexname(word_or_synset, pos_tag=None):
    if isinstance(word_or_synset, Synset):
        return word_or_synset.lexname()
    elif isinstance(word_or_synset, str):
        assert isinstance(pos_tag, str)
        synset = best_synset(word_or_synset[0], word_or_synset[1])
        if synset:
            return synset.lexname()


def deps_which_are_hyponym_of(head, hypernym):
    # deps = [token for token in head.subtree if token.dep_ in dep_label_list]
    result = []

    # for dep in head.subtree:
    #     try:
    #         lemmas = lemmatize(dep.text.lower())
    #         tag = to_wordnet_tag(dep.pos_)
    #         if lemmas and tag:
    #             d_synset = wn.synset('{}.{}.{}'.format(lemmas[0], tag, '01'))
    #             if not d_synset:
    #                 raise WordNetError
    #             # NOTE: the same can be expressed with '<', '>'
    #             if hypernym in list(d_synset.closure(lambda x: x.hypernyms())) + [d_synset]:
    #                 result.append(dep)
    #         else:
    #             break
    #     except WordNetError:
    #         try:
    #             d_synset = wn.lemmas(lemmatize(dep.text.lower())[0])
    #             if not d_synset:
    #                 raise WordNetError
    #             d_synset = d_synset[0].synset()
    #             if hypernym in list(d_synset.closure(lambda x: x.hypernyms())) + [d_synset]:
    #                 result.append(dep)
    #         except WordNetError:
    #             pass

    for dep in head.subtree:
        synset = best_synset(head.text.lower(), head.pos_)
        if synset:
            if hypernym in list(synset.closure(lambda x: x.hypernyms())) + [synset]:
                result.append(dep)

    return result
