from nltk.tag import StanfordNERTagger
import nltk
from nltk.corpus import stopwords


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

def get_feedback3(text, sigwords):
    sentences = nltk.sent_tokenize(text)

    in_list = []

    stopword = set(stopwords.words('english'))

    ps = nltk.stem.PorterStemmer()

    for sentence in sentences:
        count = 0
        ps_sentence = [ps.stem(word) for word in nltk.word_tokenize(sentence)]
        for word in sigwords:
            if ps.stem(word) in ps_sentence and word not in stopword:
                count += sentence.count(word)
        if count > 0:
            in_list.append((-count, sentence))

    return in_list

def main():
    pass


if __name__ == "__main__":
    main()

# model = '../stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz'
# jar = '../stanford-ner/stanford-ner.jar'
# st = StanfordNERTagger(model, jar, encoding='utf-8')
#
#
# example_sentence = 'Where did Fred find the cookies?'.split()
# example_sentence2 = 'The rain in Spain falls mostly on the plain.'.split()
#
# print(st.tag(example_sentence))
# print(st.tag(example_sentence2))
