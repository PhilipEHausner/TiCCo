import argparse
from itertools import repeat
import re
import timeit
import typing
import pickle
import os

from nltk.corpus import stopwords
from spacy.tokens.doc import Doc as spacyDoc
from tqdm import tqdm
import spacy

import config
import documents.Documents as Documents


class FullSet(set):
    # Always returns True, as if every element is part of the set
    def __contains__(self, item):
        return True


class DocumentsCreator:
    """
    Takes documents as a json with "text" field where the text is tagged by Heideltime, and processes them resulting in
    a DocumentCollection. It extracts and processes the timestamps first, and then transforms the text into a bag of
    words model. For more information have a look at Documents.py.
    """
    # nlp: spacy.lang model
    # tag_start, tag_end: re patterns
    dict_up_to_x_chars: set
    disable_tqdm: bool
    output_path: str

    def __init__(self, args: argparse.Namespace, model: str = None) -> None:
        """
        Initialize spacy model and compile regular expressions used for detection of TIMEX3 tags.
        @param args: The command line arguments given by the user
        @param model: Specific spacy model can be given
        """

        self.documentCollectionAlreadyGiven = args.dcolload
        if self.documentCollectionAlreadyGiven:
            self.documentCollectionPath = args.data
            return

        print("Load Spacy Model.")
        start = timeit.default_timer()
        # if model is specified
        if model:
            self.nlp = spacy.load(model)
        elif args.hlang.lower() == "german":
            self.nlp = spacy.load("de_core_news_md")
        elif args.hlang.lower() == "english":
            self.nlp = spacy.load("en_core_web_md")
        end = timeit.default_timer()
        print("Loaded Spacy Model in", end - start, "seconds.")

        self.dict_up_to_x_chars = self.__load_language_dict__(args.hlang, 4)

        # Sentencizer needs to be first part of pipeline
        self.nlp.add_pipe(self.nlp.create_pipe('sentencizer'), first=True)

        # Merge entities to one token
        self.nlp.add_pipe(spacy.pipeline.merge_entities)

        # Extend the list of stop words
        self.nlp.vocab['\n'].is_stop = True
        # Insert NLTK stop words
        for stopword in stopwords.words(args.hlang.lower()):
            self.nlp.vocab[stopword].is_stop = True

        # Only words that are a certain pos tag are taken into account
        self.possible_pos_tags = ["ADJ", "NOUN", "PROPN", "VERB"]

        # Compile the necessary regular expressions
        self.tag_start = re.compile(r"<[^/].*?>")
        self.tag_end = re.compile(r"</.*?>")

        self.disable_tqdm = args.disable_tqdm
        self.output_path = args.output

    @staticmethod
    def __load_language_dict__(lang: str, max_chars: int) -> set:
        """
        Load a dictionary containing words of the respective language.
        @param lang: language of the dictionary
        @param max_chars: only words up to this number of chars are loaded
        @return: the dictionary
        """
        if lang.lower() == "german":
            with open(config.GERMAN_DICT_PATH, "r", encoding="ISO-8859-1") as f:
                temp = f.read()
                res = set([item for item in temp.split("\n") if len(item) <= max_chars])
        elif lang.lower() == "english":
            with open(config.ENGLISH_DICT_PATH, "r", encoding="ISO-8859-1") as f:
                temp = f.read()
                res = set([item for item in temp.split("\n") if len(item) <= max_chars])
        else:
            res = FullSet
        return res

    def __parse_HeidelTimeTags__(self, document: dict) -> typing.Optional[Documents.Document]:
        """
        Finds TIMEX3 tags in document. Creates Document object from input document and found temporal annotations.
        The created Document object has no sentences yet, since text segmentation is not done yet.
        @param document: The document to be processed
        @return: Document object
        """
        annotations = []
        text = document["text"]

        # In every step find start tag and associated end tag
        # Store annotations
        try:
            match = re.search(self.tag_start, text)
        except Exception as e:
            print("DocumentsCreator:", e)
            print('Is the input data for HeidelTimedSpacy in the right format?')
            return None
        try:
            # While we find a new start tag
            while match:
                # extract tag and delete it in the text
                temp_tuple = (match.span()[0], match[0][1:-1])
                text = text[:match.span()[0]] + text[match.span()[1]:]
                date_start_idx = match.span()[0]

                # Same for end tag
                match = re.search(self.tag_end, text)
                annotations.append(Documents.TemporalAnnotation.from_HeidelTimeTag(temp_tuple[0], match.span()[0],
                                                                                   temp_tuple[1]))

                date_end_idx = match.span()[0]
                text = text[:match.span()[0]] + text[match.span()[1]:]

                # replace text by zeros, s.t. length stays constant
                text = text[:date_start_idx] + "0" * (date_end_idx - date_start_idx) + text[date_end_idx:]

                match = re.search(self.tag_start, text)
        except Exception as e:
            print("DocumentsCreator:", e)
            print('Is there the same amount of start and end tags?')
            return None

        document["text"] = text

        result = Documents.Document.from_json(document, annotations)

        return result

    def __spacy_processing__(self, document: Documents.Document, entity_only_lastname: bool) \
            -> typing.Optional[Documents.Document]:
        """
        Processing with SpaCy: Sentence segmentation, named entity recognition, stop word removal, etc.
        @param document: Document object
        @param entity_only_lastname: If true only the lastname of all entities of type Person is stored
        @return: Document object with segmented sentences (sentences are modelled as BoW)
        """
        if not document:
            return None

        spacy_doc: spacyDoc
        spacy_doc = self.nlp(document.text)

        annotations_start_indices = set([a.start for a in document.annotations])

        for sent in spacy_doc.sents:
            # ignore sentences that have 200 or more words (those are probably lists)
            if len(sent) > 200:
                sentence = Documents.Sentence(sent.start_char, sent.end_char, document)
                document.addSentence(sentence)
                continue

            # Create new sentence
            sentence = Documents.Sentence(sent.start_char, sent.end_char, document)

            len_sentence = len(sent)

            # is a word tagged with a timestamp found?
            found_tag = False

            # Take track of indices
            tag_end_index = 0

            for wcount, word in enumerate(sent):

                # Last word was tagged with a timestamp
                if found_tag:

                    # End of sentence
                    if wcount + 1 == len_sentence:

                        # Current word has different (or no) tag
                        if tag_end_index < word.idx:
                            found_tag = False

                            # Current word has new tag
                            if word.idx in annotations_start_indices:
                                annotation = document.getAnnotationByStartIdx(word.idx)
                                w = Documents.Word.from_spacyToken(word, True, sentence, annotation.timestamp)
                                sentence.addAnnotatedWord(w, annotation)
                                # it is the end of the sentence, but this needs to be done, so the second half of the
                                # function is not called
                                found_tag = True

                    # Not end of sentence, and word has not the same tag as the word before
                    # -> Process word below
                    elif tag_end_index < word.idx:
                        found_tag = False

                    # Not end of sentence, but word belongs to same tag as the word before
                    else:
                        w.appendLemma(word.lemma_)

                if not found_tag:

                    # Word is start of timestamp tag
                    if word.idx in annotations_start_indices:
                        found_tag = True
                        annotation = document.getAnnotationByStartIdx(word.idx)
                        w = Documents.Word.from_spacyToken(word, True, sentence, annotation.timestamp)
                        sentence.addAnnotatedWord(w, annotation)

                    # Word is regular and untagged (base case)
                    else:

                        if not (word.is_stop or word.is_punct):

                            # if we only want to process lastname of persons
                            if entity_only_lastname and word.ent_type_ == "PER":
                                temp = word.lemma_.split(" ")
                                w = Documents.Word(temp[-1], word.ent_type_, False, sentence)
                                sentence.addWord(w)

                            # base case
                            else:
                                # if word.ent_type_ or len(word) > 4 or word.lemma_ in self.dict_up_to_x_chars:
                                if word.ent_type_ or word.pos_ in self.possible_pos_tags:
                                    w = Documents.Word.from_spacyToken(word, False, sentence)
                                    sentence.addWord(w)

            document.addSentence(sentence)

        return document

    @staticmethod
    def __set_word_lemmas_for_timestamps__(document: Documents.Document) -> Documents.Document:
        """
        Transform the lemma of words that represent a timestamp to a uniform representation
        @param document: Document object
        @return: Document object with changed lemmas for words representing a timestamp
        """
        for sentence in document.sentences:
            for word in sentence.words:
                if word.is_timestamp:
                    word.lemma = str(word.timestamp)
        return document

    def parse_documents(self, documents: typing.List[dict], entity_only_lastname: bool = False) \
            -> Documents.DocumentCollection:
        """
        Parses TIMEX3 tags from document field "text" and processes all documents, such that all DocumentCollection
        object is returned (see Documents.py).
        @param documents:
        @param entity_only_lastname:
        @return:
        """
        if self.documentCollectionAlreadyGiven:
            with open(self.documentCollectionPath, "rb") as f:
                data = pickle.load(f)
                print("Document Collection loaded.")
                return data

        print("Start creating Document Collection.")
        start = timeit.default_timer()
        documents = list(map(self.__parse_HeidelTimeTags__, tqdm(documents, disable=self.disable_tqdm)))
        documents = list(map(self.__spacy_processing__, tqdm(documents, disable=self.disable_tqdm),
                             repeat(entity_only_lastname)))
        documents = list(map(self.__set_word_lemmas_for_timestamps__, tqdm(documents, disable=self.disable_tqdm)))
        documents = Documents.DocumentCollection(documents)
        end = timeit.default_timer()

        if self.output_path:
            with open(os.path.join(self.output_path, "document_collection.pickle"), "wb") as f:
                pickle.dump(documents, f)

        print("Finished creating Document Collection in", end - start, "seconds.")

        return documents
