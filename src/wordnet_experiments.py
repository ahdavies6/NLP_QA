from queue import Queue
from spacy.tokens import Doc, Span, Token
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError, Synset
from text_analyzer import lemmatize
from parse import get_spacy_dep_parse
from sentence_similarity import sentence_similarity


# todo: where to implement modifiers...?
# todo: rename
# todo: implement NER?
class LSAnalyzer(object):
    QUESTION_WORDS = ['who', 'whom', 'whose',
                      'what', 'which',
                      'when', 'where', 'why', 'how']
    SUBJECTS = ['agent', 'expl', 'nsubj', 'nsubjpass', 'csubj', 'csubjpass']
    OBJECTS = ['attr', 'dative', 'dobj', 'iobj', 'obj', 'oprd', 'pobj']
    CONJUNCTIONS = ['acomp', 'ccomp', 'conj', 'cc', 'dep', 'pcomp', 'preconj', 'xcomp', 'mark']
    AUXILIARIES = ['aux', 'auxpass', 'cop', 'prt']
    PREPOSITIONS = ['prep']
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
        self.root_synset = best_synset(self.root.text, 'v')

        self.qword = ''
        self.subjects = []
        self.objects = []
        # self.conjunctions = []
        self.auxiliaries = []
        self.prepositions = []

        # for child in self.root.children:
        #     if child.text.lower() in self.QUESTION_WORDS:
        #         if self.qword == '':
        #             self.qword = child.text.lower()
        #         continue
        #
        #     dependency = child.dep_
        #     if dependency in self.SUBJECTS:
        #         self.subjects.append(child)
        #     elif dependency in self.OBJECTS:
        #         self.objects.append(child)
        #     elif dependency in self.CONJUNCTIONS:
        #         self.conjunctions.append(child)
        #     elif dependency in self.AUXILIARIES:
        #         self.auxiliaries.append(child)
        #     elif dependency in self.PREPOSITIONS:
        #         self.prepositions.append(child)
        #
        # if self.conjunctions:
        #     for complement in self.conjunctions:
        #         for child in complement.children:
        #             if child.text.lower() in self.QUESTION_WORDS:
        #                 if self.qword == '':
        #                     self.qword = child.text.lower()
        #                 continue
        #
        #             dependency = child.dep_
        #             if dependency in self.SUBJECTS:
        #                 self.subjects.append(child)
        #             elif dependency in self.OBJECTS:
        #                 self.objects.append(child)
        #             elif dependency in self.CONJUNCTIONS:
        #                 self.objects.append(child)
        #             elif dependency in self.AUXILIARIES:
        #                 self.auxiliaries.append(child)
        #             elif dependency in self.PREPOSITIONS:
        #                 self.prepositions.append(child)

        pool = Queue()
        for child in self.root.children:
            pool.put(child)

        while not pool.empty():
            head = pool.get()

            if head.text.lower() in self.QUESTION_WORDS:
                if self.qword == '':
                    self.qword = head.text.lower()
                continue

            dependency = head.dep_
            if dependency in self.SUBJECTS:
                self.subjects.append(head)
            elif dependency in self.OBJECTS:
                self.objects.append(head)
            elif dependency in self.AUXILIARIES:
                self.auxiliaries.append(head)
            elif dependency in self.PREPOSITIONS:
                self.prepositions.append(head)

            if dependency in self.CONJUNCTIONS:
                for child in head.children:
                    pool.put(child)

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
                self._wants_dep = self.AUXILIARIES + self.PREPOSITIONS + self.PREP_MODIFIERS
            elif self.qword == 'how':
                self._wants_dep = self.AUXILIARIES + self.NOUN_MODIFIERS + self.VERB_MODIFIERS + \
                                  self.PREPOSITIONS + self.PREP_MODIFIERS

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
                if 'do' in self._aux_lemmas and 'be' not in self._aux_lemmas:       # 'do' case
                    self._wants_pos = self.POS_NOUN + self.POS_VERB
                elif 'be' in self._aux_lemmas and 'do' not in self._aux_lemmas:     # 'be'/general case
                    self._wants_pos = self.POS_NOUN + self.POS_ADJ
                else:                                                               # both cases
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
                # TODO: consider switching this to just objects? test it out!
                for head in self.subjects + self.objects:
                    for branch in head.subtree:
                        arg_synset = best_synset(branch.text, branch.pos_)
                        if arg_synset:
                            root_synset = root_hypernyms(arg_synset)
                            if root_synset:
                                arg_synsets.extend(root_synset)
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
                self._wants_wordnet = [wn.synset('entity.n.01')]
            elif self.qword == 'why':
                pass
            elif self.qword == 'how':
                pass

            else:
                self._wants_wordnet = []

        return self._wants_wordnet

    # todo: also consider auxiliaries, modifiers, etc.
    # todo: move over useful/relevant code from produce_answer_phrase
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

        score = 0
        args = []
        auxiliaries = []
        prepositions = []

        has_child_dep = False
        has_child_wn = False
        q_dependency_types = [sub.dep_ for sub in self.root.subtree]
        s_dependency_types = []
        for child in root.subtree:
            dependency = child.dep_
            s_dependency_types.append(dependency)
            if dependency in self.SUBJECTS or dependency in self.OBJECTS:
                args.append(child)
            elif dependency in self.AUXILIARIES:
                auxiliaries.append(child)
            elif dependency in self.PREPOSITIONS:
                prepositions.append(child)

            if child.dep_ in self.wants_dep:
                has_child_dep = True
            if self.wants_wordnet:
                hypernyms = root_hypernyms(best_synset(child.text, child.pos_))
                if hypernyms:
                    for synset_want in self.wants_wordnet:
                        if synset_want in hypernyms:
                            has_child_wn = True
                            break
        # answer type score
        score += len([b for b in (has_child_dep, has_child_wn) if b])

        # dependency overlap score
        if q_dependency_types and s_dependency_types:
            dep_overlap = 0
            for dep in q_dependency_types:
                if dep in s_dependency_types:
                    s_dependency_types.remove(dep)
                    dep_overlap += 1
            score += dep_overlap / len(q_dependency_types)

        s_arg_head, q_arg_head = max(
            [(s_arg, my_arg) for s_arg in args for my_arg in self.subjects + self.objects],
            key=lambda pair: sentence_similarity(
                to_sentence(pair[0]),
                to_sentence(pair[1])
            )
        )
        # max arg similarity score
        score += synset_sequence_similarity(
            [x for x in [best_synset(t) for t in s_arg_head.subtree] if x],
            [x for x in [best_synset(t) for t in q_arg_head.subtree] if x]
        )

        # overall similarity score
        question_synsets = [x for x in [best_synset(word) for word in self.doc] if x]
        sentence_synsets = [x for x in [best_synset(word) for word in root.subtree] if x]
        score += synset_sequence_similarity(question_synsets, sentence_synsets)

        # verb similarity score
        score += synset_sequence_similarity(
            [best_synset(self.root)],
            [best_synset(root)]
        )

        return score

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

        matches = {}        # key: number of matches (i.e. 0 to 3), value: list of matching heads ('children')
        for child in root.subtree:
            if child.i > root.i:    # only want tokens to the right of the verb
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

    def produce_answer_phrase_2(self, sentence):
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

        matches = {}        # key: number of matches (i.e. 0 to 5), value: list of matching heads
        
        pool = Queue()
        for child in root.children:
            pool.put(child)
        
        while not pool.empty():
            head = pool.get()

            # todo: this
            # left_score = 0
            # best_left_head = None
            # for l in head.sent[head.left_edge.i:head.i]:
            #     score = self.score_left(l)
            #     if score > left_score:
            #         left_score = score
            #         best_left_head = l

            root_score = self.score_root(head)

            right_score = 0
            best_right_head = None
            for token in head.sent[head.i+1:head.right_edge.i+1]:
                score = self.score_right(token)
                if score > right_score:
                    right_score = score
                    best_right_head = token

            score = root_score + right_score
            if score:
                if score in matches:
                    matches[score] += [best_right_head]
                else:
                    matches[score] = [best_right_head]

            # if head.i > root.i:  # only want tokens to the right of the verb
            #     score = 0
            #     if head.dep_ in self.wants_dep:
            #         score += 1
            #     if head.pos_ in self.wants_pos:
            #         score += 1
            #     if self.wants_wordnet:
            #         hypernyms = root_hypernyms(best_synset(head.text, head.pos_))
            #         if hypernyms:
            #             for synset_want in self.wants_wordnet:
            #                 if synset_want in hypernyms:
            #                     score += 1
            #                     break
            #     if score in matches.keys():
            #         matches[score] += [head]
            #     else:
            #         matches[score] = [head]

        for score in sorted(matches.keys(), reverse=True):
            match_list = [match for match in matches[score] if match]
            if len(match_list) == 1:
                return to_sentence(match_list[0])
            elif len(match_list) > 1:
                # TODO: something more sophisticated here...?
                return to_sentence(max(
                    [match for match in match_list if match],
                    key=lambda x: len(list(x.subtree))
                ))
                # if best:
                #     return best
                # else:
                #     return self.produce_answer_phrase(sentence)

    # todo: this
    def score_left(self, head):
        assert isinstance(head, Token)

    def score_root(self, root):
        assert isinstance(root, Token)

        tag = to_wordnet_tag(root.pos_)
        if tag == 'v':
            synset = best_synset(root.text, tag)
            if synset and self.root_synset:
                similarity = synset.path_similarity(self.root_synset)
                if similarity:
                    return synset.path_similarity(self.root_synset) * 2

        return root.similarity(self.root)

    def score_right(self, head):
        assert isinstance(head, Token)

        score = 0
        if head.dep_ in self.wants_dep:
            score += 1
        if head.pos_ in self.wants_pos:
            score += 1
        if self.wants_wordnet:
            hypernyms = root_hypernyms(best_synset(head.text, head.pos_))
            if hypernyms:
                for synset_want in self.wants_wordnet:
                    if synset_want in hypernyms:
                        score += 1
                        break
        return score

    # def find_why(self, sentence):
    #     root = None
    #     if isinstance(sentence, str):
    #         root = list(get_spacy_dep_parse(sentence).sents)[0].root
    #     elif isinstance(sentence, Doc):
    #         root = list(sentence.sents)[0].root
    #     elif isinstance(sentence, Span):
    #         root = sentence.root
    #     elif isinstance(sentence, Token):
    #         root = sentence
    #     assert isinstance(root, Token)
    #
    #     candidate_heads = []
    #     for head in root.subtree:
    #         if head.text.lower() in ['because', 'to', 'for', 'so']:
    #             candidate_heads.append(head)
    #
    #     if candidate_heads:
    #         return to_sentence(max(
    #             candidate_heads,
    #             key=lambda x: len(list(x.subtree))
    #         ))

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
    if isinstance(word_str, Token):
        word_str, pos_tag = word_str.text.lower(), word_str.pos_
    assert isinstance(word_str, str)
    assert isinstance(pos_tag, str)

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


def synset_sequence_similarity(synsets_1, synsets_2):
    score, count = 0, 0

    for synset_1 in synsets_1:
        matches = [
            x for x in [
                (synset_2.path_similarity(synset_1), synset_2) for synset_2 in synsets_2
            ] if x[0] is not None
        ]
        if matches:
            best_match = max(matches, key=lambda pair: pair[0])
            if best_match:
                score += best_match[0]
                count += 1
                synsets_2.remove(best_match[1])

    if count:
        return score / count
    else:
        return 0


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
    
    # test = LSAnalyzer('What is Haider accused of being?')
    # response = test.produce_answer_phrase('Haider is accused of being a Nazi sympathizer.')
    # print(response)
    #
    # test = LSAnalyzer('On what was Shoemaker considered an authority?')
    # response = test.produce_answer_phrase(
    #     'He was considered an authority on craters and the collisions that cause them.')
    # print(response)
    #
    # test = LSAnalyzer('What usually causes mudslides?')
    # response = test.produce_answer_phrase(
    #     'They are usually caused by weakened land on hills and mountains.')
    # print(response)
    #
    # test = LSAnalyzer('What can mudslides do when they start moving quickly?')
    # response = test.produce_answer_phrase(
    #     'Mudslides can move quickly and powerfully, picking up rocks, trees, houses and cars.')
    # print(response)
    #
    # test = LSAnalyzer("What is Canada's copyright law largely based on?")
    # response = test.produce_answer_phrase_2(
    #     "Canada's copyright act came into effect in 1924, and is based largely on the law in the United Kingdom.")
    # print(response)
    #
    # test = LSAnalyzer("What happens to cells in one half of the brain as a result of Rasmussen's disease?")
    # response = test.produce_answer_phrase_2(
    #     "It is not known what causes the disease, "
    #     "but it is known that cells in one half of the brain become inflamed, or puffy when infected.")
    # print(response)

    test = LSAnalyzer("Why can't the woman be identified by name?")
    # response = test.find_why(
    #     "The Chinese woman can't be identified because of a legal order, "
    #     "but it seems her claim to be accepted as a refugee to Canada may succeed "
    #     "where the claims of 32 people who arrived with her have failed."
    # )
    a = test.sentence_match("this sentence is garbage")
    b = test.sentence_match("the woman identified as female")
    print(max([a, b]))
