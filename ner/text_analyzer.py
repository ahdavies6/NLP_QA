from nltk.tag import StanfordNERTagger
from nltk.parse.corenlp import CoreNLPParser
from gensim.models import Word2Vec
import nltk
from nltk.corpus import stopwords
from syntax import parse
import os


# Lemmatizes either a string-word, a string-sentence, or a word-tokenized sentence.
def lemmatize(text, pos: str='v'):
    wnl = nltk.stem.WordNetLemmatizer()
    if type(text) is not list:
        text_list = nltk.word_tokenize(text)

    if len(text_list) > 1:
        wnl_sentence = [wnl.lemmatize(word, pos) for word in text_list]

        return wnl_sentence
    else:
        return wnl.lemmatize(text, pos)


def get_feedback(text, nes, sigwords):
    model = '../stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
    jar = '../stanford-ner/stanford-ner.jar'
    st = StanfordNERTagger(model, jar, encoding='utf-8')
    pass


def get_feedback1(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    stopword = set(stopwords.words('english'))

    for sentence in sentences:
        count = 0
        for word in sigwords:
            if word in sentence and word not in stopword:
                count += sentence.count(word)
        if count > 0:
            in_list.append((-count, sentence))

    return in_list


def get_feedback2(text, sigphrases):
    sentences = nltk.sent_tokenize(text)

    print(nltk.sent_tokenize(text))

    in_list = []

    for words in sigphrases:
        pass

    for sentence in sentences:
        count = 0
        for word in sigphrases:
            if word in sentence:
                count += sentence.count(word)
        if count > 0:
            in_list.append((count, sentence))

    return in_list

def get_feedback_with_stemmer(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    stopword = set(stopwords.words('english'))

    ps = nltk.stem.PorterStemmer()

    for sentence in sentences:
        count = 0
        tk_sentence = nltk.word_tokenize(sentence)
        ps_sentence = [ps.stem(word) for word in tk_sentence]
        for word in sigwords:
            if ps.stem(word) in ps_sentence and word not in stopword:
                count += sentence.count(word)

        if count > 0:
            in_list.append((-count/len(sentence), sentence))

    return in_list


def get_feedback_with_lemmatizer(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    stopword = set(stopwords.words('english'))

    for sentence in sentences:
        count = 0
        lm_sentence = lemmatize(sentence)
        for word in sigwords:
            if lemmatize(word) in lm_sentence and word not in stopword:
                count += sentence.count(word)

        if count > 0:
            in_list.append((-count/len(sentence), sentence))

    return in_list

def get_feedback_with_lemmatizer2(text, question_form):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    for sentence in sentences:
        ps_sentence = nltk.ne_chunk(lemmatize(sentence))





# def get_feedback_with_word2vec(text, sigwords):
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

def get_feedback_for_where(text, sigwords):
    sentences = get_feedback_with_stemmer(text, sigwords)

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

def get_feedback_for_who(text, sigwords):
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


# example_sentence = 'Where did Fred find the cookies?'.split()
# example_sentence2 = 'The rain in Spain falls mostly on the plain.'.split()
#
# print(st.tag(example_sentence))
# print(st.tag(example_sentence2))
