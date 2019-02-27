import nltk


with open("example_text.txt") as f:
    fulltext = []
    for line in f:
        fulltext.append(line.strip())
    fulltext = ' '.join(fulltext)

sentences = nltk.sent_tokenize(fulltext)
for sentence in sentences:
    words = nltk.word_tokenize(sentence)
    pairs = nltk.pos_tag(words)
    print(pairs)
