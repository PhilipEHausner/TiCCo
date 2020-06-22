import argparse
import os


def createParser() -> argparse.Namespace:
    """
    Creates a parser for command line arguments.
    @return: The argparser
    """
    parser = argparse.ArgumentParser(prog="TimeCentricCooccurrenceGraphCreator",
                                     description="This program takes a JSON file with fields \"text\", and optionally "
                                                 "\"ref_date\" (as \"YYYY-MM-DD\") as reference date for HeidelTime "
                                                 "as well as \"ref_id\" if every document has its own ID. The output "
                                                 "is a set of time-centric co-occurrence graphs. HeidelTime arguments "
                                                 "are explained in the HeidelTime Standalone Manual.")

    parser.add_argument("-d", "--data", required=True, help="Relative or absolute file location for input JSON file.")

    parser.add_argument("-hlang", type=str, default="GERMAN", help="Document language. Default: GERMAN",
                        choices=["ENGLISH", "GERMAN", "DUTCH", "ENGLISHCOLL", "ENGLISHSCI", "SPANISH", "ITALIAN",
                                 "ARABIC", "VIETNAMESE", "FRENCH", "CHINESE", "RUSSIAN", "CROATIAN", "PORTUGUESE",
                                 "ESTONIAN"], metavar="LANGUAGE")

    parser.add_argument("-htype", type=str, default="NARRATIVES", help="Type of document. Default: NARRATIVES",
                        choices=["NARRATIVES", "NEWS", "COLLOQUIAL", "SCIENTIFIC"], metavar="TYPE")

    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Relative or absolute directory path where the result is stored.",
                        metavar="PATH")

    parser.add_argument("-f", "--folder", type=str, required=True, dest="temp_folder",
                        help="Folder where intermediate results are stored, or retrieved.",
                        metavar="Folder")

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument("-hskip", "--skipHeidelTime", action="store_true", dest="hskip", default=False,
                        help="Skips the tagging with HeidelTime if a further processed file exists.")
    group1.add_argument("-hload", "--loadHeidelTime", action="store_true", dest="hload", default=False,
                        help="Load a file already tagged with HeidelTime (specified with -d).")
    group1.add_argument("-dcolload", "--loadDocumentCollection", action="store_true", dest="dcolload", default=False,
                        help="Load a pickle file containing a already processed Document Collection (specified with"
                             "-d).")

    parser.add_argument("-w", "--window_size", type=int, required=True,
                        help="Window size for co-occurrence extraction in each direction, s.t. total window size "
                             "equals 2*w+1.", metavar="SIZE")

    parser.add_argument("-start", "--start-year", type=int, default=-float("Inf"), dest="start_year",
                        help="Minimal year for which a time-centric co-occurrence network is constructed.",
                        metavar="YEAR")

    parser.add_argument("-end", "--end-year", type=int, default=float("Inf"), dest="end_year",
                        help="Maximal year for which a time-centric co-occurrence network is constructed.",
                        metavar="YEAR")

    parser.add_argument("--disable-tqdm", type=bool, default=False, dest="disable_tqdm",
                        help="Disable progress bars created by tqdm for multiprocessing.",
                        metavar="BOOL")

    args = parser.parse_args()

    # some precautions for path management
    args.data = os.path.abspath(args.data)
    args.output = os.path.abspath(args.output)
    args.temp_folder = os.path.abspath(args.temp_folder)

    # check if input file exists
    if not os.path.isfile(args.data):
        print("Input file is not found.")
        raise FileNotFoundError

    # create output directories
    try:
        output_dir = os.path.dirname(args.output)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.exists(args.temp_folder):
            os.mkdir(args.temp_folder)
    except Exception as e:
        print("Output or intermediate data folder cannot be created.")
        print(e)

    # if dcolload is true, hskip has to be also true
    if args.dcolload:
        args.hskip = True

    return args
