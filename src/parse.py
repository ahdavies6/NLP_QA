# import en_core_web_lg
from nltk import Tree
from spacy.tokens import Doc, Token
from nltk.parse.corenlp import CoreNLPParser, CoreNLPDependencyParser
from sentence_similarity import sentence_similarity


_constituency_parser = None
_dependency_parser = None
# _spacy_parser = None


class DependencyNode(object):

    def __init__(self, root_node_dict, nodes_dict):
        self._node_dict = root_node_dict
        # if 'dependencies' not in node_dict:
        #     self._node_dict['dependencies'] = []
        self._node_dict['num_nodes'] = len(nodes_dict)
        for rel in root_node_dict['deps']:
            # if node['head'] == self._node_dict['address']:
            #     self._node_dict[]
            for address in root_node_dict['deps'][rel]:
                if 'dep_Nodes' in self:
                    if rel in self._node_dict['dep_Nodes']:
                        self._node_dict['dep_Nodes'][rel].append(
                            DependencyNode(
                                nodes_dict[address], nodes_dict
                            )
                        )
                    else:
                        self._node_dict['dep_Nodes'][rel] = [
                            DependencyNode(
                                nodes_dict[address], nodes_dict
                            )
                        ]
                else:
                    self._node_dict['dep_Nodes'] = {
                        rel: [
                            DependencyNode(
                                nodes_dict[address], nodes_dict
                            )
                        ]
                    }

    def __str__(self):
        # full_str = ""
        # if 'dep_Nodes' in self._node_dict:
        #     for i in range(self._node_dict['num_nodes']):
        #         if i == self._node_dict['address']:
        #             full_str = "{}{}{}".format(
        #                 full_str,
        #                 " " if self._node_dict['tag'] != '.' else "",
        #                 self._node_dict['word']
        #             )
        #         for rel in self._node_dict['dep_Nodes']:
        #             for node in self._node_dict['dep_Nodes'][rel]:
        #                 if node['address'] == i:
        #                     full_str = "{}{}{}".format(
        #                         full_str,
        #                         " " if node['tag'] != '.' else "",
        #                         " ".join(node.__str__().split())
        #                     )
        #     return full_str
        # else:
        #     return self._node_dict['word']
        return " ".join([token[0] for token in self.get_pairs])

    def __getitem__(self, key):
        result = self._node_dict.get(key)
        if result:
            if isinstance(result, list) and len(result) == 1:
                return result[0]
            else:
                return result
        else:
            result = self._node_dict['dep_Nodes'].get(key)
            if isinstance(result, list) and len(result) == 1:
                return result[0]
            else:
                return result

    def __contains__(self, item):
        return item in self._node_dict

    @property
    def tuple(self):
        return self._node_dict['word'], self._node_dict['tag']

    @property
    def get_pairs(self):
        return [(node['word'], node['tag']) for node in self.get_nodes]

    @property
    def get_nodes(self):
        nodes = [self]
        if 'dep_Nodes' in self._node_dict:
            # if i == self._node_dict['address']:
            #     full_str = "{}{}{}".format(
            #         full_str,
            #         " " if self._node_dict['tag'] != '.' else "",
            #         self._node_dict['word']
            #     )
            for rel in self._node_dict['dep_Nodes']:
                for node in self._node_dict['dep_Nodes'][rel]:
                    # full = "{}{}{}".format(
                    #     full,
                    #     " " if node['tag'] != '.' else "",
                    #     " ".join(node.__str__().split())
                    # )
                    nodes += node.get_nodes
        return sorted(nodes, key=lambda n: n['address'])


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


# def fill_in_node_dependencies(head_index, nodes):
#     # dependencies = {
#     #     'root': (nodes[index]['word'], nodes[index]['tag']),
#     #     'dependencies': []
#     # }
#     head = nodes[head_index]
#     dependencies = []
#     for node in nodes:
#         if isinstance(node, Node):
#             if node['head'] == head_index:
#                 # dependencies[node['rel']] = get_dependent_indices(node['address'], nodes)
#                 # dependencies['dependencies'].append(dependencies[node['rel']]['dependencies'])
#                 head[node['rel']] = fill_in_node_dependencies(node['address'], nodes)
#                 dependencies += node
#                 head['dependencies'] += dependencies
#             # elif node['address'] == index:
#                 # dependencies['dependencies'].append((node['word'], node['tag']))
#     return dependencies


# # def get_nested_dependencies(root, dependency_list, sentence, dependency_string_sets):
# def get_nested_dependencies(node_index, nodes, sentence, dependency_string_sets):
#     # todo: make this more elegant
#     dependencies = {
#         # 'root': (nodes[node_num]['word'], nodes[node_num]['tag']),
#         # 'full': put_in_order(dependency_string_sets[root[0]], sentence) if root[0] in dependency_string_sets else [root]
#         'root': nodes[node_index]
#         # todo
#     }
#     # for head, relationship, dependent in dependency_list:
#     #     if head == root:
#     #         dependencies[relationship] = get_nested_dependencies(
#     #             dependent,
#     #             dependency_list,
#     #             sentence,
#     #             dependency_string_sets
#     #         )
#     # for node in nodes:
#     #     if node['head'] == node[node_index]:
#     #         dependencies[node['rel']] = get_nested_dependencies(
#     #             node_index,
#     #             nodes,
#     #             # sentence,
#     #             # dependency_string_sets
#     #         )
#     dependency_indices = get_dependent_indices(node_index, nodes)
#
#     return dependencies


def to_sentence(tokens, index=0):
    if isinstance(tokens, str):
        return tokens
    elif isinstance(tokens, list):
        if isinstance(tokens[index], tuple):
            return ' '.join([
                token[index] for token in tokens
            ])
        else:
            return ' '.join(tokens)
    elif isinstance(tokens, Token):
        return ' '.join([token.text for token in tokens.subtree])


def get_dependency_parse(sentence):
    """
    Get a full Sentence object from a raw text sentence
    :param sentence: the sentence (in raw text)
    :return: a Sentence object representing the syntactic dependencies in the sentence
    """
    # find all syntactic dependencies for the question
    dependency_graph = next(_dependency_parser.raw_parse(sentence))
    # # nodes = [None] + [Node(dependency_graph.get_by_address(i)) for i in range(1, len(dependency_graph.nodes))]
    # nodes = [None] + [
    #     Node(dependency_graph.get_by_address(i), dependency_graph.nodes) for i in range(1, len(dependency_graph.nodes))
    # ]
    #
    # # dependency_string_sets = {}  # keys are the head word, values are the fully traversed string
    # # for dependency in dependency_graph.tree().subtrees():
    # #     if isinstance(dependency, Tree):
    # #         dependency_string_sets[dependency.label()] = traverse_dep_tree(dependency)
    #
    # # root = (dependency_graph.root['word'], dependency_graph.root['tag'])
    # # dependency_list = list(dependency_graph.triples())
    #
    # # sentence = []   # get full sentence as S = [(word1, tag1), ...]
    # # for i in range(1, len(dependency_graph.nodes)):
    # #     sentence.append((dependency_graph.nodes[i]['word'], dependency_graph.nodes[i]['tag']))
    #
    # # heads = get_nested_dependencies(root, dependency_list, sentence, dependency_string_sets)
    # # heads = get_nested_dependencies(1, nodes, sentence, dependency_string_sets)
    # # heads = fill_in_node_dependencies(dependency_graph.root['address'], nodes)

    return DependencyNode(dependency_graph.root, dependency_graph.nodes)

    # return Sentence(heads)


def get_constituency_parse(raw_sentence):
    """
    Get a full constituency Tree structure from raw text sentence
    :param raw_sentence: the sentence (in raw text)
    :return: a Tree structure representing the sentence's constituents
    """
    return next(_constituency_parser.raw_parse(raw_sentence))


def get_spacy_dep_parse(raw_sentence):
    return _spacy_parser(raw_sentence)


def get_token_dependent_of_type(root, dep_label):
    if isinstance(root, Doc):
        for token in root:
            if token.dep_ == 'ROOT':
                root = token
                break

    for child in root.children:
        if child.dep_ == dep_label:
            return child


def get_subtree_dependent_of_type(root, dep_label):
    if isinstance(root, Doc):
        for token in root:
            if token.dep_ == 'ROOT':
                root = token
                break

    for child in root.children:
        if child.dep_ == dep_label:
            return [subtree for subtree in child.subtree]


def best_dep_of_type(head, dep_label_list):
    deps = [token for token in head.subtree if token.dep_ in dep_label_list]
    if deps:
        return max(deps, key=lambda x: len(list(x.subtree)))


def get_all_verbs_from_sentence(document):
    return [token for token in document if token.pos_ == 'VERB']


# def get_all_subjs_of_verb():
#     pass
#
#
# def get_all_iobjs_of_verb():
#     pass


# todo: distinguish more in answers?
def useful_arguments(head):
    # best_subj = max(
    #     [token for token in verb.subtree if token.dep_ in ['nsubj', 'nsubjpass', 'csubj', 'csubjpass', 'agent']],
    #     key=lambda x: len(list(x.subtree))
    # )
    # best_obj = max(
    #     [token for token in verb.subtree if token.dep_ in ['obj', 'dobj', 'iobj', 'pobj', 'dative', 'obl']],
    #     key=lambda x: len(list(x.subtree))
    # )
    # # if best_subj and best_obj:
    # #     return [best_subj, best_obj]
    # # elif best_subj:
    # #     return [best_subj]
    # # elif best_obj:
    # #     return [best_obj]
    best_subj = best_dep_of_type(head, ['nsubj', 'nsubjpass', 'csubj', 'csubjpass', 'agent'])
    best_obj = best_dep_of_type(head, ['obj', 'dobj', 'iobj', 'pobj', 'dative', 'obl'])
    return [arg for arg in [best_subj, best_obj] if arg]


def extras(head):
    # best_adjs = max(
    #     [token for token in verb.subtree if token.dep_ in [
    #         'acl', 'amod', 'appos', 'nn', 'nounmod', 'nummod', 'poss', 'quantmod', 'relcl'
    #     ]],
    #     key=lambda x: len(list(x.subtree))
    # )
    # best_advs = max(
    #     [token for token in verb.subtree if token.dep_ in [
    #         'advcl', 'advmod', 'npmod'
    #     ]],
    #     key=lambda x: len(list(x.subtree))
    # )
    # best_prep = max(
    #     [token for token in verb.subtree if token.dep_ in [
    #         'prep'
    #     ]],
    #     key=lambda x: len(list(x.subtree))
    # )
    best_adjs = best_dep_of_type(
        head,
        ['acl', 'amod', 'appos', 'nn', 'nounmod', 'nummod', 'poss', 'quantmod', 'relcl']
    )
    best_advs = best_dep_of_type(head, ['advcl', 'advmod', 'npmod'])
    best_prep = best_dep_of_type(head, ['prep'])
    return [mod for mod in [best_adjs, best_advs, best_prep] if mod]


def compare_q_and_a(q_sent_doc, a_sent_doc):
    q_verb = [t for t in q_sent_doc if t.dep_ == 'ROOT']
    assert len(q_verb) == 1
    q_verb = q_verb[0]

    q_extras = extras(q_verb)
    q_args = useful_arguments(q_verb)

    # a_verb = max(get_all_verbs_from_sentence(a_doc), key=lambda x: len(useful_arguments(x)))
    num_args_to_verb = {}
    for verb in get_all_verbs_from_sentence(a_sent_doc):
        a_args = useful_arguments(verb)
        if q_args and a_args:
            best_score, q_arg, a_arg = max(
                [(
                    sentence_similarity(
                        to_sentence(q_arg),
                        to_sentence(a_arg)
                    ),
                    q_arg,
                    a_arg
                ) for q_arg in q_args for a_arg in a_args],
                key=lambda pair: sentence_similarity(to_sentence(pair[1]), to_sentence(pair[2]))
            )
        else:
            best_score = -1
            q_arg = a_arg = None
        if best_score in num_args_to_verb:
            # num_args_to_verb[len(args)].append(verb)
            num_args_to_verb[best_score] += [(verb, q_arg, a_arg)]
        else:
            # num_args_to_verb[len(a_args)] = [(verb, best_score, q_arg, a_arg)]
            num_args_to_verb[best_score] = [(verb, q_arg, a_arg)]

    for val in sorted(num_args_to_verb.keys(), reverse=True):
        if val > -1:
            best = (val, -1, None, None, None)
            # e.g. ( .7, .5, verb, arg1, arg2)
            for verb, q_arg, a_arg in num_args_to_verb[val]:
                if extras(verb) and q_extras:
                    extra_sim = max([
                        sentence_similarity(
                            to_sentence(a_extra),
                            to_sentence(q_extra)
                        ) for a_extra in extras(verb) for q_extra in q_extras
                    ])
                else:
                    extra_sim = -1
                if extra_sim > best[1]:
                    best = (val, extra_sim, verb, q_arg, a_arg)
            if best != (val, -1, None, None, None):
                return best[0], best[1]

            # return max(
            #     (
            #         val,
            #         sentence_similarity(
            #             to_sentence(extras(num_args_to_verb[val])), to_sentence(extras(q_verb))
            #         ),
            #         num_args_to_verb[val]
            #     ),
            #     key=lambda a_verb: sentence_similarity(
            #         to_sentence(extras(a_verb)), to_sentence(extras(q_verb))
            #     )
            # )


if _dependency_parser is None:
    _dependency_parser = CoreNLPDependencyParser()
if _constituency_parser is None:
    _constituency_parser = CoreNLPParser()
# if _spacy_parser is None:
#     _spacy_parser = en_core_web_lg.load()
