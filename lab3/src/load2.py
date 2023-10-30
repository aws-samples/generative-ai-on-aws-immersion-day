"""Custom HTML parser and Loader"""

import re
import glob
from html_parser_ex import BSHTMLLoaderEx

from langchain.text_splitter import RecursiveCharacterTextSplitter


def to_san(fname):
    return fname.split("/")[-1].split(".")[0]


def list_14A(folder):
    if folder[-1] != "/":
        folder = folder + "/"
    return [to_san(f) for f in glob.iglob(folder + "*.html")]


def clean_html(s):
    s = s.replace("\xa0", " ")  # no-break space
    return s


def clean_text(s):
    s = "".join(c for c in s if ord(c) < 128)  # remove special chars
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def like_page_number(text):
    """Match standalone one or two digit number"""
    return re.match(r"^(\d+){1,2}\.?$", text)


def load_14A(folder, san):
    doc_path = folder + san + ".html"
    print("Loading:", doc_path)

    # loader = BSHTMLLoader(doc_path)
    loader = BSHTMLLoaderEx(doc_path, bs_kwargs={"features": "html.parser"})

    data = loader.load()

    # Clean entire HTML
    data[0].page_content = clean_html(data[0].page_content)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1400, chunk_overlap=0)

    docs = text_splitter.split_documents(data)

    for i, doc in enumerate(docs):
        doc.page_content = clean_text(doc.page_content)
        doc.metadata["passage_id"] = i
        # print('doc len',len(doc.page_content))

    # Filter page numbers
    docs = [doc for doc in docs if not like_page_number(doc.page_content)]

    print(f"Now you have {len(docs)} short passages")

    return docs
