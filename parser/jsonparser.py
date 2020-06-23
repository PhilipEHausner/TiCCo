"""
Preprocess JSON files, e.g., to remove certain undesirable characters, or to alter date specifications (which needs
special attention for every data set).
"""
import json
import typing
import os


def parseJson(filepath: str, output_folder: str) -> typing.List[dict]:
    """
    Read and preprocess document input json, e.g., removal of certain characters.
    @param filepath: path to json file
    @param output_folder: The folder in which the result is stored
    @return: Read and processed json file.
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    # sanity check: "text" field is absolutely necessary
    for doc in data:
        if "text" not in doc.keys():
            raise KeyError("Key \"text\" not in input json file.")

    # add a unique index to each document
    data, output_data = _jsonAddIndex(data)

    # save the indexed files in a separate json for later visualization in the web api
    output_file = os.path.join(output_folder, "indexed_documents.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    data = _preprocessJson(data)

    return data


def storeJson(data: typing.List[dict], filepath: str) -> None:
    """
    Write a json file
    @param data: json file that needs to be stored
    @param filepath: output path
    """
    with open(filepath, "w") as f:
        json.dump(data, f)


def loadJson(filepath: str) -> typing.List[dict]:
    """
    Load a json file
    @param filepath: input path
    @return: json file
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    return data


def _preprocessJson(data: typing.List[dict]) -> typing.List[dict]:
    """
    Necessary preprocessing steps. At the moment, this removes certain characters that cannot be processed in later
    steps, e.g., "<" and ">", since they conflict with the design of TIMEX3 tags.
    @param data:
    @return:
    """
    char_replace = [("&", " "), ("<", " "), (">", " "), (r"\u0007", ""), (r"\b", ""), ("–", "-")]
    for d in data:
        for y0, y1 in char_replace:
            d["text"] = d["text"].replace(y0, y1)
    return data


def _jsonAddIndex(data: typing.List[dict]) -> (typing.List[dict], typing.Dict[int, dict]):
    """
    Adds an index to each document in the json list.
    @param data: Input document json
    @return: Input data with additional field "id" which stores a unique ID for each document
    """
    curr_index = 1
    output_data = {}
    for d in data:
        output_data[curr_index] = d
        d["id"] = curr_index
        curr_index += 1
    return data, output_data
