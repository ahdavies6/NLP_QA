from nltk import Tree
from nltk.parse.corenlp import CoreNLPParser, CoreNLPDependencyParser
from nltk.parse.dependencygraph import DependencyGraph


# todo: try this out
# from nltk.stem.wordnet import WordNetLemmatizer


class Sentence(object):

    def __init__(self, dependents=None):
        self._dependents = dependents if dependents else {}

    def __getitem__(self, key):
        return self._dependents.get(key)

    def __setitem__(self, key, value):
        self._dependents[key] = value

    def __contains__(self, item):
        return item in self._dependents


class Question(Sentence):

    def __init__(self, question_word, dependents=None):
        super().__init__(dependents)
        self._dependents['qword'] = [question_word]


def get_all_dependents(graph, node):
    dependents = []
    for key in node['deps']:
        second_order_dependents = []
        for i in node['deps'][key]:
            third_order_dependents = get_all_dependents(graph, graph.nodes[i])
            if third_order_dependents:
                second_order_dependents.append((graph.nodes[i], third_order_dependents))
            else:
                second_order_dependents.append(graph.nodes[i])
        if second_order_dependents:
            dependents.append((node, second_order_dependents))
        else:
            dependents.append(node)
    return dependents


def put_in_order(dependents, sentence):
    """
    :param dependents: (unordered) set of dependents in the sentence
    :param sentence: (ordered) list of tuples of word tokens [(word1, tag1), (word2, tag2), ...]
    :return: the dependents, in the order they appear in the sentence
    """
    potential_order = []
    for word, tag in sentence:
        if word in dependents:
            potential_order.append((word, tag))
            if len(potential_order) == len(dependents):
                return potential_order
        else:
            potential_order = []


def traverse_dep_tree(tree):
    nodes = [tree.label()]
    for subtree in tree:
        if isinstance(subtree, Tree):
            nodes.extend(traverse_dep_tree(subtree))
        elif isinstance(subtree, str):
            nodes.append(subtree)
    return nodes


def get_nested_dependencies(root, dependency_list, sentence, dependency_string_sets):
    dependencies = {
        'root': root,
        'full': put_in_order(dependency_string_sets[root[0]], sentence) if root[0] in dependency_string_sets else [root]
    }
    for head, relationship, dependent in dependency_list:
        if head == root:
            dependencies[relationship] = get_nested_dependencies(
                dependent,
                dependency_list,
                sentence,
                dependency_string_sets
            )
    return dependencies


def get_sentence(sentence):
    """
    Get a full Sentence object from a raw text sentence
    :param sentence: the sentence (in raw text)
    :return: a Sentence object representing the syntactic dependencies in the sentence
    """
    # find all syntactic dependencies for the question
    dependency_graph = next(CoreNLPDependencyParser().raw_parse(sentence))

    # todo: debug the part of this that gives repeat words the wrong text
    dependency_string_sets = {}  # keys are the head word, values are the fully traversed string
    for dependency in dependency_graph.tree().subtrees():
        if isinstance(dependency, Tree):
            dependency_string_sets[dependency.label()] = traverse_dep_tree(dependency)

    root = (dependency_graph.root['word'], dependency_graph.root['tag'])
    dependency_list = list(dependency_graph.triples())

    sentence = []   # get full sentence as S = [(word1, tag1), ...]
    for i in range(1, len(dependency_graph.nodes)):
        sentence.append((dependency_graph.nodes[i]['word'], dependency_graph.nodes[i]['tag']))

    heads = get_nested_dependencies(root, dependency_list, sentence, dependency_string_sets)

    return Sentence(heads)
