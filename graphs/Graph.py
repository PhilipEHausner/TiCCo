from __future__ import annotations
import typing
import collections

import documents.Documents as Documents
from documents.Timestamps import Timestamp


class Node:
    # static
    next_id: int = 0
    id: int
    label: str
    count: int
    weight: int
    words = typing.List[Documents.Word]

    def __init__(self, word: Documents.Word, weight: int = 1) -> None:
        self.label = word.lemma
        self.id = Node.next_id
        Node.next_id += 1
        self.count = 1
        self.weight = weight
        self.words = [word]

    def increase_weight(self, word: Documents.Word, weight: int = 1) -> None:
        if word not in self.words:
            self.words.append(word)
            self.count += 1
            self.weight += weight

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.label == other.label
        return NotImplemented

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return "Node({0}, {1})".format(self.label, self.weight)

    def __str__(self):
        return "Node({0}, {1})".format(self.label, self.weight)


class Edge:
    # Only for undirected graphs
    source: Node
    target: Node
    sent_functionality: list

    def __init__(self, source: Node, target: Node):
        if source.label <= target.label:
            self.source = source
            self.target = target
        else:
            self.source = target
            self.target = source
        self.sent_functionality = []

    def append_to_sentence_functionality(self, word1: Documents.Word, word2: Documents.Word):
        cooc = {"doc_id": word1.belongs_to.belongs_to.idx,
                "sentence1": (word1.belongs_to.sent_start, word1.belongs_to.sent_end),
                "sentence2": (word2.belongs_to.sent_start, word2.belongs_to.sent_end)}
        if cooc not in self.sent_functionality:
            self.sent_functionality.append(cooc)

    def __eq__(self, other):
        if isinstance(other, Edge):
            return self.source == other.source and self.target == other.target
        return NotImplemented

    def __hash__(self):
        return hash((self.source, self.target))

    def __repr__(self):
        return "Edge({0}, {1})".format(self.source.label, self.target.label)

    def __str__(self):
        return "Edge({0}, {1})".format(self.source.label, self.target.label)


class Graph:
    timestamp: Timestamp
    node_to_label: typing.DefaultDict[Node]
    label_to_node: typing.DefaultDict[str]
    nodes_to_edge: typing.DefaultDict[(Node, Node)]
    edge_to_nodes: typing.DefaultDict[Edge]

    def __init__(self, timestamp: Timestamp):
        self.timestamp = timestamp
        self.node_to_label = collections.defaultdict(lambda: None)
        self.label_to_node = collections.defaultdict(lambda: None)
        self.nodes_to_edge = collections.defaultdict(lambda: None)
        self.edge_to_nodes = collections.defaultdict(lambda: None)

    def nodes(self):
        return self.node_to_label.keys()

    def edges(self):
        return self.edge_to_nodes.keys()

    # if node is not in self.nodes yet, add it to the list. Otherwise increase its weight.
    def add_node(self, node: Node, word: Documents.Word) -> None:
        if self.node_to_label[node]:
            node.increase_weight(word)
        else:
            self.node_to_label[node] = node.label
            self.label_to_node[node.label] = node

    def add_edge(self, word1: Documents.Word, word2: Documents.Word) -> None:
        node1 = self.label_to_node[word1.lemma]
        node2 = self.label_to_node[word2.lemma]
        if not node1:
            node1 = Node(word1)
        self.add_node(node1, word1)

        if not node2:
            node2 = Node(word2)
        self.add_node(node2, word2)

        if node1.label > node2.label:
            node1, node2 = node2, node1
            word1, word2 = word2, word1

        if self.nodes_to_edge[(node1, node2)]:
            edge = self.nodes_to_edge[(node1, node2)]
        else:
            edge = Edge(node1, node2)
            self.nodes_to_edge[(node1, node2)] = edge
            self.edge_to_nodes[edge] = (node1, node2)

        edge.append_to_sentence_functionality(word1, word2)

    def remove_node(self, node: Node) -> None:
        edges_to_remove = [self.nodes_to_edge[(node1, node2)]
                           for (node1, node2)
                           in self.nodes_to_edge.keys()
                           if (node1 == node or node2 == node)]
        # loop version of above code for clarity
        # for node1, node2 in self.nodes_to_edge.keys():
        #     if node1 == node or node2 == node:
        #         edges_to_remove.append(self.nodes_to_edge[(node1, node2)])
        [self.remove_edge(edge) for edge in edges_to_remove]
        self.node_to_label.pop(node, None)
        self.label_to_node.pop(node.label, None)

    def remove_edge(self, edge: Edge) -> None:
        self.nodes_to_edge.pop(self.edge_to_nodes[edge], None)
        self.edge_to_nodes.pop(edge, None)

    def remove_self_loops(self) -> None:
        edges_to_remove = []
        for nodes, edge in self.nodes_to_edge:
            if nodes[0] == nodes[1]:
                edges_to_remove.append(edge)
        [self.nodes_to_edge.pop((edge.source, edge.target)) for edge in edges_to_remove]
        [self.edge_to_nodes.pop(edge) for edge in edges_to_remove]

    def remove_timestamp_self_appearance(self) -> None:
        for node, label in self.node_to_label:
            if node.label == str(self.timestamp):
                self.remove_node(node)
                break

    def require_minimum_node_weight(self, min_weight: int) -> None:
        nodes_to_remove = [node for node in self.node_to_label.keys() if node.weight < min_weight]
        [self.remove_node(node) for node in nodes_to_remove]

    def reduce_to_highest_weighted_nodes(self, n: int) -> None:
        # there are less or equal than n nodes
        if n >= len(self.node_to_label):
            return
        weights = [node.weight for node in self.node_to_label.keys()]
        weights = list(sorted(weights))
        min_weight = weights[-n]
        self.require_minimum_node_weight(min_weight)


def get_graph_from_list(graphs: typing.List[Graph], year: int, month: int = None) -> typing.Optional[Graph]:
    """
    Return graph of specified date. This function is designed for use increate_graph_from_timecentric_cooccurrences, and
    may break other code.
    @param graphs: list of graphs to look in
    @param year: queried year
    @param month: queried month
    @return: the found graph or None
    """
    date_exists = None
    result = None
    # desired graph has year granularity
    if year and not month:
        for graph in graphs:
            if graph.timestamp.year == year and graph.timestamp.granularity == "Y":
                result = graph
                date_exists = True
                break
        # Remove the graph from the list, since we append it later on, and hence, want to avoid duplicates
        if date_exists:
            graphs.remove(result)
        # Desired graph does not exist yet, create it
        if not date_exists:
            result = Graph(Timestamp(year=year))
    # desired graph has month granularity
    elif year and month:
        for graph in graphs:
            if graph.timestamp.year == year and graph.timestamp.month == month and graph.timestamp.granularity == "M":
                result = graph
                date_exists = True
                break
        # Remove the graph from the list, since we append it later on, and hence, want to avoid duplicates
        if date_exists:
            graphs.remove(result)
        # Desired graph does not exist yet, create it
        if not date_exists:
            result = Graph(Timestamp(year=year, month=month))
    return result


# extra function for multiprocessing
def create_graph_from_timecentric_cooccurrences(data: typing.Tuple[Timestamp,
                                                                   typing.List[typing.Tuple[Documents.Word,
                                                                                            Documents.Word]]],
                                                existing_graphs: typing.List[Graph]) \
        -> typing.List[Graph]:
    """
    Construct graphs from given co-occurrence list
    @param data: tuple with (timestamp, list of co-occurrences)
    @param existing_graphs: Graphs previously computed
    @return: list of graphs with changed content
    """
    timestamp, timecentric_cooccurrences = data[0], data[1]

    # timestamp is of year granularity
    if timestamp.year and not timestamp.month and not timestamp.day:
        graph_year = Graph(timestamp)
        for word1, word2 in timecentric_cooccurrences:
            graph_year.add_edge(word1, word2)
        return [graph_year]

    # timestamp is of month granularity
    if timestamp.year and timestamp.month and not timestamp.day:
        graph_year = get_graph_from_list(existing_graphs, timestamp.year)
        graph_month = Graph(timestamp)
        for word1, word2 in timecentric_cooccurrences:
            graph_year.add_edge(word1, word2)
            graph_month.add_edge(word1, word2)
        return [graph_month, graph_year]

    # timestamp is of day granularity
    if timestamp.year and timestamp.month and timestamp.day:
        graph_year = get_graph_from_list(existing_graphs, timestamp.year)
        graph_month = get_graph_from_list(existing_graphs, timestamp.year, timestamp.month)
        graph_day = Graph(timestamp)
        for word1, word2 in timecentric_cooccurrences:
            graph_year.add_edge(word1, word2)
            graph_month.add_edge(word1, word2)
            graph_day.add_edge(word1, word2)
        return [graph_day, graph_month, graph_year]

    return []
