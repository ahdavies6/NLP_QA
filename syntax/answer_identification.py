from parse import get_sentence
from question_classifier import *
from nltk.corpus import stopwords
import nltk
import text_analyzer
import re


"""
dep
    aux
    arg (argument)
        comp (complement)
            obj
        subj
    mod (modifier)
"""

# todo: squash_with_ne
# squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)

# for size in [decreasing size of constituents as you go more precise]
# for


def num_occurrences_time(chunk):
    dates_pattern = r'[[0-9]{1,2}/]*[0-9]{1,2}/[0-9]{2,4}|[0-9]{4}|january|february|march|april|may|june|july|' \
                    r'august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|' \
                    r'sept|oct|nov|dec|[0-2]?[0-9]'
    time_pattern = r"\s*(\d{1,2}\:\d{2}\s?(?:AM|PM|am|pm)?)|\d{1,2}\s*(?:o'clock)"
    span_pattern = r'(?:last|next|this)?\s*(?:week|month|yesterday|today|tomorrow|year)'
    begin_pattern = r"first|last|since|ago"
    end_pattern = r"start|begin|since|year"

    if isinstance(chunk, list):
        chunk = " ".join(chunk)
    chunk = chunk.lower()

    return len(re.findall(dates_pattern, chunk)) + \
           len(re.findall(time_pattern, chunk)) + \
           len(re.findall(span_pattern, chunk))

    # return any([
    #     re.search(dates_pattern, chunk),
    #     re.search(time_pattern, chunk),
    #     re.search(span_pattern, chunk),
    # ])


# def get_contiguous_x_in_y_phrases(tagged_sentence, list_tags):
#     y_phrases = []
#     y_words = []
#     for tag in list_tags:
#         this_tag = []
#         # y_words += [(tag, [])]
#         for word in tagged_sentence:
#             if word[1] == tag:
#                 this_tag.append(word)
#             elif len(this_tag) > 0:
#                 x_phrases.append(text_analyzer.restring(this_tag))
#                 this_tag.clear()
#     if len(x_words) > 0:
#         x_phrases.append(text_analyzer.restring(x_words))
#         x_words.clear()
#
#     return x_phrases


def get_parse_trees_with_tag(sentence, tag):
    parse_tree = next(CoreNLPParser().raw_parse(sentence))
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


def calculate_overlap(sequence1, sequence2):
    overlap = 0
    for word in sequence1:
        if word in sequence2 and word not in stopwords.words('english'):
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


# todo: put a huge try/catch(all) block to just return the sentence
def get_answer_phrase(question_sentence, answer_sentence):
    """
    Extract the narrowest phrase from the answer sentence containing the full answer to the question sentence
    :param question_sentence: an answer sentence
    :param answer_sentence: a question sentence
    :return: the narrowest phrase containing the full answer
    """
    question = formulate_question(question_sentence)
    answer = get_sentence(answer_sentence)

    # # # highly rudimentary form:
    # # targets = text_analyzer.squash_with_ne(
    # #     nltk.ne_chunk(nltk.pos_tag(
    # #         text_analyzer.lemmatize(question_sentence)),
    # #         binary=False
    # #     )
    # # )
    # # sentence = text_analyzer.squash_with_ne(
    # #     nltk.ne_chunk(nltk.pos_tag(
    # #         text_analyzer.lemmatize(answer_sentence)),
    # #         binary=False
    # #     )
    # # )
    # targets = nltk.word_tokenize(question_sentence.lower())
    # sentence = nltk.word_tokenize(answer_sentence.lower())
    # overlap = overlap_indices(targets, sentence)

    if question['qword'][0].lower() == "what":
        pass

    elif question['qword'][0].lower() == "when":
        # get prepositional phrases
        prep_nodes = [d for d in answer.get_nodes if d['tag'] == "prep"]
        if prep_nodes:
            # todo: should this be the uppermost node (which'll be [0], always)?
            top_prep_string = " ".join([x[0] for x in prep_nodes[0].get_pairs])
            if num_occurrences_time(top_prep_string) > 0:
                return top_prep_string

        prep_phrases = [x.leaves() for x in get_parse_trees_with_tag(answer_sentence, "PP")]

        if prep_phrases:
            return to_sentence(
                max(
                    prep_phrases, key=lambda x: num_occurrences_time(x)
                )
            )
        else:
            # todo: perhaps reconsider which one to return here. this may be the wrong idea.
            if prep_phrases:
                return max(prep_phrases, key=lambda x: len(x))

    elif question['qword'][0].lower() == "where":
        answer_chunks = get_top_ner_chunk_of_each_tag(answer_sentence, {"GPE"})

        untagged = [
            tagged[0][1] for tagged in [
                answer_chunks[tag] for tag in answer_chunks
            ]
        ]

        # prep_phrases = get_phrases_with_tag(answer_sentence, "PP")
        # if answer['prep']:
            # get_dep_trees_with_tag()

        pass

    elif question['qword'][0].lower() == "which":
        pass

    elif question['qword'][0].lower() == "who":
        question_chunks = get_top_ner_chunk_of_each_tag(question_sentence)
        answer_chunks = get_top_ner_chunk_of_each_tag(answer_sentence)

        # todo: try something with checking the question tag with the answer tag
        # todo: consider stripping out the part of the answer with question entity in it...?

        untagged = [
            tagged[0][1] for tagged in [
                answer_chunks[tag] for tag in answer_chunks
            ]
        ]

        return to_sentence(max(untagged, key=lambda x: len(x)))

    elif question['qword'][0].lower() == "why":
        pass

    elif question['qword'][0].lower() == "how":
        # TODO: look at "QP" parse tag for this!
        pass

    # if nothing else worked, just return the whole sentence...?
    else:
        return answer_sentence


def test_who():
    question_sentence = "Who is the principal of South Queens Junior High School?"
    answer_sentence = "Principal Betty Jean Aucoin says the club is a first for a Nova Scotia public school."
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


if __name__ == "__main__":
    # test_who()
    # test_where()
    test_when()
