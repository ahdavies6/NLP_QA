from question_classifier import *
from nltk.corpus import stopwords
import nltk
import text_analyzer
import re
import string


def num_occurrences_time_regex(tokens):
    dates_pattern = r'[[0-9]{1,2}/]*[0-9]{1,2}/[0-9]{2,4}|[0-9]{4}|january|february|march|april|may|june|july|' \
                    r'august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|' \
                    r'sept|oct|nov|dec|[0-2]?[0-9]'
    time_pattern = r"\s*(\d{1,2}\:\d{2}\s?(?:AM|PM|am|pm)?)|\d{1,2}\s*(?:o'clock)"
    span_pattern = r'(?:last|next|this)?\s*(?:week|month|yesterday|today|tomorrow|year)'

    if isinstance(tokens, list):
        tokens = " ".join(tokens)
    tokens = tokens.lower()

    return len(re.findall(dates_pattern, tokens)) + len(re.findall(time_pattern, tokens)) + len(re.findall(span_pattern, tokens))


def num_occurrences_quant_regex(tokens):
    much_pattern = r'\$\s*\d+[,]?\d+[.]?\d*'
    much_pattern2 = r'\d+[,]?\d*\s(?:dollars|cents|crowns|pounds|euros|pesos|yen|yuan|usd|eur|gbp|cad|aud)'
    much_pattern3 = r'(?:dollar|cent|penny|pennies|euro|peso)[s]?'

    if isinstance(tokens, list):
        tokens = " ".join(tokens)
    tokens = tokens.lower()

    return len(re.findall(much_pattern, tokens)) + len(re.findall(much_pattern2, tokens)) + len(re.findall(much_pattern3, tokens))


def get_parse_tree(sentence_text):
    return next(CoreNLPParser().raw_parse(sentence_text))


def get_parse_trees_with_tag(sentence_text, tag):
    parse_tree = next(CoreNLPParser().raw_parse(sentence_text))
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


def get_top_ner_chunk_of_each_tag(sentence,
                                  accepted_tags=("PERSON", "GPE", "ORGANIZATION")):
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
                top_chunks[tag] = [(tag, top_question_chunk)]
    return top_chunks


def to_sentence(tokens, index=0):
    if isinstance(tokens, str):
        return tokens
    elif isinstance(tokens, list):
        if isinstance(tokens[index], tuple):
            return " ".join([
                token[index] for token in tokens
            ])
        else:
            return " ".join(tokens)


def remove_punctuation(s):
    return ''.join(c for c in s if c not in set(string.punctuation))


def get_answer_phrase(question_sentence, answer_sentence):
    """
    Extract the narrowest phrase from the answer sentence containing the full answer to the question sentence
    :param question_sentence: an answer sentence
    :param answer_sentence: a question sentence
    :return: the narrowest phrase containing the full answer
    """
    try:
        question_sentence = remove_punctuation(question_sentence)
        answer_sentence = remove_punctuation(answer_sentence)

        question = formulate_question(question_sentence)
        answer = get_sentence(answer_sentence)

        if question['qword'][0].lower() == "when":
            # get prepositional phrases
            prep_nodes = [d for d in answer.get_nodes if d['tag'] == "prep"]
            if prep_nodes:
                top_prep_string = " ".join([x[0] for x in prep_nodes[0].get_pairs])
                if num_occurrences_time_regex(top_prep_string) > 0:
                    return top_prep_string

            prep_phrases = [x.leaves() for x in get_parse_trees_with_tag(answer_sentence, "PP")]
            if prep_phrases:
                return to_sentence(
                    max(
                        prep_phrases, key=lambda x: num_occurrences_time_regex(x)
                    )
                )
            else:
                if prep_phrases:
                    return to_sentence(max(prep_phrases, key=lambda x: len(x)))

        elif question['qword'][0].lower() == "where":
            answer_chunks = get_top_ner_chunk_of_each_tag(answer_sentence, {"GPE"})

            untagged = [
                tagged[0][1] for tagged in [
                    answer_chunks[tag] for tag in answer_chunks
                ]
            ]

            prep_phrases = [tree.leaves() for tree in get_parse_trees_with_tag(answer_sentence, "PP")]

            if prep_phrases:
                return to_sentence(max(
                    prep_phrases,
                    key=lambda x: calculate_overlap(x, untagged, False)
                ))

        elif question['qword'][0].lower() in ["who", "whose", "whom"]:
            answer_chunks = get_top_ner_chunk_of_each_tag(answer_sentence)

            untagged = [
                tagged[0][1] for tagged in [
                    answer_chunks[tag] for tag in answer_chunks
                ]
            ]
            if untagged:
                return to_sentence(max(untagged, key=lambda x: len(x)))

        elif question['qword'][0].lower() == "why":
            parse_tree = next(CoreNLPParser().raw_parse(answer_sentence))
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

            for i, word in enumerate(answer_sentence.split()):
                if word in ["to", "so", "because"]:
                    return to_sentence(answer_sentence.split()[:i])

        elif question['qword'][0].lower() == "how":
            if any([
                get_parse_trees_with_tag(question_sentence, "WHADJP"),
                re.search(r"much|many|tall|long", question_sentence)
            ]):
                qp_phrases = get_parse_trees_with_tag(answer_sentence, "QP")
                if qp_phrases:
                    return to_sentence(min(
                        [tree.leaves() for tree in qp_phrases],
                        key=lambda x: num_occurrences_quant_regex(x)
                    ))

    except:
        pass
