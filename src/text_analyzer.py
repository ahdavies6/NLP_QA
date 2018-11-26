from nltk.corpus import wordnet
import nltk
from parse import get_constituency_parse
import re

_wnl = None


def overlap(word_list_one, word_list_two):
    if not word_list_two or not word_list_two:
        return 0
    word_list_one = set(word_list_one)
    word_list_two = set(word_list_two)
    # max_len = len(word_list_one) if len(word_list_one) > len(word_list_two) else len(word_list_two)
    min_len = len(word_list_one) if len(word_list_one) < len(word_list_two) else len(word_list_two)
    if min_len == 0:
        return 0
    else:
        count = 0
        for word in word_list_one:
            if word in word_list_two:
                count += 1
        return count/min_len


# Lemmatizes either a string-word, a string-sentence, or a word-tokenized sentence.
def lemmatize(text, pos: str = 'v'):
    if type(text) is not list:
        text = nltk.word_tokenize(text)

    return [_wnl.lemmatize(word, pos) for word in text]


# Converts a tagged sentence into a string.
def restring(sentence):
    result = []
    for word in sentence:
        result.append(word[0])

    return ' '.join(result)


# Reduces recursive tree structures in ne_chunked sentences
def flatten(tagged_sentence):
    final_form = []
    for sub_form in tagged_sentence:
        if type(sub_form) is nltk.tree.Tree:
            final_form.extend(flatten(sub_form))
        else:
            final_form.append(sub_form)

    return final_form


# Just like flatten, but removes determiners, existential there, conjunctions, punctuations, and 'to'
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


def get_grammar_phrases(tagged_sentence, grammar):
    x_phrases = []
    parser = nltk.RegexpParser(grammar)
    for sub_form in parser.parse(tagged_sentence):
        if type(sub_form) == nltk.tree.Tree:
            x_phrases.append(restring(sub_form))

    return x_phrases


def get_words_with_tag_x(tagged_sentence, tag):
    x_words = []
    for word in tagged_sentence:
        if word[1] == tag:
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


# Convert between a Penn Treebank tag to a simplified Wordnet tag
def get_wordnet_tag(tag):
    if tag.startswith('N'):
        return 'n'
    if tag.startswith('V'):
        return 'v'
    if tag.startswith('J'):
        return 'a'
    if tag.startswith('R'):
        return 'r'

    return None


# Takes a wordnet pos tagged word, and converts to synset
def get_synset(word, tag):
    wn_tag = get_wordnet_tag(tag)
    if wn_tag is None:
        return None
    try:
        return wordnet.synsets(word, wn_tag)[0]
    except:
        return None


def sentence_similarity(sentence1, sentence2):
    sentence1 = nltk.pos_tag(nltk.word_tokenize(sentence1))
    sentence2 = nltk.pos_tag(nltk.word_tokenize(sentence2))

    synsets1 = [get_synset(*tagged_word) for tagged_word in sentence1]
    synsets2 = [get_synset(*tagged_word) for tagged_word in sentence2]

    synsets1 = [ss for ss in synsets1 if ss]
    synsets2 = [ss for ss in synsets2 if ss]

    score, count = 0.0, 0

    for synset_one in synsets1:
        score_list = [synset_one.path_similarity(ss) for ss in synsets2]
        verify_scores = [0]
        for s in score_list:
            if type(s) is float:
                verify_scores.append(s)

        best_score = max(verify_scores)

        if best_score is not None:
            score += best_score
            count += 1
    if count != 0:
        score /= count
    else:
        score = 0
    return score


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

    return in_list


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

    return in_list


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

    return in_list


def get_prospects_with_lemmatizer2(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(inquiry)), binary=True)))
    sigwords = restring(sigwords).split()
    ps_sentences = []

    for sentence in sentences:
        count = 0
        in_word = []
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        ps_sentence = restring(ps_sentence).split()
        for word in ps_sentence:
            if word in sigwords:
                count += 1
                in_word.append(word)
        ps_sentences.append((ps_sentence, in_word))  # For debugging purposes

        if count > 0:
            in_list.append((-count, sentence))

    return in_list


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

    return in_list


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

    return in_list


def get_prospects_with_wordnet(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = [(-sentence_similarity(sentence, inquiry), sentence) for sentence in sentences]

    return in_list


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

    return in_list


def get_prospects_for_who_ner(text, inquiry):
    occupation_pattern = r'(?:teacher|fighter|leader|father|minister|lawyer|officer|mother|member|chef|politician|' \
                         r'salesperson|cashier|person|worker|janitor|engineer|accountant|manager|woman|man|boy|girl|' \
                         r'driver|captain|marshall|doctor|nurse|chairman)'

    who_is_pattern = r'[Ww]ho\sis\s([A-Z][a-z]+\s?[[A-Za-z]+]?)'
    who_is_title = r'[Ww]ho is the ((\w|\s)+) of'
    who_is_title2 = r'[Ww]ho is the ((.)+)'

    sentences = nltk.sent_tokenize(text)
    in_list = []

    person = re.search(who_is_pattern, inquiry)

    if person:

        person = person.group(1)
        person_pattern = r'(?:{0}, |, {0}|[A-Z][\w]+\s{0})'.format(person)
        for sentence in sentences:
            sentence_match = re.search(person_pattern, sentence)
            if sentence_match:
                in_list.append(sentence)
        sub_text = ' '.join(in_list)
        return get_prospects_with_wordnet(sub_text, inquiry)

    title = re.search(who_is_title2, inquiry)

    if title:
        title = title.group(1)
        ps_title = get_grammar_phrases(nltk.pos_tag(nltk.word_tokenize(title)), "XX: {<NN|NNS|NNP|NNPS|DT>+}")
        if len(ps_title) > 0:
            title = ps_title[0]
            for sentence in sentences:
                score = overlap(nltk.word_tokenize(title), nltk.word_tokenize(sentence))
                if score >= 0.5:
                    in_list.append((-score, sentence))
            return in_list

    # Experimental.
######################################################################################################
    # s_inquiry = lemmatize(inquiry)
    # if 'be' in s_inquiry:
    #     parse_tree = get_constituency_parse(inquiry)
    #     results = []
    #     for tree in parse_tree.subtrees():
    #         if tree.label() == "NP":
    #             results.append(tree)
    #     if results:
    #         in_list = []
    #
    #         best_phrase = max(results, key=lambda x: len(list(x.subtrees())))
    #         best_phrase = [w.lower() for w in (lemmatize(' '.join(flatten(best_phrase))))]
    #         for sentence in sentences:
    #             tagged_sentence = [w.lower() for w in (lemmatize(sentence))]
    #             score = overlap(best_phrase, tagged_sentence)
    #             if score >= 0.5:
    #                 in_list.append(sentence)
    #
    #         if len(in_list) > 0:
    #             sub_story = ' '.join(in_list)
    #             get_prospects_with_lemmatizer2(sub_story, inquiry)
    #             return in_list

    # parse_tree = get_constituency_parse(inquiry)
    # results = []
    # for tree in parse_tree.subtrees():
    #     if tree.label() == "NP":
    #         results.append(tree)
    # if results:
    #     in_list = []
    #
    #     best_phrase = max(results, key=lambda x: len(list(x.subtrees())))
    #     best_phrase = [w.lower() for w in (lemmatize(' '.join(flatten(best_phrase))))]
    #     for sentence in sentences:
    #         tagged_sentence = [w.lower() for w in (lemmatize(sentence))]
    #         score = overlap(best_phrase, tagged_sentence)
    #         if score == 1.0:
    #             in_list.append(sentence)
    #
    #     # if len(in_list) > 0:
    #     sub_story = ' '.join(in_list)
    #     return get_prospects_with_lemmatizer2(sub_story, inquiry)
    #     # return in_list
##########################################################################################################

    ne_check_list = []

    for sentence in sentences:
        ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
        ne_phrases = []
        # ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'NE'))
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
    return get_prospects_with_wordnet(sub_story, inquiry)


def get_prospects_for_how_regex(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    s_inquiry = inquiry.lower().split()

    if 'long' in s_inquiry or 'time' in s_inquiry:
        long_time_pattern = r'\d*\s(?:minute[s]?|second[s]?|year[s]?|century|centuries|decade[s]?|day[s]?|hour[s]?|lifetime[s]?)'
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

    elif 'much' in s_inquiry:
        much_pattern = r'\$\s*\d+[,]?\d+[.]?\d*'
        much_pattern2 = r'\d+[,]?\d*\s(?:dollars|cents|crowns|pounds|euros|pesos|yen|yuan|usd|eur|gbp|cad|aud)'
        much_pattern3 = r'(?:dollar|cent|penny|pennies|euro|peso)[s]?'

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            monies = re.search(much_pattern, l_sentence)
            monies2 = re.search(much_pattern2, l_sentence)
            monies3 = re.search(much_pattern3, l_sentence)
            if monies or monies2 or monies3:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_lemmatizer2(sub_text, inquiry)

    elif 'many' in s_inquiry:
        cd_check_list = []

        for sentence in sentences:
            ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
            cd_phrases = get_contiguous_x_phrases(ps_sentence, 'CD')
            if len(cd_phrases) > 0:
                cd_check_list.append(sentence)
                continue

        sub_story = ' '.join(cd_check_list)

        return get_prospects_with_lemmatizer_all(sub_story, inquiry)
    elif 'old' in s_inquiry:
        age_pattern = r'\d*\s(?:year[s]?|century|centuries|decade[s]?)'
        age_pattern2 = r'(?:baby|toddler|teen|teenager|twent|thirt|fourt|fift|sixt|sevent|eight|ninet|old)'
        age_grammar = r"""
        XX: {<NNP>+<,>?<CD>+}
        """

        check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            age = re.search(age_pattern, l_sentence)
            age2 = re.search(age_pattern2, l_sentence)
            age3 = get_grammar_phrases(nltk.pos_tag(nltk.word_tokenize(sentence)), age_grammar)
            if age or age2 or len(age3) > 0:
                check_list.append(sentence)

        sub_text = ' '.join(check_list)

        return get_prospects_with_lemmatizer_all(sub_text, inquiry)

    elif 'did' in s_inquiry or 'does' in s_inquiry or 'are' in s_inquiry or 'is' in s_inquiry:
        return get_prospects_with_lemmatizer2(text, inquiry)
    else:
        return get_prospects_with_lemmatizer2(text, inquiry)


def get_prospects_for_what(text, inquiry):
    sentences = nltk.sent_tokenize(text)
    in_list = []
    # ps_inquiry = squash_with_ne(nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(inquiry)), binary=True))
    # ne_words = get_words_with_tag_x(ps_inquiry, 'NE')
    # if len(ne_words) > 0:
    #
    #     ne_words.extend([('he', 'PRP'), ('she', 'PRP')])
    #
    #     for sentence in sentences:
    #         ps_sentence = squash_with_ne(nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sentence)), binary=True))
    #         for word in ne_words:
    #             if word in ps_sentence:
    #                 in_list.append(sentence)
    #
    #     sub_text = ' '.join(in_list)
    #     return get_prospects_with_wordnet(sub_text, inquiry)

    if 'will' in inquiry:
        for sentence in sentences:
            if 'will' in sentence:
                in_list.append(sentence)
        sub_text = ' '.join(in_list)
        return get_prospects_with_lemmatizer2(sub_text, inquiry)

    return get_prospects_with_lemmatizer2(text, inquiry)
    # s_inquiry = lemmatize(inquiry)
    # if 'be' in s_inquiry:
    #     parse_tree = get_constituency_parse(inquiry)
    #     results = []
    #     for tree in parse_tree.subtrees():
    #         if tree.label() == "NP":
    #             results.append(tree)
    #     if results:
    #         in_list = []
    #
    #         best_phrase = max(results, key=lambda x: len(list(x.subtrees())))
    #         best_phrase = nltk.pos_tag(nltk.word_tokenize(' '.join(flatten(best_phrase))))
    #         for sentence in sentences:
    #             tagged_sentence = nltk.pos_tag(nltk.word_tokenize(sentence))
    #             score = overlap(best_phrase, tagged_sentence)
    #             if score > 0:
    #                 in_list.append((-score, sentence))
    #
    #         if len(in_list) > 0:
    #             return in_list

    # s_inquiry = inquiry.lower().split()
    #
    # if 'what' in s_inquiry:
    #     index = s_inquiry.index('what')
    #     if len(s_inquiry) > index+1:
    #         if 'is' == s_inquiry[index+1]:
    #             in_list = []
    #             tagged_inquiry = nltk.pos_tag(nltk.word_tokenize(inquiry))[index:]
    #             g_phrase = get_grammar_phrases(tagged_inquiry, r"XX: {<DT>?<NN|NNP>+}")
    #             if len(g_phrase) > 0:
    #                 g_phrase = g_phrase[0]
    #                 for sentence in sentences:
    #                     ps_sentence = restring(squash(nltk.pos_tag(lemmatize(sentence))))
    #                     if g_phrase in ps_sentence:
    #                         in_list.append(sentence)
    #
    #                 sub_text = ' '.join(in_list)
    #                 return get_prospects_with_lemmatizer_all(sub_text, inquiry)


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

        return get_prospects_with_lemmatizer_all(sub_text, inquiry)

    else:
        dates_pattern = r'[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[0-9]{4}|january|february|march|april|may|' \
                        r'june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|' \
                        r'jul|aug|sep|sept|oct|nov|dec|[0-2]?[0-9]'
        time_pattern = r"\s*(\d{1,2}\:\d{2}\s?(?:AM|PM|am|pm)?)|\d{1,2}\s*(?:o'clock)"
        span_pattern = r'(?:last|next|this)?\s*(?:week|month|yesterday|today|tomorrow|year)'

        regex_check_list = []

        for sentence in sentences:
            l_sentence = sentence.lower()
            dates = re.search(dates_pattern, l_sentence)
            times = re.search(time_pattern, l_sentence)
            spans = re.search(span_pattern, l_sentence)
            if dates is not None or times is not None or spans is not None:
                regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)

        return get_prospects_with_wordnet(sub_text, inquiry)


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

        in_list.append((-count, sentence))

    return in_list


def get_prospects_for_where_ner(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    loc_check_list = []

    prep_grammar = r"""
        XX: {<IN><DT>?<JJ>*<NN|NNP>+}
        {<IN><GP|NN|OR|JJ>+}
    """

    for sentence in sentences:
        ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
        loc_phrases = []
        loc_phrases.append(get_contiguous_x_phrases(ps_sentence, 'GP'))
        loc_phrases.append(get_grammar_phrases(ps_sentence, prep_grammar))
        if len(loc_phrases) > 0:
            loc_check_list.append(sentence)

    sub_story = ' '.join(loc_check_list)
    return get_prospects_with_lemmatizer_all(sub_story, inquiry)


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


def main():
    pass


if __name__ == "__main__":
    main()


if _wnl is None:
    _wnl = nltk.stem.WordNetLemmatizer()
