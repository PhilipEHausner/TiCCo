import typing
import argparse
import os

import parser.jsonparser as jsonparser
import parser.heideltimeparser as heideltimeparser


def readAndHeidelTimeJson(path: str, args: argparse.Namespace) -> typing.List[dict]:
    """
    Reads input document json, preprocessed documents, and tags them with HeidelTime.
    @param path: path to input file
    @param args: arguments created by argparser that can be passed via command line arguments
    @return: json with processed documents
    """
    if args.hskip:
        print("Skipping HeidelTime processing of documents.")
        return [{}]
    if args.hload:
        print("Loaded documents already preprocessed with HeidelTime.")
        return jsonparser.loadJson(path)

    # standard case: data has to be loaded, preprocessed and processed by HeidelTime
    data = jsonparser.parseJson(path, args.output)
    settings = heideltimeparser.createHeidelTimeSettings(args.hlang, args.htype)
    data = heideltimeparser.heidelTimeParseJson(data, settings, disable_tqdm=args.disable_tqdm)
    heideltimeparser.storeProcessedDocuments(data, os.path.join(args.output, "heideltimed_documents.json"))

    return data
