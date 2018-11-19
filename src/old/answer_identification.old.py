from src.question_classifier import *
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
    begin_pattern = r"first|last|since|ago"
    end_pattern = r"start|begin|since|year"

    if isinstance(tokens, list):
        tokens = " ".join(tokens)
    tokens = tokens.lower()

    return len(re.findall(dates_pattern, tokens)) + len(re.findall(time_pattern, tokens)) + len(
        re.findall(span_pattern, tokens))


def num_occurrences_quant_regex(tokens):
    much_pattern = r'\$\s*\d+[,]?\d+[.]?\d*'
    much_pattern2 = r'\d+[,]?\d*\s(?:dollars|cents|crowns|pounds|euros|pesos|yen|yuan|usd|eur|gbp|cad|aud)'
    much_pattern3 = r'(?:dollar|cent|penny|pennies|euro|peso)[s]?'

    if isinstance(tokens, list):
        tokens = " ".join(tokens)
    tokens = tokens.lower()

    return len(re.findall(much_pattern, tokens)) + len(re.findall(much_pattern2, tokens)) + len(
        re.findall(much_pattern3, tokens))


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


# todo: look through all of Carlos' stuff and make sure I'm implementing anything useful that he has
# todo: consider adding a "bad" tag in last-resort-y responses... or just don't return... idk
# todo: re-capitalize text when returning?
def get_answer_phrase(question_sentence, answer_sentence):
    """
    Extract the narrowest phrase from the answer sentence containing the full answer to the question sentence
    :param question_sentence: an answer sentence
    :param answer_sentence: a question sentence
    :return: the narrowest phrase containing the full answer
    """
    # TODO: UNCOMMENT TRY/CATCH BLOCK!
    try:
        question_sentence = remove_punctuation(question_sentence)
        answer_sentence = remove_punctuation(answer_sentence)

        question = formulate_question(question_sentence)
        answer = get_sentence(answer_sentence)

        # todo!!!!
        if question['qword'][0].lower() in ["what", "which"]:
            best_phrase = None
            for subtree in [
                tree.subtrees() for tree in
                get_parse_trees_with_tag(answer_sentence, "NP") +
                get_parse_trees_with_tag(answer_sentence, "NX")
            ]:
                for tree in subtree:
                    baseline = text_analyzer.sentence_similarity(question_sentence, " ".join(tree.leaves()))

            baseline = text_analyzer.sentence_similarity(question_sentence)

        elif question['qword'][0].lower() == "when":
            # get prepositional phrases
            prep_nodes = [d for d in answer.get_nodes if d['tag'] == "prep"]
            if prep_nodes:
                # todo: should this be the uppermost node (which'll be [0], always)?
                top_prep_string = " ".join([x[0] for x in prep_nodes[0].get_pairs])
                if num_occurrences_time_regex(top_prep_string) > 0:
                    return top_prep_string

            # todo: find a way to use my dependency parse here?
            prep_phrases = [x.leaves() for x in get_parse_trees_with_tag(answer_sentence, "PP")]

            if prep_phrases:
                return to_sentence(
                    max(
                        prep_phrases, key=lambda x: num_occurrences_time_regex(x)
                    )
                )
            else:
                # todo: perhaps reconsider which one to return here. sentence length may be the wrong idea.
                if prep_phrases:
                    return to_sentence(max(prep_phrases, key=lambda x: len(x)))

        elif question['qword'][0].lower() == "where":
            answer_chunks = get_top_ner_chunk_of_each_tag(answer_sentence, {"GPE"})

            untagged = [
                tagged[0][1] for tagged in [
                    answer_chunks[tag] for tag in answer_chunks
                ]
            ]

            # get_dep_trees_with_tag(answer, "prep")
            prep_phrases = [tree.leaves() for tree in get_parse_trees_with_tag(answer_sentence, "PP")]

            # todo: strip preposition (e.g. "in") out of the answer
            if prep_phrases:
                return to_sentence(max(
                    prep_phrases,
                    key=lambda x: calculate_overlap(x, untagged, False)
                ))

        elif question['qword'][0].lower() in ["who", "whose", "whom"]:
            question_chunks = get_top_ner_chunk_of_each_tag(question_sentence)
            answer_chunks = get_top_ner_chunk_of_each_tag(answer_sentence)

            # todo: try something with checking the question tag with the answer tag
            # todo: consider stripping out the part of the answer with question entity in it...?

            untagged = [
                tagged[0][1] for tagged in [
                    answer_chunks[tag] for tag in answer_chunks
                ]
            ]

            # todo: figure out what to do if not untagged
            if untagged:
                return to_sentence(max(untagged, key=lambda x: len(x)))

        elif question['qword'][0].lower() == "why":
            # q_verb = question.tuple
            # a_verb = answer.tuple

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
            # todo: potentially strip out "to", and might consider including object?
            # todo: honestly, might just pick out things after "to"
            # if to_vp_phrases:
            #     return to_sentence(min(
            #         [tree.leaves() for tree in to_vp_phrases],
            #         key=lambda x: calculate_overlap(to_vp_phrases, x)
            #     ))

            # todo: finish debugging
            # vp_phrases = get_parse_trees_with_tag(answer_sentence, "VP")
            # to_phrases = []
            # if to_phrases:
            #     return to_sentence(max(
            #         to_phrases,
            #         key=lambda x: len([])
            #     ))

            # todo: soup up this absolute trash
            for i, word in enumerate(answer_sentence.split()):
                if word in ["to", "so", "because"]:
                    return to_sentence(answer_sentence.split()[:i])

            # todo: try things with conjunctions, potentially? test.
            # conj_phrases = [tree.leaves() for tree in get_parse_trees_with_tag(answer_sentence, "PP")]

        elif question['qword'][0].lower() == "how":
            # TODO: look at "QP" parse tag for this!
            if any([
                # 'advmod' in [
                #     pair[1] for pair in [
                #         node.get_pairs[1] for node in question.get_nodes if node['tag'][0].lower() == 'w'
                #     ]
                # ],
                get_parse_trees_with_tag(question_sentence, "WHADJP"),
                re.search(r"much|many|tall|long", question_sentence)
            ]):
                qp_phrases = get_parse_trees_with_tag(answer_sentence, "QP")
                if qp_phrases:
                    return to_sentence(min(
                        [tree.leaves() for tree in qp_phrases],
                        key=lambda x: num_occurrences_quant_regex(x)
                    ))

            # todo: non-measure cases! (mostly thinking about "how did/does")

    except:
        pass


def test_who1():
    question_sentence = "Who is the principal of South Queens Junior High School?"
    answer_sentence = "Principal Betty Jean Aucoin says the club is a first for a Nova Scotia public school."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_who2():
    question_sentence = "Who said \"the effects were top notch\" when he was talking about \"The Phantom Menace\"?"
    answer_sentence = "Mark Churchill and Ken Green were at the St. John's screening."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_where():
    question_sentence = "Where is South Queens Junior High School located?"
    answer_sentence = "A middle school in Liverpool, Nova Scotia is pumping up bodies as well as minds."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_when():
    question_sentence = "When did Babe play for \"the finest basketball team that ever stepped out on a floor\"?"
    answer_sentence = "Babe Belanger played with the Grads from 1929 to 1937."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_why_to():
    question_sentence = "Why did someone sleep in a tent on a sidewalk in front of a theater in Montreal?"
    answer_sentence = "In Montreal someone actually slept in a tent out on the sidewalk in front of a movie " \
                      "theatre to make sure he got the first ticket."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_why_other():
    question_sentence = "Why will diabetics have to be patient, despite Dr. Ji-Won Yoon's discovery?"
    answer_sentence = "But, diabetics will have to be patient -- a cure for humans is between five and 10 years away."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_how_does():
    question_sentence = "How does Newfoundland intend to use a film of seals feasting on cod?"
    answer_sentence = "The Newfoundland government has a new weapon in its fight to increase the seal hunt: film of cod carnage."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_how_much():
    question_sentence = "How much was sealing worth to the Newfoundland economy in 1996?"
    answer_sentence = "In 1996 alone it was worth in excess of $11 million, with seal products being sold in Canada, Norway and Asia."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def test_what1():
    question_sentence = "What has South Queens Junior High School done with its old metal shop?"
    answer_sentence = "The school has turned its one-time metal shop - lost to budget cuts almost two years ago - into a money-making professional fitness club."
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


def template():
    question_sentence = 0
    answer_sentence = 0
    test = get_answer_phrase(question_sentence, answer_sentence)
    print(test)


if __name__ == "__main__":
    # test_who1()
    # test_who2()
    # test_where()
    # test_when()
    # test_why_to()
    # test_why_other()
    # test_how_does()
    # test_how_much()
    test_what1()
