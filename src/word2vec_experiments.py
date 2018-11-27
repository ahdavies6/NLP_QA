import gensim
from gensim.models.word2vec import Word2Vec


model = gensim.models.KeyedVectors.load_word2vec_format('../GoogleNews-vectors-negative300.bin.gz',
                                                        binary=True, limit=100000)


def similarity(word1, word2):
    return model.similarity(word1, word2)
