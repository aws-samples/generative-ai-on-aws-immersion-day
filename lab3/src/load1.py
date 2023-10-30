"""Standard HTML Loader"""

import re


from langchain.document_loaders import BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def clean_text(s):
    s = s.replace("\xa0", " ")  # no-break space
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def load_html(doc_path):
    print("Loading", doc_path)
    loader = BSHTMLLoader(doc_path)

    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1600, chunk_overlap=200)

    docs = text_splitter.split_documents(data)

    for i, doc in enumerate(docs):
        doc.page_content = clean_text(doc.page_content)
        doc.metadata["passage_id"] = i

    print(f"Now you have {len(docs)} short passages")

    return docs
