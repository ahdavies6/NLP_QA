import gensim
import nltk
from nltk.corpus import stopwords
# from corpus_io import Corpus


model = gensim.models.KeyedVectors.load_word2vec_format('GoogleNews-vectors-negative300.bin.gz',
                                                        binary=True, limit=100000)


def vector_similarity(word1, word2):
    return model.similarity(word1, word2)


def vector_sequence_similarity(sequence1, sequence2):
    if isinstance(sequence1, str):
        sequence1 = nltk.word_tokenize(sequence1)
    if isinstance(sequence2, str):
        sequence2 = nltk.word_tokenize(sequence2)

    score, count = 0, 0
    sequence1 = [s for s in sequence1 if s and s not in stopwords.words('english')]
    sequence2 = [s for s in sequence2 if s and s not in stopwords.words('english')]

    if sequence1 and sequence2:
        for word1 in sequence1:
            matches = []
            for word2 in sequence2:
                try:
                    sim = vector_similarity(word1, word2)
                    matches.append(sim)
                except KeyError:
                    pass

            if matches:
                score += max(matches)
                count += 1

    if count:
        return score / count
    else:
        return 0


# def analyze_corpora(corpus):
#     corpus = Corpus(['developset', 'testset1'])
#     stories = corpus.all


# print(vector_sequence_similarity('eat lunch', 'go to eat'))
# print(vector_sequence_similarity('eat lunch', 'eat dinner'))
