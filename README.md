## Installation Instructions
The current installation instructions have been tested against an
empty Anaconda Python environment, with `python3.7`.

Install requirements in `requirements.txt` with
```bash
python3 -m pip install -r requirements.txt
```
To avoid any conflicts with existing packages, ideally create a new virtual environment for this tool.

Additionally, the `nltk.stopwords` and spaCy's `en_core_web_md` or `de_core_news_md` for German, respectively, are required.
These can be installed with
```bash
python3 -m nltk.downloader stopwords
python3 -m spacy download en_core_web_md
python3 -m spacy download de_core_news_md
```

We further require the [`python_heideltime`](https://github.com/PhilipEHausner/python_heideltime) wrapper,
which also details the installation instructions in a similar manner, and includes the download and setup of the HeidelTime library.

Lastly, the runtime requires an available MongoDB host at `mongodb://localhost:27017/`.
If you do not have MongoDB installed already, see the [official MongoDB docs](https://docs.mongodb.com/manual/installation/).
The connection port is set under `database/database.py`, as well as `api/API.py`.
This is important if your MongoDB is running under a port different from the default setting.

## Input Documents and Graph Generation

### Input Format
For the sake of reference and reproducibility, we have included a small test dataset to demonstrate the input format,
both for Germand and English data. They can be found in `test_files/`. Note that each JSON file represents an *entire collection*.

Requests for the full dataset used in our evaluation can be made to [hausner@informatik.uni-heidelberg.de](mailto:hausner@informatik.uni-heidelberg.de).

A single document in the JSON input file should look like this:
```python3
{
    "article_title": "The Article Title",
    "title": "The Current Section Title (Can be the same as article_title)",
    "subtitle": "Subsection title",
    "text": "The text of the current part",
    "url": "http://source-of-document.com/article/section"
}
```

### Processing a Collection
To generate the time-centric co-occurrence graphs, a minimal call should look like this:
```bash
python3 main.py -d input/file.json -o output_folder/
```

The full available options can be inspected with
```bash
python3 main.py --help
```
which outputs
```
  -h, --help            show this help message and exit
  -d DATA, --data DATA  Relative or absolute file location for input JSON
                        file.
  -hlang LANGUAGE       Document language. Default: GERMAN
  -htype TYPE           Type of document. Default: NARRATIVES
  -o PATH, --output PATH
                        Relative or absolute directory path where the result
                        is stored.
  -f Folder, --folder Folder
                        Folder where intermediate results are stored, or
                        retrieved.
  -hskip, --skipHeidelTime
                        Skips the tagging with HeidelTime if a further
                        processed file exists.
  -hload, --loadHeidelTime
                        Load a file already tagged with HeidelTime (specified
                        with -d).
  -dcolload, --loadDocumentCollection
                        Load a pickle file containing a already processed
                        Document Collection (specified with-d).
  -w SIZE, --window_size SIZE
                        Window size for co-occurrence extraction in each
                        direction, s.t. total window size equals 2*w+1.
                        Default: 2
  -start YEAR, --start-year YEAR
                        Minimal year for which a time-centric co-occurrence
                        network is constructed.
  -end YEAR, --end-year YEAR
                        Maximal year for which a time-centric co-occurrence
                        network is constructed.
  --disable-tqdm BOOL   Disable progress bars created by tqdm for
                        multiprocessing.

```

## Running the User Interface
During the generation of time-centric co-occurrence graphs, a file named `indexed_documents.json` is created in the output folder. In `api/config.py` specify the path to this file in the variable `INDEXED_DOCUMENTS_PATH`.

To start the user interface, `cd` into the `api/` folder, and run
```bash
uvicorn API:app --reload
```
The website will be served to `http://localhost:8000`.
To inspect the underlying API structure, 
you can view the API documentation auto-generated by fastAPI under `http://localhost:8000/docs`.

## Reference
Disclaimer: This work is currently under review at the 29th ACM International Conference on Information and Knowledge Management (CIKM2020).

If you intend to use this work in your research, please cite a preliminary version of this work:
```bibtex
@unpublished{Hausner20Ticco
    author = "Philip Hausner and Dennis Aumiller and Michael Gertz",
    title = "TiCCo: Time-Centric Content Exploration",
    year = "2020",
    note = "submitted to CIKM'20",
}
```

For any further questions, reach out to [Philip Hausner](mailto:hausner@informatik.uni-heidelberg.de) or
[Dennis Aumiller](mailto:Aumiller@informatik.uni-heidelberg.de).
