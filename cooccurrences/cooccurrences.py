import argparse
import typing
import collections
import itertools
import sys

import documents.Documents as Documents
import documents.Timestamps as Timestamps


def extract_timecentric_cooccurrences_from_collection(docs: Documents.DocumentCollection, args: argparse.Namespace) \
        -> typing.DefaultDict[Timestamps.Timestamp, list]:
    """
    Extract time-centric co-occurrences as described in the paper for a list of documents.
    @param docs: The documents from which time-centric co-occurrences are extracted.
    @param args: arguments from command-line arguments, i.e., start and end year as well as window size
    @return: A dictionary of time-centric co-occurrences with timestamps as keys
    """
    # Unpack inputs
    window_size = args.window_size
    start_year = args.start_year
    end_year = args.end_year

    # dictionary in which results are stored
    timecentric_coocs = collections.defaultdict(list)

    count = 1
    max_count = len(docs.documents)
    for doc in docs.documents:
        print("Document:", count, "/", max_count, end="\n")
        count += 1
        sys.stdout.flush()
        sentences = doc.sentences

        for source_sentID in range(len(sentences)):
            # unpack sentence information
            source_sentence = sentences[source_sentID]
            annotations = source_sentence.annotations
            startID = max(0, source_sentID - window_size)
            endID = min(len(sentences) - 1, source_sentID + window_size)
            # Iterate over all words that are annotated as timestamp in the sentence
            for wordID in annotations.keys():
                # If the date is None or not within the specified time frame, it is not processed for co-occurrences
                current_year = annotations[wordID].timestamp.year
                if current_year is None or current_year < start_year or current_year > end_year:
                    continue
                # All combinations of words in the window around the timestamp are co-occurrences
                target_sentences = sentences[startID:endID+1]
                coocs = list(itertools.combinations([word for sent in target_sentences for word in sent.words], 2))
                timecentric_coocs[annotations[wordID].timestamp].extend(coocs)

    return timecentric_coocs


def unify_timecentric_cooccurrences(timecentric_cooccurrences: typing.List[typing.DefaultDict[Timestamps.Timestamp,
                                                                                              list]]):
    """
    Take a list with (timestamp, co-occurrences) pairs, s.t. every timestamp occurs only once, and unify all
    time-centric co-occurrences.
    @param timecentric_cooccurrences: list of dicts with (timestamp, co-occurrences)- pairs
    @return: Unified list, s.t. every timestamp occurs only once
    """
    result = collections.defaultdict(list)
    for item in timecentric_cooccurrences:
        for timestamp, coocs in item.items():
            result[timestamp].extend(coocs)
    return result


