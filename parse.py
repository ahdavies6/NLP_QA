from nltk import Tree
from nltk.parse.corenlp import CoreNLPDependencyParser


# todo: try this out
# from nltk.stem.wordnet import WordNetLemmatizer
    
    
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


def get_sentence(sentence):
    """
    Get a full Sentence object from a raw text sentence
    :param sentence: the sentence (in raw text)
    :return: a Sentence object representing the syntactic dependencies in the sentence
    """
    # find all syntactic dependencies for the question
    dependency_graph = next(CoreNLPDependencyParser().raw_parse(sentence))
    from nltk import DependencyGraph
    assert isinstance(dependency_graph, DependencyGraph)
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


# a = get_sentence("Why does Carole Mills think it is more of a health risk not to eat country food than to eat it?")
# b = a['nsubj'].get_nodes
# print()
