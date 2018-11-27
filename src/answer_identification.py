import nltk
import text_analyzer
import re
import string
from nltk.corpus import stopwords
from spacy.tokens import Doc, Span, Token
from text_analyzer import lemmatize
from parse import get_constituency_parse, get_dependency_parse, get_spacy_dep_parse
from question_classifier import formulate_question
from wordnet_experiments import get_lexname, LSAnalyzer


def num_occurrences_time_regex(tokens):
    dates_pattern = r'[[0-9]{1,2}/]*[0-9]{1,2}/[0-9]{2,4}|[0-9]{4}|january|february|march|april|may|june|july|' \
                    r'august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|' \
                    r'sept|oct|nov|dec|[0-2]?[0-9]'
    time_pattern = r"\s*(\d{1,2}\:\d{2}\s?(?:AM|PM|am|pm)?)|\d{1,2}\s*(?:o'clock)"
    span_pattern = r'(?:last|next|this)?\s*(?:week|month|yesterday|today|tomorrow|year)'

    if isinstance(tokens, list):
        tokens = " ".join(tokens)
    tokens = tokens.lower()

    return sum([
        len(group) for group in [
            re.findall(p, tokens) for p in (dates_pattern, time_pattern, span_pattern)
        ]
    ])


def num_occurrences_quant_regex(tokens):
    much_pattern = r'\$\s*\d+[,]?\d+[.]?\d*'
    much_pattern2 = r'\d+[,]?\d*\s(?:dollars|cents|crowns|pounds|euros|pesos|yen|yuan|usd|eur|gbp|cad|aud)'
    much_pattern3 = r'(?:dollar|cent|penny|pennies|euro|peso)[s]?'

    if isinstance(tokens, list):
        tokens = " ".join(tokens)
    tokens = tokens.lower()

    return sum([
        len(group) for group in [
            re.findall(p, tokens) for p in (much_pattern, much_pattern2, much_pattern3)
        ]
    ])


def get_parse_trees_with_tag(sentence, tag):
    if isinstance(sentence, str):
        sentence = get_constituency_parse(sentence)
    assert isinstance(sentence, nltk.Tree)

    # phrases = []
    # for subtree in sentence.subtrees():
    #     if subtree.label() == tag:
    #         phrases.append(subtree)
    # return phrases

    return [x for x in sentence.subtrees() if x.label() == tag]


def get_dep_trees_with_tag(root_node, tag):
    tagged = []
    for node in root_node.get_nodes:
        if node['tag'].lower() == tag.lower():
            tagged.append(node)
    return tagged


def calculate_overlap(sequence1, sequence2, eliminate_stopwords=True):
    overlap = 0
    for word in sequence1:
        if word in sequence2 and (word not in stopwords.words('english') or eliminate_stopwords):
            overlap += 1
    return overlap


def overlap_indices(target_words, sentence):
    indices = []
    for i, word in enumerate(sentence):
        if word in target_words and word not in stopwords.words('english'):
            indices.append(i)
    return indices


def get_top_ner_chunk_of_each_tag(
        sentence,
        accepted_tags=("PERSON", "GPE", "ORGANIZATION")
):
    named_question_chunks = text_analyzer.squash_with_ne(
        nltk.ne_chunk(nltk.pos_tag(
            text_analyzer.lemmatize(sentence)),
            binary=False
        )
    )
    top_chunks = {}
    for tag in accepted_tags:
        question_chunks = [
            x.split() for x in text_analyzer.get_contiguous_x_phrases(
                named_question_chunks, tag
            )
        ]
        if question_chunks:
            top_question_chunk = max(question_chunks, key=lambda x: len(x))
            if len(top_question_chunk) > 0:
                top_chunks[tag] = top_question_chunk
    return top_chunks


def to_sentence(tokens, index=0):
    if isinstance(tokens, str):
        return tokens
    elif isinstance(tokens, list):
        if len(tokens) > 1:
            if isinstance(tokens[0], str) or isinstance(tokens[0], tuple):
                if index < len(tokens):
                    if isinstance(tokens[index], tuple):
                        return ' '.join([
                            token[index] for token in tokens
                        ])
                    else:
                        return ' '.join(tokens)
            elif isinstance(tokens, nltk.Tree):
                return [x.join for x in (
                    ' '.join(tokens.leaves())
                )]
    elif isinstance(tokens, Token):
        return ' '.join([token.text for token in tokens.subtree])
    elif isinstance(tokens, nltk.Tree):
        return ' '.join(tokens.leaves())


def remove_punctuation(s):
    return ''.join(c for c in s if c not in set(string.punctuation))


# TODO: test whether the NER type matching actually helps or not
def get_phrase_for_who(raw_question, raw_sentence):
    question_chunks = get_top_ner_chunk_of_each_tag(raw_question, ('PERSON', 'ORGANIZATION'))
    answer_chunks = get_top_ner_chunk_of_each_tag(raw_sentence, ('PERSON', 'ORGANIZATION'))

    # if the question has an NER chunk, try to return the "top NER chunk" of the same type in the answer sentence
    if question_chunks:
        q_tag_type = max(
            [tag for tag in question_chunks],
            key=lambda x: len(x)
        )
        if q_tag_type in answer_chunks:
            return to_sentence(answer_chunks[q_tag_type])

    # the question didn't have an NER chunk, or the answer didn't have one of the same type;
    # either way, just return the longest NER chunk in the answer sentence, if the answer sentence
    # has any NER chunks to begin with
    if answer_chunks:
        return to_sentence(
            max(
                [answer_chunks[tag] for tag in answer_chunks],
                key=lambda x: len(x)
            )
        )


# todo: either delete this or the other get_p_4_who
def get_phrase_for_who2(raw_question, raw_sentence):
    who_is_pattern = r'[Ww]ho\sis\s([A-Z][a-z]+\s?[[A-Za-z]+]?)'
    person = re.search(who_is_pattern, raw_question)
    if person:
        full_name = person.group(1)
        name_pattern1 = r'(?:{0},\s(.+))'.format(full_name)
        name_pattern2 = r'(?:(.+),\s{0})'.format(full_name)
        name_pattern3 = r'((?:[A-Z][A-z\.]+\s)+){0}'.format(full_name)
        name_pattern4 = r'{0}\s((?:[A-Z][A-z\.]+\s)+)'.format(full_name)
        title = re.search(name_pattern1, raw_sentence)
        if title:
            return title.group(1)
        title = re.search(name_pattern2, raw_sentence)
        if title:
            return title.group(1)
        title = re.search(name_pattern3, raw_sentence)
        if title:
            return title.group(1)
        title = re.search(name_pattern4, raw_sentence)
        if title:
            return title.group(1)

    answer_chunks = get_top_ner_chunk_of_each_tag(raw_sentence)

    if answer_chunks:
        return to_sentence(
            max(
                [answer_chunks[tag] for tag in answer_chunks],
                key=lambda x: len(x)
            )
        )


# todo: 'have' (lemma) option as well
def get_phrase_for_what(raw_question, raw_sentence):
    q_root = get_spacy_dep_parse(raw_question)
    aux = lemmatize(
        [to_sentence(token) for token in q_root if token.dep_ in ['aux', 'auxpass']]
    )
    do_result = -1
    be_result = -1
    result = None
    if aux:
        if len(aux) == 1:
            if aux[0] == 'do':
                result = get_phrase_for_what_do(raw_question, raw_sentence)
            elif aux[0] == 'be':
                result = get_phrase_for_what_be(raw_question, raw_sentence)
        else:
            big_aux = max(aux, key=lambda x: len(x))
            if 'do' in big_aux:
                result = get_phrase_for_what_do(raw_question, raw_sentence)
            elif 'be' in big_aux:
                result = get_phrase_for_what_be(raw_question, raw_sentence)

        # if isinstance(do_result, str):
        #     return do_result
        # elif isinstance(be_result, str):
        #     return be_result
        if result:
            return result

    lemmatized = lemmatize(raw_question)
    if 'do' in lemmatized:
        result = get_phrase_for_what_do(raw_question, raw_sentence)
    elif 'be' in lemmatized:
        result = get_phrase_for_what_be(raw_question, raw_sentence)

    if result:
        return result

    return get_phrase_for_what_do(raw_question, raw_sentence)

    # if isinstance(do_result, str):
    #     return do_result
    # elif isinstance(be_result, str):
    #     return be_result
    # elif isinstance(be_result, int) or be_result is None:
    #     return get_phrase_for_what_be(raw_question, raw_sentence)
    # else:
    #     return get_phrase_for_what_do(raw_question, raw_sentence)


def get_phrase_for_what_wn(raw_question, raw_sentence):
    return None
    analyzer = LSAnalyzer(raw_question)
    return analyzer.produce_answer_phrase(raw_sentence)
    # return analyzer.produce_answer_phrase_2(raw_sentence)


# todo: figure out whether to continue rejecting left or not
def get_phrase_for_what_do(raw_question, raw_sentence):
    q_doc = get_spacy_dep_parse(raw_question)
    s_doc = get_spacy_dep_parse(raw_sentence)

    q_verb = [t for t in q_doc if t.dep_ == 'ROOT']
    assert len(q_verb) == 1
    q_verb = q_verb[0]

    s_verb = max(
        [t for t in s_doc if t.pos_ == 'VERB'],
        key=lambda x: x.similarity(q_verb)
    )
    assert isinstance(s_verb, Token)

    # objs = [t for t in s_verb.subtree if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj']]
    # obj_heads = [r for r in s_verb.rights if r.dep_ in ['obj', 'dobj', 'iobj', 'pobj']]
    # stuff = [t for t in [list(r.subtree) for r in s_verb.rights] if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj']]
    rights = []
    for sublist in [list(r.subtree) for r in s_verb.rights]:
        rights += sublist
    r_obj_heads = []
    for head in rights:
        r_obj_heads += [t for t in head.subtree if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj', 'dative']]
    # to_sentence(max([r for r in s_verb.rights], key=lambda x: len(list(x.subtree))))
    if r_obj_heads:
        return to_sentence(max(
            r_obj_heads,
            key=lambda x: len(list(x.subtree))
        ))
        # longest_obj = max(
        #     objs,
        #     key=lambda x: len([y for y in x.subtree])
        # )
        # return to_sentence(longest_obj)

    all_object_heads = [t for t in s_verb.subtree if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj', 'dative']]
    if all_object_heads:
        return to_sentence(max(
            all_object_heads,
            key=lambda x: len(list(x.subtree))
        ))


def get_phrase_for_what_be(raw_question, raw_sentence):
    q_doc = get_spacy_dep_parse(raw_question)
    s_doc = get_spacy_dep_parse(raw_sentence)

    # are both Span objects
    q_noun_chunks = [np for np in q_doc.noun_chunks]
    s_noun_chunks = [np for np in s_doc.noun_chunks]

    pairs = []
    for q_np in q_noun_chunks:
        q_head = q_np.root
        q_ln = get_lexname(q_head.text, q_head.pos_)
        for s_np in s_noun_chunks:
            s_head = s_np.root
            s_ln = get_lexname(s_head.text, s_head.pos_)

            if q_ln == s_ln:
                pairs += [(q_head, s_head)]

    if len(pairs) == 1:
        return to_sentence(pairs[0][1])
    elif len(pairs) > 1:
        s_obj_heads = [pair[1] for pair in pairs if pair[1].dep_ in ['obj', 'dobj', 'iobj', 'pobj', 'dative']]
        if s_obj_heads:
            return to_sentence(max(
                s_obj_heads,
                key=lambda x: len(list(x.subtree))
            ))
        else:
            return to_sentence(max(
                [pair[1] for pair in pairs],
                key=lambda x: len(list(x.subtree))
            ))

    if len(s_noun_chunks) > 0:
        return to_sentence(max(
            [span.root for span in s_noun_chunks],
            key=lambda x: len(list(x.subtree))
        ))

    # todo: show to Carlos; use in extraction?
    # todo: if you wanna use this, look more at OBJECTS!
    # q_root = list(q_doc.sents)[0].root
    # s_root = list(s_doc.sents)[0].root
    #
    # q_entities = deps_which_are_hyponym_of(q_root, wn.synset('entity.n.01'))
    # s_entities = deps_which_are_hyponym_of(s_root, wn.synset('entity.n.01'))
    #
    # if q_entities and s_entities:
    #     best_sim = -1
    #     best_q_entity = None
    #     for q_e in q_entities:
    #         for s_e in s_entities:
    #             sim = sentence_similarity(
    #                 to_sentence(q_e),
    #                 to_sentence(s_e)
    #             )
    #             if sim > best_sim:
    #                 best_sim = sim
    #                 best_q_entity = s_e
    #     if best_q_entity:
    #         return to_sentence(best_q_entity)
    # elif s_entities:
    #     return to_sentence(max(s_entities, key=lambda s: len(to_sentence(s))))


def get_phrase_for_when(raw_question, raw_sentence):
    answer_sentence = get_dependency_parse(raw_sentence)

    # get prepositional phrases
    prep_nodes = [d for d in answer_sentence.get_nodes if d['tag'] == "prep"]
    if prep_nodes:
        top_prep_string = " ".join([x[0] for x in prep_nodes[0].get_pairs])
        if num_occurrences_time_regex(top_prep_string) > 0:
            return top_prep_string

    prep_phrases = [x.leaves() for x in get_parse_trees_with_tag(raw_sentence, "PP")]
    if prep_phrases:
        return to_sentence(
            max(
                prep_phrases, key=lambda x: num_occurrences_time_regex(x)
            )
        )
    else:
        if prep_phrases:
            return to_sentence(max(prep_phrases, key=lambda x: len(x)))


def get_phrase_for_where(raw_question, raw_sentence):
    answer_chunks = get_top_ner_chunk_of_each_tag(raw_sentence, {"GPE"})

    untagged = [
        tagged[0][1] for tagged in [
            answer_chunks[tag] for tag in answer_chunks
        ]
    ]

    # TODO: put this in conditional block for "if untagged isn't empty"; else look @ overlap for... question sentence?
    prep_phrases = [tree.leaves() for tree in get_parse_trees_with_tag(raw_sentence, "PP")]
    if prep_phrases:
        return to_sentence(max(
            prep_phrases,
            key=lambda x: calculate_overlap(x, untagged, False)
        ))


def get_phrase_for_why(raw_question, raw_sentence):
    # parse_tree = next(CoreNLPParser().raw_parse(raw_sentence))
    parse_tree = get_constituency_parse(raw_sentence)
    to_vp_phrases = []
    prev_was_to = False
    for tree in parse_tree.subtrees():
        if tree.label() == "VP":
            for subtree in tree.subtrees():
                if prev_was_to:
                    to_vp_phrases.append(subtree)
                    prev_was_to = False
                elif subtree.label() == "TO":
                    prev_was_to = True

    for i, word in enumerate(nltk.word_tokenize(raw_sentence)):
        if word in ['to', 'so', 'because', 'for']:
            result = to_sentence(raw_sentence.split()[i:])
            if result:
                if 'because' not in result:
                    result = 'because ' + result
                return result


def get_phrase_for_why_2(raw_question, raw_sentence):
    root = None
    if isinstance(raw_sentence, str):
        root = list(get_spacy_dep_parse(raw_sentence).sents)[0].root
    elif isinstance(raw_sentence, Doc):
        root = list(raw_sentence.sents)[0].root
    elif isinstance(raw_sentence, Span):
        root = raw_sentence.root
    elif isinstance(raw_sentence, Token):
        root = raw_sentence
    assert isinstance(root, Token)

    direct_text_matches = []
    prep_deps = []
    prep_mods = []
    conjunctions = []
    for head in root.subtree:
        if head.dep_ in LSAnalyzer.PREPOSITIONS:
            prep_deps.append(head)
        if head.dep_ in LSAnalyzer.PREP_MODIFIERS:
            prep_mods.append(head)
        if head.dep_ in LSAnalyzer.CONJUNCTIONS:
            conjunctions.append(head)
        full_head_text = ''.join([dep.text.lower() for dep in head.subtree])
        if any(
            [x in full_head_text for x in ['because', 'to', 'for', 'so']]
        ):
            direct_text_matches.append(head)

    if direct_text_matches:
        largest_head_text = to_sentence(max(
            direct_text_matches,
            key=lambda x: len(list(x.subtree))
        ))
        if 'because' not in largest_head_text:
            largest_head_text = 'because ' + largest_head_text
        return largest_head_text

    # for group in (prep_deps, prep_mods, conjunctions):
    #     if group:
    #         most_promising = to_sentence(max(
    #             group,
    #             key=lambda x: len(list(x.subtree))
    #         ))
    #         if 'because' not in most_promising:
    #             most_promising = 'because ' + most_promising
    #         return most_promising

    # todo: try using conjunctions as well.
    # preps = [tree for tree in get_constituency_parse(raw_sentence) if tree.label() == 'PP']
    preps = get_parse_trees_with_tag(raw_sentence, 'PP')
    if preps:
        return to_sentence(max(preps, key=lambda x: len(list(x.subtrees()))))

    for i, word in enumerate(nltk.word_tokenize(raw_sentence)):
        if word in ['because', 'to', 'for', 'so']:
            result = to_sentence(raw_sentence.split()[i:])
            if 'because' not in result:
                result = 'because ' + result
            return result


def get_phrase_for_how_adj(raw_question, raw_sentence):
    if any([
        get_parse_trees_with_tag(raw_question, "WHADJP"),
        re.search(r"much|many|tall|long", raw_question)
    ]):
        qp_phrases = get_parse_trees_with_tag(raw_sentence, "QP")
        if qp_phrases:
            return to_sentence(min(
                [tree.leaves() for tree in qp_phrases],
                key=lambda x: num_occurrences_quant_regex(x)
            ))


def get_answer_phrase(raw_question, raw_sentence):
    """
    Extract the narrowest phrase from the answer sentence containing the full answer to the question sentence
    :param raw_question: an answer sentence
    :param raw_sentence: a question sentence
    :return: the narrowest phrase containing the full answer
    """
    question = formulate_question(raw_question)

    get_phrases = {
        # 'who': get_phrase_for_who,
        # 'whose': get_phrase_for_who,
        # 'whom': get_phrase_for_who,
        'who': get_phrase_for_who2,
        'whose': get_phrase_for_who2,
        'whom': get_phrase_for_who2,

        # 'what': get_phrase_for_what,
        # 'what': get_phrase_for_what_do,
        'what': get_phrase_for_what_wn,

        'when': get_phrase_for_when,
        'where': get_phrase_for_where,

        'why': get_phrase_for_why,
        # 'why': get_phrase_for_why_2,

        'how': get_phrase_for_how_adj,
        # TODO: put in 'which'? look for other qwords not included?
    }

    qword = question['qword'][0].lower()
    if qword in get_phrases:
        answer = get_phrases[qword](raw_question, raw_sentence)
        if answer:
            return answer

    # answer = get_dependency_parse(raw_sentence)

    # if question['qword'][0].lower() == "when":
    #     # get prepositional phrases
    #     prep_nodes = [d for d in answer.get_nodes if d['tag'] == "prep"]
    #     if prep_nodes:
    #         top_prep_string = " ".join([x[0] for x in prep_nodes[0].get_pairs])
    #         if num_occurrences_time_regex(top_prep_string) > 0:
    #             return top_prep_string
    #
    #     # todo: look into whether "answer_sentence" here was screwing it all up
    #     prep_phrases = [x.leaves() for x in get_parse_trees_with_tag(raw_sentence, "PP")]
    #     if prep_phrases:
    #         return to_sentence(
    #             max(
    #                 prep_phrases, key=lambda x: num_occurrences_time_regex(x)
    #             )
    #         )
    #     else:
    #         if prep_phrases:
    #             return to_sentence(max(prep_phrases, key=lambda x: len(x)))
    #
    # elif question['qword'][0].lower() == "where":
    #     answer_chunks = get_top_ner_chunk_of_each_tag(raw_sentence, {"GPE"})
    #
    #     untagged = [
    #         tagged[0][1] for tagged in [
    #             answer_chunks[tag] for tag in answer_chunks
    #         ]
    #     ]
    #
    #     prep_phrases = [tree.leaves() for tree in get_parse_trees_with_tag(raw_sentence, "PP")]
    #
    #     if prep_phrases:
    #         return to_sentence(max(
    #             prep_phrases,
    #             key=lambda x: calculate_overlap(x, untagged, False)
    #         ))
    #
    # elif question['qword'][0].lower() in ["who", "whose", "whom"]:
    #     answer_chunks = get_top_ner_chunk_of_each_tag(raw_sentence)
    #
    #     untagged = [
    #         tagged[0][1] for tagged in [
    #             answer_chunks[tag] for tag in answer_chunks
    #         ]
    #     ]
    #     if untagged:
    #         return to_sentence(max(untagged, key=lambda x: len(x)))
    #
    # elif question['qword'][0].lower() == "why":
    #     parse_tree = next(CoreNLPParser().raw_parse(raw_sentence))
    #     to_vp_phrases = []
    #     prev_was_to = False
    #     for tree in parse_tree.subtrees():
    #         if tree.label() == "VP":
    #             for subtree in tree.subtrees():
    #                 if prev_was_to:
    #                     to_vp_phrases.append(subtree)
    #                     prev_was_to = False
    #                 elif subtree.label() == "TO":
    #                     prev_was_to = True
    #
    #     for i, word in enumerate(raw_sentence.split()):
    #         if word in ["to", "so", "because"]:
    #             return to_sentence(raw_sentence.split()[:i])
    #
    # elif question['qword'][0].lower() == "how":
    #     if any([
    #         get_parse_trees_with_tag(raw_question, "WHADJP"),
    #         re.search(r"much|many|tall|long", raw_question)
    #     ]):
    #         qp_phrases = get_parse_trees_with_tag(raw_sentence, "QP")
    #         if qp_phrases:
    #             return to_sentence(min(
    #                 [tree.leaves() for tree in qp_phrases],
    #                 key=lambda x: num_occurrences_quant_regex(x)
    #             ))


if __name__ == '__main__':
    test = get_phrase_for_why_2(
        "Why is a democratic society in Kosovo essential, according to Lloyd Axworthy?",
        "YNN is a private company that gives schools free equipment - like televisions and computers - "
        "to make sure it has an audience for its commercial news service."
    )
    print(test)
