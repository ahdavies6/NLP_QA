import nltk


def get_ne_chunks(sentence):
    tokens = nltk.word_tokenize(sentence)
    tagged = nltk.pos_tag(tokens)
    chunk_tokens = nltk.ne_chunk(tagged)

    chunks = []
    constituents = []
    for i in chunk_tokens:
        if type(i) == nltk.Tree:
            constituents.append(" ".join([token for token, pos in i.leaves()]))
        elif constituents:
            entity = " ".join(constituents)
            if entity:
                chunks.append(entity)
                constituents = []

    return chunks


def main():
    print(get_ne_chunks("George was a member of the Republican Party."))


if __name__ == "__main__":
    main()
