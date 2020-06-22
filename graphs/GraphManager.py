from __future__ import annotations

import argparse
import typing
import collections
import multiprocessing
import timeit
import math
import collections
import sys

import tqdm

from graphs.Graph import Graph
from graphs.Graph import create_graph_from_timecentric_cooccurrences
from documents.Timestamps import Timestamp
import documents.Documents as Documents
from cooccurrences.cooccurrences import extract_timecentric_cooccurrences_from_collection


class GraphManager:
    graphs: typing.DefaultDict[Timestamp, Graph]
    weighting_function = None

    def __init__(self, timecentric_graphs: typing.DefaultDict[Timestamp, Graph]) -> None:
        self.graphs = timecentric_graphs

    @classmethod
    def from_DocumentCollection(cls, documents: Documents.DocumentCollection, args: argparse.Namespace) -> GraphManager:
        # First, extract time-centric co-occurrences
        print("Start extracting time-centric co-occurrences.")

        start = timeit.default_timer()
        timecentric_coocs = extract_timecentric_cooccurrences_from_collection(documents, args)
        end = timeit.default_timer()
        print("Finished extracting time-centric co-occurrences in", end - start, "seconds.")

        # Create a graph for each date co-occurrences were extracted from
        print("Start creating time-centric co-occurrence graphs.")
        sys.stdout.flush()
        start = timeit.default_timer()

        graphs = []

        count, max_count = 1, len(timecentric_coocs)
        for key, value in timecentric_coocs.items():
            print("Graph (Y):", count, "/", max_count, end="\r", flush=True)
            if key.year and not key.month and not key.day:
                graphs.extend(create_graph_from_timecentric_cooccurrences((key, value), graphs))
            count += 1

        count, max_count = 1, len(timecentric_coocs)
        for key, value in timecentric_coocs.items():
            print("Graph (M):", count, "/", max_count, end="\r", flush=True)
            if key.year and key.month and not key.day:
                graphs.extend(create_graph_from_timecentric_cooccurrences((key, value), graphs))
            count += 1

        count, max_count = 1, len(timecentric_coocs)
        for key, value in timecentric_coocs.items():
            print("Graph (D):", count, "/", max_count, end="\r", flush=True)
            if key.year and key.month and key.day:
                graphs.extend(create_graph_from_timecentric_cooccurrences((key, value), graphs))
            count += 1

        timecentric_graphs = collections.defaultdict(None)
        for g in graphs:
            timecentric_graphs[g.timestamp] = g
        end = timeit.default_timer()
        print("Finished extracting time-centric co-occurrence graphs in", end - start, "seconds.", flush=True)

        return cls(timecentric_graphs)

    def _tf_itf_weighting_per_granularity(self) -> None:
        granularities = ["D", "M", "Y"]
        for granularity in granularities:
            # for normalization
            sum_terms = 0
            # around how many timestamps is the term found
            term_around_x_timestamps = collections.defaultdict(int)
            number_of_timestamps = 0
            for graph in self.graphs.values():
                if graph.timestamp.granularity == granularity:
                    number_of_timestamps += 1
                    for node in graph.nodes():
                        sum_terms += node.count
                        term_around_x_timestamps[node.label] += 1
            itf = dict()
            sum_terms = 1
            for term, count in term_around_x_timestamps.items():
                itf[term] = math.log(number_of_timestamps / (1 + count))
            for graph in self.graphs.values():
                if graph.timestamp.granularity == granularity:
                    for node in graph.nodes():
                        node.weight = (node.count / sum_terms) * itf[node.label]

    def _tf_itf_weighting(self) -> None:
        # for normalization
        sum_terms = 0
        # around how many timestamps is the term found
        term_around_x_timestamps = collections.defaultdict(int)
        number_of_timestamps = len(self.graphs)
        for graph in self.graphs.values():
            for node in graph.nodes():
                sum_terms += node.count
                term_around_x_timestamps[node.label] += 1
        itf = dict()
        sum_terms = 1
        for term, count in term_around_x_timestamps.items():
            itf[term] = math.log(number_of_timestamps / (1 + count))
        for graph in self.graphs.values():
            for node in graph.nodes():
                node.weight = (node.count / sum_terms) * itf[node.label]

    def weight_graph_nodes(self, weighting: str = "tf_itf_per_granularity") -> None:
        functions = {
            "tf_itf_per_granularity": self._tf_itf_weighting_per_granularity,
            "tf_itf": self._tf_itf_weighting
        }
        func = functions.get(weighting)
        if not func:
            print("GraphManager: Invalid function name in weight_graph_nodes. No changes made.")
            return
        else:
            print("Start weighing graph nodes.", flush=True)
            start = timeit.default_timer()
            func()
            end = timeit.default_timer()
            print("Calculated weights in", end - start, "seconds.", flush=True)

    def remove_self_loops(self) -> None:
        for graph in self.graphs.values():
            graph.remove_self_loops()

    def remove_timestamp_self_appearance(self) -> None:
        for graph in self.graphs.values():
            graph.remove_timestamp_self_appearance()

    def reduce_to_highest_weighted_nodes(self, n: int) -> None:
        print(f"Reducing graphs to {n} highest weighted nodes.", flush=True)
        start = timeit.default_timer()
        # map(lambda g: g.reduce_to_highest_weighted_nodes(n), self.graphs.values())
        # [g.reduce_to_highest_weighted_nodes(n) for g in self.graphs.values()]
        count, max_count = 0, len(self.graphs)
        for graph in self.graphs.values():
            print("Graph:", count, "/", max_count, end="\r", flush=True)
            count += 1
            graph.reduce_to_highest_weighted_nodes(n)
        end = timeit.default_timer()
        print("Reduced graphs in", end - start, "seconds.", flush=True)

    def create_graphs_json(self) -> typing.Dict[str, typing.Dict]:
        result = {}
        for timestamp, graph in self.graphs.items():
            result[str(timestamp)] = {
                    "nodes": [{"id": node.id, "label": node.label, "value": node.weight} for node in graph.nodes()],
                    "edges": [
                        {"from": edge.source.id, "to": edge.target.id, "value": len(edge.sent_functionality),
                         "sent_functionality": edge.sent_functionality}
                        for edge in graph.edges()
                    ]}
        return result

