import nltk
from nltk.corpus import wordnet
from nltk.corpus.reader.wordnet import WordNetError


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


# Takes a wordnet pos tagged word, and converts to synset
def get_synset(word, tag):
    wn_tag = get_wordnet_tag(tag)
    if wn_tag is None:
        return None
    try:
        synsets = wordnet.synsets(word, wn_tag)
        if synsets:
            return synsets[0]
    except WordNetError:
        pass


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
