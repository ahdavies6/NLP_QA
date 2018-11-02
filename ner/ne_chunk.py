import nltk


def get_ne_chunks(text):
    chunks = nltk.ne_chunk(
        nltk.pos_tag(
            nltk.word_tokenize(text)
        )
    )
    continuous_chunk = []
    current_chunk = []

    for i in chunks:
        if type(i) == nltk.Tree:
            current_chunk.append(" ".join([token for token, pos in i.leaves()]))
        elif current_chunk:
            named_entity = " ".join(current_chunk)
            if named_entity and named_entity not in continuous_chunk:
                continuous_chunk.append(named_entity)
                current_chunk = []
        else:
            continue

    if continuous_chunk:
        named_entity = " ".join(current_chunk)
        if named_entity and named_entity not in continuous_chunk:
            continuous_chunk.append(named_entity)

    return continuous_chunk


def main():
    print(get_ne_chunks("George was a member of the Republican Party."))


if __name__ == "__main__":
    main()
