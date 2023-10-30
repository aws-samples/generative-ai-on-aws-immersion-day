"""Load pre-computed textual 14A paragraphs"""

import glob
from langchain.docstore.document import Document
import utils_os


def to_san(fname):
    return fname.split("/")[-1].split(".")[0]


def list_14A(folder):
    if folder[-1] != "/":
        folder = folder + "/"
    return list(set(to_san(f) for f in glob.iglob(folder + "*.txt")))


def load_14A(folder, san):
    print(f"Loading: {folder}{san}.*.txt")

    docs = []
    for i, fname in enumerate(glob.iglob(folder + san + "*.txt")):
        docs += (
            Document(
                page_content=utils_os.read_text(fname),
                metadata={"source": fname, "title": None, "passage_id": i},
            ),
        )

    print(f"Now you have {len(docs)} short textual passages")

    return docs
