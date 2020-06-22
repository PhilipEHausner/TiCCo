import typing
import multiprocessing
import timeit
import re
import json

import tqdm
import python_heideltime

from documents.Timestamps import Timestamp


def createHeidelTimeSettings(language: str, doctype: str) -> typing.Dict[str, str]:
    """
    Creates a dictionary suitable for HeidelTime functionality.
    @param language: Language of documents
    @param doctype: Type of document, e.g., NARRATIVES
    @return:
    """
    result = dict()
    result["lang"] = language
    result["doctype"] = doctype
    return result


def heidelTimeParseJson(data: typing.List[dict], settings: typing.Dict[str, str], disable_tqdm: bool = False) \
        -> typing.List[dict]:
    """
    Parses a list of documents with HeidelTime.
    @param data: json file (dict), needs field "text"
    @param settings: HeidelTime settings, created by createHeidelTimeSettings
    @param disable_tqdm: disable tqdm bar
    @return: processed data, i.e., field "text" has now text including TIMEX3 tags
    """
    # create (doc, settings) tuple for multiprocessing (hence, we only need to pass one argument)
    temp_data = [(doc, settings) for doc in data]
    print("Start processing documents with HeidelTime.")
    start = timeit.default_timer()

    # Process each document with HeidelTime
    with multiprocessing.Pool() as p:
        data = list(tqdm.tqdm(p.imap(_parseDocWithHeidelTime, temp_data), disable=disable_tqdm, total=len(data)))

    # HeidelTime creates a header and footer that we do not need for further processing
    for i in range(len(data)):
        data[i] = _removeHeaderAndFooterFromHeidelTimedDoc(data[i])

    print("Documents in total:", len(data), flush=True)
    # Remove documents that have no timestamp at all
    data = _removeDocumentsWithoutTimestamps(data)
    print("Documents with timestamp:", len(data), flush=True)

    end = timeit.default_timer()
    print("Finished processing documents in", end - start, "seconds.")
    return data


def storeProcessedDocuments(docs: list, output_path: str) -> None:
    with open(output_path, "w") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)


# function for multiprocessing
def _parseDocWithHeidelTime(data) -> dict:
    """
    Parses a single document with HeidelTime. Suitable for multiprocessing.
    @param data: Tuple with (document, settings)
    @return: Processed document
    """
    # unpack input tuple
    document = data[0]
    settings = data[1]

    # initialize the HeidelTime parser
    parser = python_heideltime.Heideltime()
    parser.set_language(settings["lang"])
    parser.set_document_type(settings["doctype"])
    if "ref_date" in document.keys():
        parser.set_document_time(document["ref_date"])

    # parse document
    try:
        document["text"] = parser.parse(document["text"])
    except Exception as e:
        print("Error when parsing documents with HeidelTime:", e)
    return document


def _removeHeaderAndFooterFromHeidelTimedDoc(doc: dict) -> dict:
    """
    HeidelTime creates a header and footer. This function removes them.
    @param doc: The document header and footer are removed from
    @return: The document without header and footer
    """
    doc["text"] = doc["text"].replace('<?xml version="1.0"?>\n<!DOCTYPE TimeML SYSTEM "TimeML.dtd">\n<TimeML>\n', '')
    doc["text"] = doc["text"].replace('\n</TimeML>\n\n', '')
    return doc


def _removeDocumentsWithoutTimestamps(docs: list) -> list:
    """
    Check for each document if a timestamp is present, only keep documents with timestamps that have a year included
    @param docs: A list of documents processed by HeidelTime
    @return: A list of documents for which each has at least one timestamp
    """
    # We check for each document if we can find a TIMEX3 tag (we only check for <...>, since all < and > were removed
    # from the text beforehand. We only check for the end tag as well to do some kind of sanity check.
    tag_start = re.compile(r"<[^/].*?>")
    result = []
    count, max_count = 1, len(docs)
    for doc in docs:
        print("Removal of documents without valid timestamp:", count, "/", max_count, end="\n", flush=True)
        count += 1
        tags = re.findall(tag_start, doc["text"])
        for tag in tags:
            if Timestamp.from_HeidelTimeTag(tag).year:
                result.append(doc)
                break
    return result
