from nltk.tag import StanfordNERTagger
from nltk.parse.corenlp import CoreNLPParser
import nltk
import re
import question_classifier
import os

_wnl = None

_sner = None


# Lemmatizes either a string-word, a string-sentence, or a word-tokenized sentence.
def lemmatize(text, pos: str = 'v'):
    if type(text) is not list:
        text_list = nltk.word_tokenize(text)

    if len(text_list) > 1:
        wnl_sentence = [_wnl.lemmatize(word, pos) for word in text_list]
        return wnl_sentence

    else:
        return _wnl.lemmatize(text, pos)


# Converts a tagged sentence into a string.
def restring(sentence):
    restring = []
    for word in sentence:
        restring.append(word[0])

    return ' '.join(restring)


# Reduces recursive tree structures in ne_chunked sentences
def flatten(tagged_sentence):
    final_form = []
    for sub_form in tagged_sentence:
        if type(sub_form) is nltk.tree.Tree:
            final_form.extend(flatten(sub_form))
        else:
            final_form.append(sub_form)

    return final_form


# Just like flatten, but removes determiners, existential there, conjuctions, punctuations, and 'to'
def squash(tagged_sentence):
    final_form = []
    squash_class = ['EX', 'DT', 'CC']
    for sub_form in tagged_sentence:
        if type(sub_form) is nltk.tree.Tree:
            final_form.extend(squash(sub_form))
        else:
            if len(sub_form[1]) < 2:
                continue
            if sub_form[1] not in squash_class:
                final_form.append((sub_form[0].lower(), sub_form[1]))
    return final_form


def squash_with_ne(tagged_sentence):
    final_form = []
    squash_class = ['EX', 'DT', 'CC']
    for sub_form in tagged_sentence:
        if type(sub_form) is nltk.tree.Tree:
            for sub_sub_form in sub_form:
                final_form.append((sub_sub_form[0].lower(), sub_form._label))
        else:
            if len(sub_form[1]) < 2:
                continue
            if sub_form[1] not in squash_class:
                final_form.append((sub_form[0].lower(), sub_form[1]))
    return final_form


# Function assumes we have only a tagged sentence, similar to squashed or flattened sentences.
# Used to convert a sentence's 3-letter, specialized pos tags, into 2-letter, generalized tags.
def normalize_forms(tagged_sentence):
    final_form = []
    squash_class = ['EX', 'DT', 'CC']
    for sub_form in tagged_sentence:
        if len(sub_form[1]) == 2:
            final_form.append(sub_form)
        elif len(sub_form[1]) > 2:
            final_form.append((sub_form[0], sub_form[1][:2]))
    return final_form


def get_words_with_tag_x(tagged_sentence, tag):
    x_words = []
    for word in tagged_sentence:
        if word[1] is tag:
            x_words.append(word)

    return x_words


def get_contiguous_x_phrases(tagged_sentence, tag):
    x_phrases = []
    x_words = []
    for word in tagged_sentence:
        if word[1] == tag:
            x_words.append(word)
        elif len(x_words) > 0:
            x_phrases.append(restring(x_words))
            x_words.clear()
    if len(x_words) > 0:
        x_phrases.append(restring(x_words))
        x_words.clear()

    return x_phrases


def get_prep_phrases(tagged_sentence):
    prep_tags = ['GP', 'NN', 'OR', 'JJ']
    x_phrases = []
    x_words = []
    for word in tagged_sentence:
        if len(x_words) == 0:
            if word[1] == 'IN':
                x_words.append(word)
        elif word[1] in prep_tags:
            x_words.append(word)
        else:
            if len(x_words) > 1:
                x_phrases.append(restring(x_words))
            x_words.clear()
    if len(x_words) > 1:
        x_phrases.append(restring(x_words))
        x_words.clear()

    return x_phrases


def get_to_phrases(tagged_sentence):
    x_phrases = []
    x_words = []
    for word in tagged_sentence:
        if len(x_words) == 0:
            if word[1] == 'TO':
                x_words.append(word)
        elif word[1] == 'VB':
            x_words.append(word)
        else:
            if len(x_words) > 1:
                x_phrases.append(restring(x_words))
            x_words.clear()
    if len(x_words) > 1:
        x_phrases.append(restring(x_words))
        x_words.clear()

    return x_phrases


def get_feedback(text, nes, sigwords):
    model = '../stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
    jar = '../stanford-ner/stanford-ner.jar'
    st = StanfordNERTagger(model, jar, encoding='utf-8')
    pass


def get_prospects_with_q_analysis(text, q_inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []


def get_prospects_simple(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    for sentence in sentences:
        count = 0
        for word in sentence:
            if word in sigwords:
                count += 1
        if count > 0:
            in_list.append((-count, sentence))

    return sorted(in_list)


def get_prospects_with_stemmer(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    if type(inquiry) is not list:
        sigwords = nltk.word_tokenize(inquiry)
    else:
        sigwords = inquiry

    ps = nltk.stem.PorterStemmer()

    for sentence in sentences:
        count = 0
        tk_sentence = nltk.word_tokenize(sentence)
        ps_sentence = [ps.stem(word) for word in tk_sentence]
        for word in sigwords:
            if ps.stem(word) in ps_sentence:
                count += sentence.count(word)

        if count > 0:
            in_list.append((-count / len(sentence), sentence))

    return sorted(in_list)


def get_prospects_with_lemmatizer(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    for sentence in sentences:
        count = 0
        lm_sentence = lemmatize(sentence)
        for word in sigwords:
            if lemmatize(word) in lm_sentence:
                count += sentence.count(word)

        if count > 0:
            in_list.append((-count, sentence))

    return sorted(in_list)


def get_prospects_with_lemmatizer2(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(inquiry)), binary=True)))
    ps_sentences = []

    for sentence in sentences:
        count = 0
        in_word = []
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        for word in ps_sentence:
            if word in sigwords:
                count += 1
                in_word.append(word)
        ps_sentences.append((ps_sentence, in_word))  # For debugging purposes

        if count > 0:
            in_list.append((-count, sentence))
        #     print('sentence: ' + str(ps_sentence))
        #     print('\twords: ' + str(in_word))

        # if 'root' in question_form:
        #     sigwords.append(lemmatize(restring(question_form['root'])))
        #
        #
        # if 'nsubj' in question_form:
        #     sent = [word for word in lemmatize(restring(question_form['nsubj']))]
        #     for word in sent:
        #         if word not in _stopWords:
        #             sigwords.extend(sent)
        #
        # if 'dobj' in question_form:
        #     sent = [word for word in lemmatize(restring(question_form['dobj']))]
        #     for word in sent:
        #         if word not in _stopWords:
        #             sigwords.extend(sent)
        #
        # if 'iobj' in question_form:
        #     sent = [word for word in lemmatize(restring(question_form['iobj']))]
        #     for word in sent:
        #         if word not in _stopWords:
        #             sigwords.extend(sent)

    return sorted(in_list)


def get_prospects_with_lemmatizer_all(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(inquiry)), binary=True)))
    ps_sentences = []

    for sentence in sentences:
        count = 0
        in_word = []
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        for word in ps_sentence:
            if word in sigwords:
                count += 1
                in_word.append(word)
        ps_sentences.append((ps_sentence, in_word))  # For debugging purposes
        in_list.append((-count, sentence))

    return sorted(in_list)


def get_prospects_with_phrase_matching(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(inquiry)), binary=True)))

    nn_phrases = get_contiguous_x_phrases(sigwords, 'NN')
    vb_phrases = get_contiguous_x_phrases(sigwords, 'VB')

    for sentence in sentences:
        count = 0
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        local_nn_phrases = get_contiguous_x_phrases(ps_sentence, 'NN')
        for phrase in local_nn_phrases:
            if phrase in nn_phrases:
                count += 1
        local_vb_phrases = get_contiguous_x_phrases(ps_sentence, 'VB')
        for phrase in local_vb_phrases:
            if phrase in vb_phrases:
                count += 1

        if count > 0:
            in_list.append((-count, sentence))

    return sorted(in_list)


def get_prospects_for_how_with_pos_check(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    cd_check_list = []

    for sentence in sentences:
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        cd_phrases = get_contiguous_x_phrases(ps_sentence, 'CD')
        if len(cd_phrases) > 0:
            cd_check_list.append(sentence)
            continue

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(inquiry)), binary=True)))

    nn_phrases = get_contiguous_x_phrases(sigwords, 'NN')
    vb_phrases = get_contiguous_x_phrases(sigwords, 'VB')

    for sentence in cd_check_list:
        count = 0
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        local_nn_phrases = get_contiguous_x_phrases(ps_sentence, 'NN')
        for phrase in local_nn_phrases:
            if phrase in nn_phrases:
                count += 1
        local_vb_phrases = get_contiguous_x_phrases(ps_sentence, 'VB')
        for phrase in local_vb_phrases:
            if phrase in vb_phrases:
                count += 1

        in_list.append((-count, sentence))

    return sorted(in_list)


def get_prospects_for_why(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    why_check_list = []

    for sentence in sentences:
        l_sentence = sentence.lower()
        occupations = re.search(r'because', l_sentence)
        if occupations is not None:
            why_check_list.append(sentence)

    if len(why_check_list) == 0:
        for sentence in sentences:
            ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
            to_phrases = get_to_phrases(ps_sentence)
            if len(to_phrases) > 0:
                why_check_list.append(sentence)


    sub_story = ' '.join(why_check_list)
    return get_prospects_with_lemmatizer_all(sub_story, inquiry)


def get_prospects_for_where_ner(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    loc_check_list = []

    for sentence in sentences:
        ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
        loc_phrases = []
        loc_phrases.append(get_contiguous_x_phrases(ps_sentence, 'GP'))
        loc_phrases.append(get_prep_phrases(ps_sentence))
        if len(loc_phrases) > 0:
            loc_check_list.append(sentence)

    sub_story = ' '.join(loc_check_list)
    return get_prospects_with_lemmatizer_all(sub_story, inquiry)


def get_prospects_for_who_ner(text, inquiry):
    occupation_pattern = r'(?:teacher|fighter|leader|father|minister|lawyer|officer|mother|member|chef|politician|' \
                         r'salesperson|cashier|person|worker|janitor|engineer|accountant|manager|woman|man|boy|girl|' \
                         r'driver|captain|marshall|doctor|nurse|chairman)'

    sentences = nltk.sent_tokenize(text)

    ne_check_list = []

    for sentence in sentences:
        ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
        ne_phrases = []
        ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'NE'))
        ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'PE'))
        ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'OR'))
        if len(ne_phrases) > 0:
            ne_check_list.append(sentence)

        l_sentence = sentence.lower()
        occupations = re.search(occupation_pattern, l_sentence)
        if occupations is not None:
            if sentence not in ne_check_list:
                ne_check_list.append(sentence)

    sub_story = ' '.join(ne_check_list)
    return get_prospects_with_lemmatizer_all(sub_story, inquiry)


def get_prospects_for_when_ner(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    cd_check_list = []

    for sentence in sentences:
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        cd_phrases = get_contiguous_x_phrases(ps_sentence, 'CD')
        if len(cd_phrases) > 0:
            cd_check_list.append(sentence)
            continue

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(inquiry)), binary=True)))

    nn_phrases = get_contiguous_x_phrases(sigwords, 'NN')
    vb_phrases = get_contiguous_x_phrases(sigwords, 'VB')

    for sentence in cd_check_list:
        count = 0
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        local_nn_phrases = get_contiguous_x_phrases(ps_sentence, 'NN')
        for phrase in local_nn_phrases:
            if phrase in nn_phrases:
                count += 1
        local_vb_phrases = get_contiguous_x_phrases(ps_sentence, 'VB')
        for phrase in local_vb_phrases:
            if phrase in vb_phrases:
                count += 1

        ner_sentence = _sner.tag(nltk.word_tokenize(sentence))
        for word in ner_sentence:
            if word[1] == 'TIME' or word[1] == 'DATE':
                count *= 2
                break

        in_list.append((-count, sentence))

    return sorted(in_list)


# Most promising for when.
def get_prospects_for_when_regex(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    s_inquiry = inquiry.lower().split()

    if 'last' in s_inquiry:
        last_pattern = r'(?:first|last|since|ago)'

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            lasts = re.search(last_pattern, l_sentence)
            if lasts is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_lemmatizer_all(sub_text, inquiry)

    elif 'start' in s_inquiry or 'begin' in s_inquiry:
        start_pattern = r'(?:start|begin|since|year)'

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            starts = re.search(start_pattern, l_sentence)
            if starts is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_lemmatizer_all(text, inquiry)

    else:
        dates_pattern = r'[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[0-9]{4}|january|february|march|april|may|' \
                        r'june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|' \
                        r'jul|aug|sep|sept|oct|nov|dec|[0-2]?[0-9]'
        time_pattern = r"\s*(\d{1,2}\:\d{2}\s?(?:AM|PM|am|pm)?)|\d{1,2}\s*(?:o'clock)"
        span_pattern = r'(?:last|next|this)?\s*(?:week|month|yesterday|today|tomorrow|year)'

        in_list = []

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            dates = re.search(dates_pattern, l_sentence)
            times = re.search(time_pattern, l_sentence)
            spans = re.search(span_pattern, l_sentence)
            if dates is not None or times is not None or spans is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_lemmatizer_all(sub_text, inquiry)


def get_prospects_for_how_regex(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    s_inquiry = inquiry.lower().split()

    if 'much' in s_inquiry:
        much_pattern = r'\$\s*\d+[,]?\d+[.]?\d*'
        much_pattern2 = r'\d+[,]?\d*\s(?:dollars|cents|crowns|pounds|euros|pesos|yen|yuan|usd|eur|gbp|cad|aud)'
        much_pattern3 = r'(?:dollar|cent|penny|pennies|euro|peso)[s]?'

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            monies = re.search(much_pattern, l_sentence)
            monies2 = re.search(much_pattern2, l_sentence)
            monies3 = re.search(much_pattern3, l_sentence)
            if monies is not None or monies2 is not None or monies3 is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_for_how_with_pos_check(sub_text, inquiry)

    elif 'long' in s_inquiry:
        long_time_pattern = r'\d*\s*(?:minute[s]?|second[s]?|year[s]?|century|centuries|decade[s]?|day[s]?|hour[s]?|lifetime[s]?)'
        long_size_pattern = r'(?:meter[s]?|metre[s]?|kilometer[s]?|kilometre[s]?|mile[s]?feet|inche?s?|centimeter[s]?|centimetre[s]?|yard[s]?|light-year[s]?)'

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            lengths = re.search(long_time_pattern, l_sentence)
            lengths2 = re.search(long_size_pattern, l_sentence)
            if lengths is not None or lengths2 is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_lemmatizer_all(sub_text, inquiry)
    else:
        return get_prospects_for_how_with_pos_check(text, inquiry)


# Do not use. Not fully converted.
def get_prospects_for_how_regex_q(text, q_inquiry):
    much_pattern = r'\$\s*\d+[,]?\d+[.]?\d*'
    much_pattern2 = r'\d+[,]?\d*\s(?:dollars|cents|crowns|pounds|euros|pesos|yen|yuan|usd|eur|gbp|cad|aud)'
    much_pattern3 = r'(?:dollar|cent|penny|pennies|euro|peso)[s]?'
    if 'much' not in restring(q_inquiry.get_pairs):
        return get_prospects_for_how_with_pos_check(text, q_inquiry)
    else:
        sentences = nltk.sent_tokenize(text)

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            monies = re.search(much_pattern, l_sentence)
            monies2 = re.search(much_pattern2, l_sentence)
            monies3 = re.search(much_pattern3, l_sentence)
            if monies is not None or monies2 is not None or monies3 is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_stemmer(sub_text, q_inquiry)


# def get_prospects_with_word2vec(text, sigwords):
#     sentences = nltk.sent_tokenize(text)
#
#     in_list = []
#     expand_list = []
#
#     w2v = Word2Vec([nltk.word_tokenize(sent) for sent in sentences])
#     wnl = nltk.stem.WordNetLemmatizer()
#
#     for sword in sigwords:
#         try:
#             add_word = w2v.most_similar(wnl.lemmatize(sword, 'v'), topn=3)
#             for word in add_word:
#                 expand_list.append((wnl.lemmatize(word[0], 'v'), word[1]))
#         except:
#             pass
#     sigwords = [(wnl.lemmatize(word, 'v'), 1.0) for word in sigwords]
#
#     sigwords.extend(expand_list)
#
#     for sentence in sentences:
#         similarity = 0
#         count = 0
#         tk_sentence = lemmatize(sentence)
#         for word in sigwords:
#             if word[0] in tk_sentence:
#                 similarity += word[1]
#                 count += 1
#
#         if count > 0:
#             in_list.append((-similarity/len(sentence), sentence))
#
#     return sorted(in_list)

def get_prospects_for_where_sner(text, sigwords):
    sentences = get_prospects_with_stemmer(text, sigwords)

    model = os.getcwd() + '/stanford-ner/classifiers/english.muc.7class.distsim.crf.ser.gz'
    jar = os.getcwd() + '/stanford-ner/stanford-ner.jar'
    st = StanfordNERTagger(model, jar, encoding='utf-8')

    in_list = []

    for sentence in sentences:
        ner_sentence = st.tag(nltk.word_tokenize(sentence[1]))
        for word in ner_sentence:
            if word[1] == 'LOCATION':
                in_list.append(sentence)
                break

    return sorted(in_list)


def get_prospects_for_who(text, sigwords):
    sentences = get_prospects_with_lemmatizer2(text, sigwords)

    model = os.getcwd() + '/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
    jar = os.getcwd() + '/stanford-ner/stanford-ner.jar'
    st = StanfordNERTagger(model, jar, encoding='utf-8')

    in_list = []

    for sentence in sentences:
        pos = nltk.pos_tag(nltk.word_tokenize(sentence[1]))

        ner_sentence = st.tag(nltk.word_tokenize(sentence[1]))
        for word in ner_sentence:
            if word[1] == 'PERSON' or word[1] == 'ORGANIZATION':
                in_list.append(sentence)
                break

    return sorted(in_list)


def main():
    pass


if __name__ == "__main__":
    main()

if _wnl == None:
    _wnl = nltk.stem.WordNetLemmatizer()

# if _sner == None:
#     model = os.getcwd() + '/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
#     jar = os.getcwd() + '/stanford-ner/stanford-ner.jar'
#     _sner = StanfordNERTagger(model, jar, encoding='utf-8')
