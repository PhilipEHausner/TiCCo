import typing
import json

import pymongo


def create_database(files: typing.List[str], database_name: str) -> None:
    """
    Read in a list of json files that are then stored in a MongoDB.
    ATTENTION: THE DATABASE WITH THE NAME database_name IS DROPPED IN THIS PROCESS.
    @param files: list of jsons containing time-centric graphs.
    @param database_name: Name the database should have.
    @return: Nothing
    """
    dbClient = pymongo.MongoClient("mongodb://localhost:27017/")
    dbClient.drop_database(database_name)
    database = dbClient[database_name]
    for file in files:
        with open(file, "r") as f:
            data = json.load(f)
        mongo_data = []
        for date, graph in data.items():
            mongo_data.append(
                {
                    "_id": date,
                    "nodes": graph["nodes"],
                    "edges": graph["edges"]
                }
            )
        database.graphs.insert_many(mongo_data)
        del data, mongo_data


create_database(["../1861_small.json", "../1862_small.json", "../1863_small.json", "../1864_small.json",
                 "../1865_small.json"], "testdb")
