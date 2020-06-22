"""
Basic API for serving the processed graph.
"""

import json
import pymongo
import collections
from typing import Dict, List

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

# Use this to serve a public/index.html, see https://github.com/tiangolo/fastapi/issues/130
from starlette.responses import FileResponse

import config

# Database input
dbClient = pymongo.MongoClient("mongodb://localhost:27017/")
database = dbClient[config.DATABASE_NAME]
timeline_dates = database.graphs.find().distinct("_id")

# Set up query index
query_label_to_graphs = collections.defaultdict(set)
for graph in database.graphs.find({}, {"nodes.label"}):
    for node in graph["nodes"]:
        query_label_to_graphs[node["label"].lower()].add(graph["_id"])

index_file = "../output/indexed_documents.json"
with open(index_file, "r") as f:
    docs = json.load(f)

# Generate corresponding wikipedia page urls
links = {k: (value["url"] if "url" in value.keys() else "https://www.wikipedia.org/") for k, value in docs.items()}

# Generate a list of weighted terms
query_suggestions = collections.defaultdict(float)
# Inefficient?
for timestamp in timeline_dates:
    graph = database.graphs.find({"_id": timestamp})[0]
    for node in graph["nodes"]:
        query_suggestions[node["label"]] += node["value"]

query_suggestions = {k: v for k, v in sorted(query_suggestions.items(), key=lambda item: item[1], reverse=True)}

# Generate article titles
article_titles = {k: value["article_title"] for k, value in docs.items()}
section_titles = {k: value["title"] for k, value in docs.items()}

for doc_id, title in article_titles.items():
    if title == section_titles[doc_id]:
        section_titles[doc_id] = "Summary"

# API initialization
app = FastAPI()
app.mount("/public", StaticFiles(directory="public"), name="public")


# Response for various frontend content files
@app.get("/")
async def read_index():
    return FileResponse("public/index.html")


@app.get("/src/network.js")
async def get_network_js():
    return FileResponse("public/src/network.js")


@app.get("/src/timeline.js")
async def get_timeline_js():
    return FileResponse("public/src/timeline.js")


@app.get("/src/text.js")
async def get_text_js():
    return FileResponse("public/src/text.js")


@app.get("/src/query.js")
async def get_query_js():
    return FileResponse("public/src/query.js")


@app.get("/src/options.js")
async def get_options_js():
    return FileResponse("public/src/options.js")


@app.get("/style.css")
async def get_style_js():
    return FileResponse("public/style.css")


@app.get("/node_modules/@fortawesome/fontawesome-free/js/all.js")
async def get_fontawesome_js():
    return FileResponse("public/node_modules/@fortawesome/fontawesome-free/js/all.js")


# Timeline getter
@app.get("/timeline")
async def get_timeline() -> List:
    """
    Returns timeline elements according to the desired visjs format
    @return: Dict of vis.js compatible timeline entries
    """
    # {id: 1, content: 'item 1', start: '2014-04-20'},
    id_count = 0
    timestamps = []
    for timestamp in timeline_dates:
        # Day granularity
        if len(timestamp.split("-")) == 3:
            timestamps.append({"id": id_count, "content": timestamp[5:] + "  ", "start": timestamp,
                               "type": "point", "group": "D", "title": timestamp})
        # Month granularity
        elif len(timestamp.split("-")) == 2:
            # Discern length of months by even/odd/February
            if timestamp.split("-")[1] in ("01", "03", "05", "07", "08", "10", "12"):
                timestamps.append({"id": id_count, "content": timestamp, "group": "M",
                                   "start": timestamp + "-01", "end": timestamp + "-31",
                                   "title": timestamp})
            elif timestamp.split("-")[1] == "02":
                timestamps.append({"id": id_count, "content": timestamp, "group": "M",
                                   "start": timestamp + "-01", "end": timestamp + "-28",
                                   "title": timestamp})
            else:
                timestamps.append({"id": id_count, "content": timestamp, "group": "M",
                                   "start": timestamp + "-01", "end": timestamp + "-30",
                                   "title": timestamp})
        # Year granularity
        else:
            timestamps.append({"id": id_count, "content": timestamp, "group": "Y",
                               "start": timestamp + "-01-01", "end": timestamp + "-12-31",
                               "title": timestamp})

        id_count += 1

    return timestamps


# Network getter
@app.get("/graphs/{timestamp}")
async def get_graph(timestamp: str, limit: int = 10) -> Dict:
    """
    Returns a network for a given timestamp
    @param timestamp: Formatted as Y2020-M04-D30, or a subset thereof (year-month/year only)
    @param limit: Number of nodes that will be returned
    @return:
    """
    try:
        # return data[timestamp]

        # Select the top N "heaviest" nodes
        # nodes = data[timestamp]["nodes"]
        # [0] since _id is primary key, and hence, only one result can be returned
        graph = database.graphs.find({"_id": timestamp})[0]
        nodes = graph["nodes"]
        # Ignore first node, which is the date itself
        nodes = sorted(nodes, key=lambda x: x["value"], reverse=True)[:limit]

        # Create set so it is easier to search
        check_nodes_id = set([node["id"] for node in nodes])
        # Simple O(M + C) iteration to check for valid edges
        edges = []

        # for edge in data[timestamp]["edges"]:
        for edge in graph["edges"]:
            if edge["from"] in check_nodes_id and edge["to"] in check_nodes_id:
                if edge["from"] != edge["to"]:  # Ignore self-loops
                    edges.append(edge)

        return {"nodes": nodes,
                "edges": edges}

    except KeyError:
        print("KeyError encountered")
        return {"nodes": [],
                "edges": []}


@app.get("/text/{doc_id}")
async def get_text(doc_id: int):
    """
    Returns a  text document with given ID
    @param doc_id: Value held in indexed_document.json
    @return: Corresponding document content.
    """
    return docs[str(doc_id)]


@app.get("/text_link/{doc_id}")
async def get_text_link(doc_id: int):
    """
    Returns a link pointing to external sources
    @param doc_id: Value held in indexed_document.json
    @return: Corresponding document link.
    """
    return links[str(doc_id)]


@app.get("/text_title/{doc_id}")
async def get_text_title(doc_id: int):
    """
    Returns the title of the document
    @param doc_id: Value held in indexed documents
    @return: Corresponding document title
    """
    return article_titles[str(doc_id)] + " - " + section_titles[str(doc_id)]


@app.get("/query/query_graph_nodes/")
async def query_graph_nodes(query_terms: List[str] = Query(None)):
    """
    Search in nodes of graphs for a query term
    @query_term: The query term
    @return: All timestamps for which the corresponding graph contains the query term
    """
    if not query_terms:
        return []
    query_terms = [x.lower() for x in query_terms]
    resulting_timestamps = set(timeline_dates)
    for term in query_terms:
        resulting_timestamps.intersection_update(query_label_to_graphs[term])

    return resulting_timestamps


@app.get("/query/suggest/{phrase}")
async def suggest_nodes(phrase: str = Query(None, max_length=40), limit: int = 5):
    """
    Suggest the most popular terms based on aggregates over all graphs
    @param phrase: A partial string to match nodes on.
    @param limit: How many nodes to return.
    @return: A list of nodes that match the phrase, sorted descending by importance.
    """

    suggestions = []
    for label in query_suggestions.keys():
        if phrase.lower() in label.lower():
            suggestions.append(label)

        if len(suggestions) >= limit:
            break

    return suggestions
