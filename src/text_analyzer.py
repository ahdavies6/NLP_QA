from nltk.corpus import wordnet
import nltk
import re
import spacy
import en_core_web_lg

_wnl = None

model = None


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


def get_prep_phrases(tokenized_sentence):
    grammar = r"""
    PP: {<IN><DT>?<JJ>*<NN>+}
    {<IN><DT>?<JJ>*<NNP>+}"""
    # prep_tags = ['GP', 'NN', 'OR', 'JJ']
    x_phrases = []
    x_words = []
    prepParser = nltk.RegexpParser(grammar)
    sent = prepParser.parse(tokenized_sentence)
    for sub_form in sent:
        if type(sub_form) == nltk.tree.Tree:
            x_phrases.append(restring(sub_form))

    return x_phrases


def getGrammarPhrases(tagged_sentence, grammar):
    x_phrases = []
    parser = nltk.RegexpParser(grammar)
    for sub_form in parser.parse(tagged_sentence):
        if type(sub_form) == nltk.tree.Tree:
            x_phrases.append(restring(sub_form))

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


def word_similarity(word1, word2):
    result = model(' '.join([word1, word2]))
    word1, word2 = result[0], result[1]
    return word1.similarity(word2)


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


def get_prospects_with_wordnet(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    in_list = [(-sentence_similarity(sentence, inquiry), sentence) for sentence in sentences]

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


def get_prospects_for_who_ner(text, inquiry):
    occupation_pattern = r'(?:teacher|fighter|leader|father|minister|lawyer|officer|mother|member|chef|politician|' \
                         r'salesperson|cashier|person|worker|janitor|engineer|accountant|manager|woman|man|boy|girl|' \
                         r'driver|captain|marshall|doctor|nurse|chairman)'

    whoIsName = r"""
        XX: {<WP><VBZ|VBD><JJ>*<NNP>+<.>}
        """
    name_phrase_grammar = r"""
        XX: {<NNP>+<,><DT>?<JJ>*<NN>+}
        {<,>?<NN|NNP>+<IN><DT>?<NN|NNP>+}
        {<NN|NNP>+<NNP>+}
        """
    sentences = nltk.sent_tokenize(text)

    ne_check_list = []

    tagged_inquiry = nltk.pos_tag(nltk.word_tokenize(inquiry))

    who_is_name = getGrammarPhrases(tagged_inquiry, whoIsName)

    if len(who_is_name) > 0:
        name = getGrammarPhrases(tagged_inquiry, r"XX: {<NNP>+}")[0]
        name = nltk.word_tokenize(name)
        for sub_name in name:
            for sentence in sentences:
                if sub_name in sentence:
                    tagged_sentence = nltk.pos_tag(nltk.word_tokenize(sentence))
                    name_phrase = getGrammarPhrases(tagged_sentence, name_phrase_grammar)
                    if len(name_phrase) > 0:
                        ne_check_list.append(sentence)
    else:
        who_is_title = getGrammarPhrases(tagged_inquiry, r"XX: {<WP><VBZ|VBD><DT><JJ>*<NN|NNP>+<JJ>*}")

        if len(who_is_title) > 0:
            title = getGrammarPhrases(tagged_inquiry, r"XX: {<NN|NNP>+}")
            for sub_title in title:
                for sentence in sentences:
                    if sub_title in sentence:
                        ne_check_list.append(sentence)

        else:
            for sentence in sentences:
                # ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
                # ne_phrases = []
                # ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'NE'))
                # ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'PE'))
                # ne_phrases.extend(get_contiguous_x_phrases(ps_sentence, 'OR'))
                # if len(ne_phrases) > 0:
                #     ne_check_list.append(sentence)
                ps_sentence = model(sentence)
                for word in ps_sentence.ents:
                    if word.label_ == 'PERSON' or word.label_ == 'ORG':
                        ne_check_list.append(sentence)
                        break

                l_sentence = sentence.lower()
                occupations = re.search(occupation_pattern, l_sentence)
                if occupations is not None:
                    if sentence not in ne_check_list:
                        ne_check_list.append(sentence)

    sub_story = ' '.join(ne_check_list)
    return get_prospects_with_wordnet(sub_story, inquiry)


def get_dependency(doc, dep):
    return [token for token in doc if token.dep_ == dep]


def get_prospects_for_who_sp_ner(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    ne_check_list = []
    #
    # inquiry_ents = model(inquiry).ents
    #
    # if len(inquiry_ents) > 0:
    #     for ent in inquiry_ents:
    #         for sentence in sentences:
    #             sentence_ents = model(sentence).ents
    #             print(sentence_ents, end=' ')
    #             print(ent)
    #             if ent in sentence_ents:
    #                 ne_check_list.append(sentence)
    #
    #     final_check_list = []
    #
    #     for sentence in loc_check_list:
    #         ps_sentence = model(sentence)
    #         for word in ps_sentence.ents:
    #             if word.label_ in ['GPE', 'LOC', 'ORG']:
    #                 final_check_list.append(sentence)
    #                 break
    #
    #     sub_story = ' '.join(final_check_list)
    #     return get_prospects_with_lemmatizer_all(sub_story, inquiry)
    # else:
    for sentence in sentences:
        ps_sentence = model(sentence)
        for word in ps_sentence.ents:
            if word.label_ == 'PERSON' or word.label_ == 'ORG':
                ne_check_list.append(sentence)
                break

    # root = get_dependency(model(inquiry), 'ROOT')[0]
    # root = lemmatize(root.text)[0]
    #
    # root_check_list = []

    # for sentence in ne_check_list:
    #     ps_sentence = lemmatize(sentence)
    #     if root in ps_sentence:
    #         root_check_list.append(sentence)
    #     else:
    #         score = sentence_similarity(root, sentence)
    #         print(score)
    #         if score >= 0.5:
    #             root_check_list.append(sentence)

    sub_story = ' '.join(ne_check_list)
    return get_prospects_with_wordnet(sub_story, inquiry)


def get_prospects_for_how_regex(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    s_inquiry = inquiry.lower().split()

    if 'much' in s_inquiry:
        regex_check_list = []

        for sentence in sentences:
            for ent in model(sentence).ents:
                if ent.label_ in ['MONEY', 'QUANTITY']:
                    regex_check_list.append(sentence)

        sub_text = ' '.join(regex_check_list)
        return get_prospects_with_wordnet(sub_text, inquiry)

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

    return sorted(in_list)


def get_prospects_for_where_ner(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    loc_check_list = []

    for sentence in sentences:
        ps_sentence = normalize_forms(squash_with_ne(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=False)))
        loc_phrases = []
        loc_phrases.append(get_contiguous_x_phrases(ps_sentence, 'GP'))
        loc_phrases.append(get_prep_phrases(nltk.pos_tag(nltk.word_tokenize(sentence))))
        if len(loc_phrases) > 0:
            loc_check_list.append(sentence)

    sub_story = ' '.join(loc_check_list)
    return get_prospects_with_lemmatizer_all(sub_story, inquiry)


def get_prospects_for_where_sp_ner(text, inquiry):
    sentences = nltk.sent_tokenize(text)

    loc_check_list = []

    inquiry_ents = model(inquiry).ents

    if len(inquiry_ents) > 0:
        for ent in inquiry_ents:
            for sentence in sentences:
                sentence_ents = model(sentence).ents
                if ent in sentence_ents:
                    loc_check_list.append(sentence)

        final_check_list = []

        for sentence in loc_check_list:
            ps_sentence = model(sentence)
            for word in ps_sentence.ents:
                if word.label_ in ['GPE', 'LOC']:
                    final_check_list.append(sentence)
                    break

        sub_story = ' '.join(final_check_list)
        return get_prospects_with_wordnet(sub_story, inquiry)
    else:
        for sentence in sentences:
            ps_sentence = model(sentence)
            for word in ps_sentence.ents:
                if word.label_ in ['GPE', 'LOC']:
                    loc_check_list.append(sentence)
                    break
        sub_story = ' '.join(loc_check_list)
        return get_prospects_with_wordnet(sub_story, inquiry)


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


if _wnl is None:
    _wnl = nltk.stem.WordNetLemmatizer()


if model is None:
    model = en_core_web_lg.load()
