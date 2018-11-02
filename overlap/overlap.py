from sys import argv


def parse_file(filename):
    with open(filename) as file:
        sentence_list = []

        sentence_buffer = []
        words = file.read().split()
        for word in words:
            sentence_buffer.append(word)

            if word[-1] == '.':
                sentence_list.append(sentence_buffer)
                sentence_buffer = []

        # in case the last sentence didn't end with a period
        if len(sentence_buffer) > 0:
            sentence_list.append(sentence_buffer)

        return sentence_list


def main(filename, target):
    sentences = parse_file(filename)

    for sentence in sentences:
        if target in sentence:
            print(" ".join(sentence))


if __name__ == "__main__":
    main(argv[1], argv[2])
