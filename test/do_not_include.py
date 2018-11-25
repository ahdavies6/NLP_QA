from text_analyzer import *
import nltk
# import spacy
from parse import *
import en_core_web_lg

#
# def getGrammarPhrases(sentence, grammar):
#     x_phrases = []
#     parser = nltk.RegexpParser(grammar)
#     for sub_form in parser.parse(nltk.pos_tag(nltk.word_tokenize(sentence))):
#         if type(sub_form) == nltk.tree.Tree:
#             x_phrases.append(restring(sub_form))
#
#     return x_phrases
#
# sent = 'Who is Jennifer Conkie?'
# whoIsTitle = r"""
#     XX: {<WP><VBZ|VBD><JJ>*<NN|NNP>+<POS>?<JJ>*<NN|NNP>+<JJ>*}
#     {<WP><VBZ|VBD><DT><NN|NNP>+<IN>?<JJ>*<NN|NNP>+<JJ>*}
#     """
# whoIsName = r"""
#     XX: {<WP><VBZ|VBD><JJ>*<NNP>+<.>}
#     """
# titleGrammar = r"""
#     XX: {<,>?<PT>?<JJ>*<NN>+}
# """
# name_phrase_grammar = r"""
#     XX: {<NNP>+<,><DT>?<JJ>*<NN>+}
#     {<,>?<NN|NNP>+<IN><DT>?<NN|NNP>+}
#     {<NN|NNP>+<NNP>+}
# """
# whoIsTitle2 = r"""
#     XX: {<WP><VBZ|VBD><DT><JJ>*<NN|NNP>+<JJ>*}
#     """
# title = r"""
# """
# while(True):
#     sent = input("Enter sentence: ")
#     if sent == 'quit':
#         break
#     else:
#         print(getGrammarPhrases(sent, whoIsTitle2))
#         print(nltk.pos_tag(nltk.word_tokenize(sent)))

model = en_core_web_lg.load()
while(True):
    sent = input("Enter sentence: ")
    if sent == 'quit':
        break
    else:
        sent = model(sent)
        for verb in get_all_verbs_from_sentence(sent):
            print(verb)
            try:
                if useful_arguments(verb):
                    print(useful_arguments(verb))
            except:
                print("useful failed.")
                pass
            try:
                if extras(verb):
                    print(extras(verb))
            except:
                print("extras failed.")
                pass
            print()
x=10
