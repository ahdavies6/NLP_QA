import nltk
import text_analyzer
import re
import string
from nltk.corpus import stopwords
from spacy.tokens import Token
from text_analyzer import lemmatize
from parse import get_constituency_parse, get_dependency_parse, get_token_dependent_of_type, \
    get_subtree_dependent_of_type, get_spacy_dep_parse
from question_classifier import formulate_question


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


def get_parse_trees_with_tag(sentence_text, tag):
    parse_tree = get_constituency_parse(sentence_text)
    phrases = []
    for subtree in parse_tree.subtrees():
        if subtree.label() == tag:
            phrases.append(subtree)
    return phrases


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
        if isinstance(tokens[index], tuple):
            return ' '.join([
                token[index] for token in tokens
            ])
        else:
            return ' '.join(tokens)
    elif isinstance(tokens, Token):
        return ' '.join([token.text for token in tokens.subtree])


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
    answer_chunks = get_top_ner_chunk_of_each_tag(raw_sentence)

    if answer_chunks:
        return to_sentence(
            max(
                [answer_chunks[tag] for tag in answer_chunks],
                key=lambda x: len(x)
            )
        )


# todo: figure out whether to continue rejecting left or not
def get_phrase_for_what_do(raw_question, raw_sentence):
    return None
    q_dep = get_spacy_dep_parse(raw_question)
    s_dep = get_spacy_dep_parse(raw_sentence)

    q_verb = [t for t in q_dep if t.dep_ == 'ROOT']
    assert len(q_verb) == 1
    q_verb = q_verb[0]

    s_verb = max(
        [t for t in s_dep if t.pos_ == 'VERB'],
        key=lambda x: x.similarity(q_verb)
    )
    assert isinstance(s_verb, Token)

    # objs = [t for t in s_verb.subtree if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj']]
    # obj_heads = [r for r in s_verb.rights if r.dep_ in ['obj', 'dobj', 'iobj', 'pobj']]
    # stuff = [t for t in [list(r.subtree) for r in s_verb.rights] if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj']]
    stuff = []
    for l in [list(r.subtree) for r in s_verb.rights]:
        stuff += l
    obj_heads = []
    for h in stuff:
        obj_heads += [t for t in h.subtree if t.dep_ in ['obj', 'dobj', 'iobj', 'pobj', 'dative']]
    # to_sentence(max([r for r in s_verb.rights], key=lambda x: len(list(x.subtree))))
    if obj_heads:
        return to_sentence(max(
            obj_heads,
            key=lambda x: len(list(x.subtree))
        ))
        # longest_obj = max(
        #     objs,
        #     key=lambda x: len([y for y in x.subtree])
        # )
        # return to_sentence(longest_obj)
    else:
        pass
    # return raw_sentence


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
        if word in ["to", "so", "because", "for"]:
            result = to_sentence(raw_sentence.split()[i:])
            if 'because' not in result:
                result = 'because ' + result
            return result
            # return "because" + to_sentence(raw_sentence.split()[i:])


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
    raw_question = remove_punctuation(raw_question)
    raw_sentence = remove_punctuation(raw_sentence)

    question = formulate_question(raw_question)

    get_phrases = {
        # 'who': get_phrase_for_who,
        # 'whose': get_phrase_for_who,
        # 'whom': get_phrase_for_who,
        'who': get_phrase_for_who2,
        'whose': get_phrase_for_who2,
        'whom': get_phrase_for_who2,

        'what': get_phrase_for_what_do,
        'when': get_phrase_for_when,
        'where': get_phrase_for_where,
        'why': get_phrase_for_why,
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
