import json
import os

import parser.argparser as argparser
import parser.parser as parser
from documents.DocumentsCreator import DocumentsCreator
from graphs.GraphManager import GraphManager


def main():
    args = argparser.createParser()

    # Process input documents and tag them with HeidelTime
    documents = parser.readAndHeidelTimeJson(args.data, args)

    # Create processed DocumentCollection
    # Processing includes parsing of HeidelTime tags as well as spacy pipeline (stop word removal, lemmatization,
    # building a BoW representation)
    creator = DocumentsCreator(args)
    documents = creator.parse_documents(documents)

    # build up time-centric co-occurrence graphs, here co-occurrences are extracted as well
    graphs = GraphManager.from_DocumentCollection(documents, args)

    # Graph processing
    graphs.weight_graph_nodes(weighting="tf_itf_per_granularity")
    graphs.reduce_to_highest_weighted_nodes(25)

    result_json = graphs.create_graphs_json()

    output_file = os.path.join(args.output, "timecentricgraphs.json")
    with open(output_file, "w") as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
        print("Grahps stored.", flush=True)


if __name__ == '__main__':
    main()
