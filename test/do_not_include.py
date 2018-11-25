from text_analyzer import *
import nltk
# import spacy


def getGrammarPhrases(sentence, grammar):
    x_phrases = []
    parser = nltk.RegexpParser(grammar)
    for sub_form in parser.parse(nltk.pos_tag(nltk.word_tokenize(sentence))):
        if type(sub_form) == nltk.tree.Tree:
            x_phrases.append(restring(sub_form))

    return x_phrases

sent = 'Who is Jennifer Conkie?'
whoIsTitle = r"""
    XX: {<WP><VBZ|VBD><JJ>*<NN|NNP>+<POS>?<JJ>*<NN|NNP>+<JJ>*}
    {<WP><VBZ|VBD><DT><NN|NNP>+<IN>?<JJ>*<NN|NNP>+<JJ>*}
    """
whoIsName = r"""
    XX: {<WP><VBZ|VBD><JJ>*<NNP>+<.>}
    """
titleGrammar = r"""
    XX: {<,>?<PT>?<JJ>*<NN>+}
"""
name_phrase_grammar = r"""
    XX: {<NNP>+<,><DT>?<JJ>*<NN>+}
    {<,>?<NN|NNP>+<IN><DT>?<NN|NNP>+}
    {<NN|NNP>+<NNP>+}
"""
whoIsTitle2 = r"""
    XX: {<WP><VBZ|VBD><DT><JJ>*<NN|NNP>+<JJ>*}
    """
title = r"""
"""
while(True):
    sent = input("Enter sentence: ")
    if sent == 'quit':
        break
    else:
        print(getGrammarPhrases(sent, whoIsTitle2))
        print(nltk.pos_tag(nltk.word_tokenize(sent)))

x=10
