import nltk
import text_analyzer
import re
import string
from enum import Enum
from spacy.tokens import Doc, Span, Token
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError, Synset
from text_analyzer import lemmatize
from parse import get_constituency_parse, get_dependency_parse, get_token_dependent_of_type, \
    get_subtree_dependent_of_type, get_spacy_dep_parse
from question_classifier import formulate_question
from sentence_similarity import sentence_similarity


# todo: where to implement modifiers...?
# todo: rename
# todo: implement NER?
class LSAnalyzer(object):
    QUESTION_WORDS = ['who', 'whom', 'whose',
                      'what', 'which',
                      'when', 'where', 'why', 'how']
    SUBJECTS = ['agent', 'expl', 'nsubj', 'nsubjpass', 'csubj', 'csubjpass']
    OBJECTS = ['attr', 'dative', 'dobj', 'iobj', 'obj', 'oprd']
    COMPLEMENTS = ['acomp', 'ccomp', 'pcomp', 'xcomp', 'mark']
    AUXILIARIES = ['aux', 'auxpass', 'cop', 'prt']
    PREPOSITIONS = ['conj', 'cc', 'preconj', 'mark', 'prep']
    NOUN_MODIFIERS = ['acl', 'acomp', 'amod', 'appos', 'case', 'ccomp', 'compound',
                      'det', 'nn', 'nounmod', 'nummod', 'poss',
                      'predet', 'quantmod', 'relcl']
    VERB_MODIFIERS = ['advcl', 'advmod', 'neg', 'npmod', 'xcomp', 'prt']
    PREP_MODIFIERS = ['pobj', 'pcomp']

    POS_NOUN = ['NN', 'NNS', 'NOUN', 'PRON', 'PROPN']
    POS_VERB = ['AUX', 'PART', 'VB', 'VBP', 'VBZ', 'VBD', 'VBG', 'VBN']
    POS_ADJ = ['ADJ', 'JJ', 'JJR', 'JJS']
    # see: https://github.com/clir/clearnlp-guidelines/blob/master/md/specifications/dependency_labels.md
    # for more details

    def __init__(self, raw_question):
        assert isinstance(raw_question, str)

        self.doc = get_spacy_dep_parse(raw_question)
        self.root = list(self.doc.sents)[0].root

        self.qword = ''
        self.subjects = []
        self.objects = []
        self.complements = []
        self.auxiliaries = []
        self.prepositions = []

        for child in self.root.children:
            if child.text.lower() in self.QUESTION_WORDS:
                if self.qword == '':
                    self.qword = child.text.lower()
                continue

            dependency = child.dep_
            if dependency in self.SUBJECTS:
                self.subjects.append(child)
            elif dependency in self.OBJECTS:
                self.objects.append(child)
            elif dependency in self.COMPLEMENTS:
                self.complements.append(child)
            elif dependency in self.AUXILIARIES:
                self.auxiliaries.append(child)
            elif dependency in self.PREPOSITIONS:
                self.prepositions.append(child)

        if self.complements:
            for complement in self.complements:
                for child in complement.children:
                    if child.text.lower() in self.QUESTION_WORDS:
                        if self.qword == '':
                            self.qword = child.text.lower()
                        continue

                    dependency = child.dep_
                    if dependency in self.SUBJECTS:
                        self.subjects.append(child)
                    elif dependency in self.OBJECTS:
                        self.objects.append(child)
                    elif dependency in self.COMPLEMENTS:
                        self.objects.append(child)
                    elif dependency in self.AUXILIARIES:
                        self.auxiliaries.append(child)
                    elif dependency in self.PREPOSITIONS:
                        self.prepositions.append(child)

        self._wants_dep = None
        self._wants_pos = None
        self._wants_wordnet = None
        self._aux_lemmas = [lemmatize(aux.text.lower())[0] for aux in self.auxiliaries]

    # todo: make this a bit more sophisticated/specific?
    @property
    def wants_dep(self):
        if self._wants_dep is None:
            if self.qword == 'who':
                self._wants_dep = self.SUBJECTS + self.OBJECTS
            elif self.qword == 'what':
                if self.auxiliaries:
                    if 'do' in self._aux_lemmas and 'be' not in self._aux_lemmas:       # 'do' case
                        self._wants_dep = self.OBJECTS + self.AUXILIARIES
                    elif 'be' in self._aux_lemmas and 'do' not in self._aux_lemmas:     # 'be'/general case
                        self._wants_dep = self.NOUN_MODIFIERS + self.VERB_MODIFIERS + self.OBJECTS
                    else:                                                               # both cases
                        self._wants_dep = self.NOUN_MODIFIERS + self.VERB_MODIFIERS + self.OBJECTS + self.AUXILIARIES
                else:                                                                   # general case
                    self._wants_dep = self.NOUN_MODIFIERS + self.VERB_MODIFIERS + self.OBJECTS + self.AUXILIARIES
            elif self.qword == 'when':
                self._wants_dep = self.AUXILIARIES + self.PREPOSITIONS + self.PREP_MODIFIERS
            elif self.qword == 'where':
                self._wants_dep = self.AUXILIARIES + self.PREPOSITIONS + self.PREP_MODIFIERS

            # todo: look into these two
            elif self.qword == 'why':
                self._wants_dep = self.AUXILIARIES
            elif self.qword == 'how':
                self._wants_dep = self.AUXILIARIES + self.NOUN_MODIFIERS + self.VERB_MODIFIERS

            else:
                self._wants_dep = []

        return self._wants_dep
        
    # TODO
    @property
    def wants_pos(self):
        if self._wants_pos is None:
            if self.qword == 'who':
                self._wants_pos = self.POS_NOUN
            elif self.qword == 'what':
                if 'do' in self._aux_lemmas and 'be' not in self._aux_lemmas:           # 'do' case
                    self._wants_pos = self.POS_NOUN + self.POS_VERB
                elif 'be' in self._aux_lemmas and 'do' not in self._aux_lemmas:     # 'be'/general case
                    self._wants_pos = self.POS_NOUN + self.POS_ADJ
                else:  # both cases
                    self._wants_pos = self.POS_NOUN + self.POS_VERB + self.POS_ADJ
            elif self.qword == 'when':
                pass
            elif self.qword == 'where':
                pass
            elif self.qword == 'why':
                pass
            elif self.qword == 'how':
                pass    # make sure to include NUM

            else:
                self._wants_pos = []

        return self._wants_pos

    # TODO
    @property
    def wants_wordnet(self):
        if self._wants_wordnet is None:
            if self.qword == 'who':
                self._wants_wordnet = [
                    wn.synset('entity.n.01'),
                    wn.synset('group.n.01')
                ]
            elif self.qword == 'what':
                # arg_synsets = [
                #     best_synset(branch.text, branch.pos_) for branch in [
                #         head.subtree for head in self.subjects + self.objects
                #     ]
                # ]
                arg_synsets = []
                for head in self.subjects + self.objects:
                    for branch in head.subtree:
                        arg_synset = best_synset(branch.text, branch.pos_)
                        if arg_synset:
                            arg_synsets.append(arg_synset)
                if arg_synsets:
                    self._wants_wordnet = arg_synsets
                else:
                    self._wants_wordnet = []

                # TODO: see if this distinction is necessary/helpful here (perhaps I shouldn't consider subject)
                # in one of them -- might also be true of both?)
                # if 'do' in self._aux_lemmas and 'be' not in self._aux_lemmas:   # 'do' case
                #     pass
                # else:                                                           # 'be'/general case
                #     pass
            elif self.qword == 'when':
                pass
            elif self.qword == 'where':
                pass
            elif self.qword == 'why':
                pass
            elif self.qword == 'how':
                pass

            else:
                self._wants_wordnet = []

        return self._wants_wordnet

    # todo: also consider auxiliaries, modifiers, etc.
    def sentence_match(self, sentence):
        root = None
        if isinstance(sentence, str):
            root = list(get_spacy_dep_parse(sentence).sents)[0].root
        elif isinstance(sentence, Doc):
            root = list(sentence.sents)[0].root
        elif isinstance(sentence, Span):
            root = sentence.root
        elif isinstance(sentence, Token):
            root = sentence
        assert isinstance(root, Token)

        args = []
        auxiliaries = []
        prepositions = []
        
        for child in root.subtree:
            dependency = child.dep_
            if dependency in self.SUBJECTS or dependency in self.OBJECTS:
                args.append(child)
            elif dependency in self.AUXILIARIES:
                auxiliaries.append(child)
            elif dependency in self.PREPOSITIONS:
                prepositions.append(child)

        # note: we really do actually want this in ascending order, since the worst match isn't
        # in the question, which means it's more likely to be the answer
        args_by_sim = sorted(
            [(s_arg, my_arg) for s_arg in args for my_arg in self.subjects + self.objects],
            key=lambda pair: sentence_similarity(
                to_sentence(pair[0]),
                to_sentence(pair[1])
            )
        )

        # todo: give some kind of evaluation metric. idea: 1 point if we have wants_wordnet hypernym match, then up to
        # a point per match on wants_pos and wants_dep
        if self.qword == 'who':
            # syn_people = [deps_which_are_hyponym_of()]
            if args_by_sim:
                for s_arg, _ in args_by_sim:
                    if self.wants_wordnet:
                        for synset_want in self.wants_wordnet:
                            if synset_want in root_hypernyms(
                                best_synset(s_arg.text, s_arg.pos_)
                            ):
                                return to_sentence(s_arg)
                return to_sentence(args_by_sim[0])
        elif self.qword == 'what':
            pass
        elif self.qword == 'when':
            pass
        elif self.qword == 'where':
            pass
        elif self.qword == 'why':
            pass
        elif self.qword == 'how':
            pass

    # todo: also consider auxiliaries, modifiers, etc.
    def produce_answer_phrase(self, sentence):
        root = None
        if isinstance(sentence, str):
            root = list(get_spacy_dep_parse(sentence).sents)[0].root
        elif isinstance(sentence, Doc):
            root = list(sentence.sents)[0].root
        elif isinstance(sentence, Span):
            root = sentence.root
        elif isinstance(sentence, Token):
            root = sentence
        assert isinstance(root, Token)

        args = []
        auxiliaries = []
        prepositions = []

        matches = {}        # key: number of matches (i.e. 0 to 3), value: list of matching heads ('children')
        for child in root.subtree:
            if child.i > root.i:    # only want tokens to the right of the verb
                if child.dep_ in self.SUBJECTS or child.dep_ in self.OBJECTS:
                    args.append(child)
                elif child.dep_ in self.AUXILIARIES:
                    auxiliaries.append(child)
                elif child.dep_ in self.PREPOSITIONS:
                    prepositions.append(child)

                score = 0
                if child.dep_ in self.wants_dep:
                    score += 1
                if child.pos_ in self.wants_pos:
                    score += 1
                if self.wants_wordnet:
                    hypernyms = root_hypernyms(best_synset(child.text, child.pos_))
                    if hypernyms:
                        for synset_want in self.wants_wordnet:
                            if synset_want in hypernyms:
                                score += 1
                                break
                if score in matches.keys():
                    matches[score] += [child]
                else:
                    matches[score] = [child]

        for score in sorted(matches.keys(), reverse=True):
            match_list = matches[score]
            if len(match_list) == 1:
                return to_sentence(match_list[0])
            else:
                # TODO: something more sophisticated here...?
                return to_sentence(max(match_list, key=lambda x: len(list(x.subtree))))
                # return to_sentence(match_list[0])

    def verb_similarity(self, verb):
        return best_synset(verb, 'v').path_similarity(best_synset(self.root.text, 'v'))


def to_sentence(tokens, index=0):
    if isinstance(tokens, str):
        return tokens
    elif isinstance(tokens, list):
        if isinstance(tokens[index], tuple):
            return ' '.join([
                token[index] for token in tokens
            ])
        else:
            return ' '.join(tokens)
    elif isinstance(tokens, Token):
        return ' '.join([token.text for token in tokens.subtree])


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
    lemma = lemmatize(word_str.lower())
    if lemma:
        lemma = lemma[0]
    tag = to_wordnet_tag(pos_tag)

    try:
        if lemma and pos_tag:
            synset = wn.synset('{}.{}.{}'.format(lemma, tag, '01'))
            if synset:
                return synset
            raise WordNetError
    except WordNetError:
        try:
            lemmas = wn.lemmas(lemma)
            if lemmas:
                synset = lemmas[0].synset()
                if synset:
                    return synset
            raise WordNetError
        except WordNetError:
            pass


def get_lexname(word_or_synset, pos_tag=None):
    if isinstance(word_or_synset, Synset):
        return word_or_synset.lexname()
    elif isinstance(word_or_synset, str):
        assert isinstance(pos_tag, str)
        synset = best_synset(word_or_synset, pos_tag)
        if synset:
            return synset.lexname()


def root_hypernyms(synset):
    if synset is None:
        return None
    assert isinstance(synset, Synset)

    hypernyms = synset.hypernyms()
    result = []
    if not hypernyms:
        result += [synset]
    else:
        roots = [root_hypernyms(hypernym) for hypernym in hypernyms]
        if isinstance(roots, list):
            for root_group in roots:
                for root in root_group:
                    if root not in result:
                        result += [root]
        elif isinstance(roots, Synset):
            if roots not in result:
                result += [roots]
    return result


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


if __name__ == '__main__':
    # d = wn.synsets('doctor', 'n')[0]
    # p = wn.synsets('person', 'n')[0]
    # c = wn.synsets('cat', 'n')[0]
    # assert p in d.closure(lambda x: x.hypernyms())
    # assert d in p.closure(lambda x: x.hyponyms())
    # assert p not in c.closure(lambda x: x.hypernyms())
    #
    # assert d in wn.synsets('MD', 'n') and d in wn.synsets('Dr.', 'n')
    # assert d.shortest_path_distance(p) < d.shortest_path_distance(c)
    
    test = LSAnalyzer('What is Haider accused of being?')
    response = test.produce_answer_phrase('Haider is accused of being a Nazi sympathizer.')
    print(response)

    test = LSAnalyzer('On what was Shoemaker considered an authority?')
    response = test.produce_answer_phrase(
        'He was considered an authority on craters and the collisions that cause them.')
    print(response)

    test = LSAnalyzer('What usually causes mudslides?')
    response = test.produce_answer_phrase(
        'They are usually caused by weakened land on hills and mountains.')
    print(response)

    test = LSAnalyzer('What can mudslides do when they start moving quickly?')
    response = test.produce_answer_phrase(
        'Mudslides can move quickly and powerfully, picking up rocks, trees, houses and cars.')
    print(response)
