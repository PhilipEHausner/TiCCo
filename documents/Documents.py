from __future__ import annotations
import typing

from spacy.tokens.token import Token

from documents.Timestamps import Timestamp


class Word:
    """
    Storage object for words.
    """
    next_idx: int = 0
    belongs_to: Sentence
    ent_type: str
    idx: int
    is_timestamp: bool
    lemma: str
    timestamp: typing.Optional[Timestamp]

    def __init__(self, lemma: str, ent_type: str, is_timestamp: bool, sentence: Sentence, timestamp: Timestamp = None) \
            -> None:
        self.idx = Word.next_idx
        Word.next_idx += 1
        self.belongs_to = sentence
        self.ent_type = ent_type
        self.is_timestamp = is_timestamp
        self.lemma = lemma
        if is_timestamp:
            if timestamp is None:
                print("In Word.__init()__: Timestamp missing.")
                self.timestamp = Timestamp()
            else:
                self.timestamp = timestamp
        else:
            self.timestamp = None

    @classmethod
    def from_spacyToken(cls, token: Token, is_timestamp: bool, sentence: Sentence, timestamp: Timestamp = None) -> Word:
        return cls(token.lemma_, token.ent_type_, is_timestamp, sentence, timestamp)

    def appendLemma(self, lemma: str):
        self.lemma = self.lemma + " " + lemma


class TemporalAnnotation:
    """
    Stores temporal information together with start and end character. Since it is always part of a sentence or
    document, document ID is not stored, but given only implicitly.
    """
    start: int
    end: int
    timestamp: Timestamp

    def __init__(self, start: int, end: int, timestamp: Timestamp) -> None:
        self.start = start
        self.end = end
        self.timestamp = timestamp

    @classmethod
    def from_HeidelTimeTag(cls, start: int, end: int, timestamp: str) -> TemporalAnnotation:
        return cls(start, end, Timestamp.from_HeidelTimeTag(timestamp))

    def __eq__(self, other):
        if isinstance(other, TemporalAnnotation):
            return (self.start, self.end, self.timestamp) == (other.start, other.end, other.timestamp)


class Sentence:
    """
    Sentences are BoW models that store words and annotations within the sentence structure. Annotations are only
    indices that indicate which word in the words list is annotated.
    """
    belongs_to: Document
    num_words: int
    sent_start: int
    sent_end: int
    words: typing.List[Word]
    annotations: typing.Dict[int]

    def __init__(self, start_idx: int, end_idx: int, document: Document):
        self.belongs_to = document
        self.num_words = 0
        self.sent_start = start_idx
        self.sent_end = end_idx
        if end_idx < start_idx:
            print("Warning in Documents.Sentence: End index before start index.")
        self.words = []
        self.annotations = {}

    def addWord(self, word: Word) -> None:
        self.num_words += 1
        self.words.append(word)

    def addAnnotatedWord(self, word: Word, annotation: TemporalAnnotation) -> None:
        self.addWord(word)
        self.annotations[self.num_words-1] = annotation


class Document:
    """
    Stores a list of sentences and annotations as well as the text and metadata. The procedure using from_json for this
    object is to first create an instance containing the metadata and text, and afterwards doing text processing and
    filling the annotations and sentences step by step. Alternatively, annotations and sentences can be created before
    and the base constructor can be used.
    """
    idx: int
    ref_date: str = None
    ref_id: int = None
    text: str
    annotations: typing.List[TemporalAnnotation]
    sentences: typing.List[Sentence]

    def __init__(self, idx: int, text: str, ref_date: str = None, ref_id: int = None,
                 annotations: typing.List[TemporalAnnotation] = None, sentences: typing.List[Sentence] = None) -> None:
        self.idx = idx
        self.text = text
        self.ref_date = ref_date
        self.ref_id = ref_id
        if annotations:
            self.annotations = annotations
        else:
            self.annotations = []
        if sentences:
            self.sentences = sentences
        else:
            self.sentences = []

    @classmethod
    def from_json(cls, data: dict, annotations: typing.List[TemporalAnnotation] = None) -> Document:
        if "ref_date" in data.keys():
            ref_date = data["ref_date"]
        else:
            ref_date = None
        if "ref_id" in data.keys():
            ref_id = data["ref_id"]
        else:
            ref_id = data["id"]

        return cls(data["id"], data["text"], ref_date, ref_id, annotations)

    def addSentence(self, sentence: Sentence) -> None:
        self.sentences.append(sentence)

    def getAnnotationByStartIdx(self, idx: int) -> TemporalAnnotation:
        res = None
        for ann in self.annotations:
            if ann.start == idx:
                res = ann
                break
        return res


class DocumentCollection:
    """
    Storage object for documents.
    """
    documents: typing.List[Document]

    def __init__(self, documents: typing.List[Document] = None):
        if documents:
            self.documents = documents
        else:
            self.documents = []
