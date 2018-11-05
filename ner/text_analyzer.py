from nltk.tag import StanfordNERTagger
from nltk.parse.corenlp import CoreNLPParser
import nltk
from syntax import parse
import os


_wnl = None


# Lemmatizes either a string-word, a string-sentence, or a word-tokenized sentence.
def lemmatize(text, pos: str='v'):
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
    squash_class = ['EX', 'TO', 'DT', 'CC']
    for sub_form in tagged_sentence:
        if type(sub_form) is nltk.tree.Tree:
            final_form.extend(squash(sub_form))
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
    squash_class = ['EX', 'TO', 'DT', 'CC']
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


def get_feedback(text, nes, sigwords):
    model = '../stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
    jar = '../stanford-ner/stanford-ner.jar'
    st = StanfordNERTagger(model, jar, encoding='utf-8')
    pass


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


def get_prospects_with_stemmer(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    ps = nltk.stem.PorterStemmer()

    for sentence in sentences:
        count = 0
        tk_sentence = nltk.word_tokenize(sentence)
        ps_sentence = [ps.stem(word) for word in tk_sentence]
        for word in sigwords:
            if ps.stem(word) in ps_sentence:
                count += sentence.count(word)

        if count > 0:
            in_list.append((-count/len(sentence), sentence))

    return sorted(in_list)


def get_feedback_with_lemmatizer(text, sigwords):
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

def get_prospects_with_lemmatizer2(text, question_form):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    sigwords = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(question_form)), binary=True)))
    ps_sentences = []

    for sentence in sentences:
        count = 0
        in_word = []
        ps_sentence = normalize_forms(squash(nltk.ne_chunk(nltk.pos_tag(lemmatize(sentence)), binary=True)))
        for word in ps_sentence:
            if word in sigwords:
                count += 1
                in_word.append(word)
        ps_sentences.append((ps_sentence, in_word))         # For debugging purposes

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

def get_prospects_for_where(text, sigwords):
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
    sentences = get_feedback_with_lemmatizer(text, sigwords)

    model = os.getcwd() + '/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
    jar = os.getcwd() + '/stanford-ner/stanford-ner.jar'
    st = StanfordNERTagger(model, jar, encoding='utf-8')

    in_list = []

    for sentence in sentences:
        pos = nltk.pos_tag(nltk.word_tokenize(sentence[1]))


        ner_sentence = st.tag(nltk.word_tokenize(sentence[1]))
        for word in ner_sentence:
            if word[1] == 'PERSON':
                in_list.append(sentence)
                break

    return sorted(in_list)


def main():
    pass


if __name__ == "__main__":
    main()


if _wnl == None:
    _wnl = nltk.stem.WordNetLemmatizer()


