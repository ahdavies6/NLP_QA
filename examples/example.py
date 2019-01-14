import nltk


# we'll be using the WordNet Lemmatizer
# don't worry, though; this only downloads something if it hasn't already been downloaded
nltk.download('wordnet')
from nltk.stem.wordnet import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

text = "John was kissing Mary. This means that kisses were being made."
sentences = nltk.sent_tokenize(text)

for sentence in sentences:
    words = nltk.word_tokenize(sentence)

    # part of speech tagging:
    tags = nltk.pos_tag(words)
    for word, tag in tags:
        print("word: '{}'".format(word))
        print("tag: '{}'".format(tag))

        # get WordNet tags from Penn Treebank (NLTK's default) tags
        simple_tag = None
        if tag[0] == 'N':
            simple_tag = 'n'
        elif tag[0] == 'V':
            simple_tag = 'v'

        # lemmatization:
        if simple_tag:
            lemma = lemmatizer.lemmatize(word, simple_tag)
        else:
            lemma = lemmatizer.lemmatize(word)
        print("lemma: '{}'".format(lemma))

        # newline
        print()
