import streamlit as st
import streamlit.components.v1 as components
import yaml
from typing import Any, Iterable, List
from abc import ABC, abstractmethod
import sys

sys.path.append("../src/")
import langchain_qa
import re
import hashlib


from doc_source import DocSource, OpensearchTextFrags, OpenSearchHTML, KendraHTML
import utils_text, utils_os
import utils_14a_ext

with open("../src/config.yml", "r") as file:
    config = yaml.safe_load(file)


# task
_TASK_RE = False


@st.cache_resource
def check_env():
    langchain_qa.validate_environment()


@st.cache_data
def list_llm_models():
    return ["FLAN-T5-XL"]


@st.cache_resource
def list_doc_source_instances():
    return [OpensearchTextFrags(config), OpenSearchHTML(config), KendraHTML(config)]


@st.cache_data
def list_doc_sources():
    return [str(x) for x in list_doc_source_instances()]


@st.cache_data
def list_embedding_models():
    return ["GPT-J"]


# @st.cache_resource
def to_doc_source(doc_source_str: str) -> DocSource:
    """String to class instance"""
    return next(i for i in list_doc_source_instances() if str(i) == doc_source_str)


@st.cache_data
def list_14A(doc_source_nm):
    doc_source = to_doc_source(doc_source_nm)
    return doc_source.list_14A()


# @st.cache_data
def load_14A(doc_source_nm, model, embed_model, san):
    doc_source = to_doc_source(doc_source_nm)
    return doc_source.load_14A(model, embed_model, san)


# @st.cache_data
def recommended_k(doc_source_nm):
    doc_source = to_doc_source(doc_source_nm)
    return doc_source.recommended_k()


@st.cache_data
def list_questions():
    return [
        "How old is Catherine J. Randall?",
        "How old is Phillip W. Webb?",
        "What is Angus R. Cooper, III's current position and what is the name of the organization he/she currently works for?",
        "What year did Robert D. Powers joined the board of directors?",
        "What committees is Catherine J. Randall a member of?",
        "What is Phillip W. Webb's current position and what is the name of the organization he/she currently works for?",
        "Ask your question",
    ]


@st.cache_resource
def create_qa_chain(model, verbose=False):
    if model == "FLAN-T5-XL":
        llm = langchain_qa.sagemaker_endpoint(config["llm"]["t5_endpoint"])
    else:
        assert False
    print("Make QA chain for", model)
    return langchain_qa.chain_qa(llm, verbose=verbose)


def markdown(text, answer, fg_color=None, bg_color=None):
    """
    The exact match of answer may not be the possible.
    Split the answer into tokens and find most compact span
    of the text containing all the tokens. Highlight them.
    """
    tokens = utils_text.tokenize(answer)
    print("highlight", tokens)

    spans = utils_text.spans_of_tokens_ordered(text, tokens)
    if not spans:
        spans = utils_text.spans_of_tokens_compact(text, tokens)

    output, k = "", 0
    for i, j in spans:
        output += text[k:i]
        k = j

        if bg_color:
            output += (
                f'<span style="background-color:{bg_color};">' + text[i:j] + "</span>"
            )
        else:
            output += f":{fg_color}[" + text[i:j] + "]"

    output += text[k:]
    return output


def main():

    check_env()

    st.title("SEC 14A Question & Answer")
    st.write(f"streamlit version: {st.__version__}")

    model = st.selectbox("Select LLM", list_llm_models())
    embed_model = st.selectbox("Select Embedding Model", list_embedding_models())

    chain_qa = create_qa_chain(model, verbose=True)

    doc_source_nm = st.selectbox("Select documents source", list_doc_sources())

    san = st.selectbox("Select 14A", list_14A(doc_source_nm))

    html = utils_os.read_text(config["corpus"]["path14A_html"] + san + ".html")
    components.html(html, height=400, scrolling=True)

    if (
        st.session_state.get("doc_source_nm", "") != doc_source_nm
        or st.session_state.get("san", "") != san
    ):

        st.empty()

        # Load vector store
        store = load_14A(doc_source_nm, model, embed_model, san)

        st.session_state["doc_source_nm"] = doc_source_nm
        st.session_state["san"] = san
        st.session_state["store"] = store
    else:
        store = st.session_state["store"]
        san = st.session_state["san"]

    query = st.selectbox("Select question", [""] + list_questions())
    if "Ask" in query:
        query = st.text_input(
            "Your Question: ", placeholder="Ask me anything ...", key="input"
        )
    if not query:
        return

    # cannot make objects hashable
    cache_key = f"{model},{san},{doc_source_nm},{query}"
    cache_hex = hashlib.md5(cache_key.encode("utf-8")).hexdigest()

    print("Hex:", model, san, doc_source_nm, query)
    print(cache_hex)
    if "cache" in st.session_state:
        print(st.session_state["cache"])
    if "cache" in st.session_state and st.session_state["cache"] == cache_hex:
        print("Same question again")
        return

    st.session_state["cache"] = cache_hex

    # This is PoC specific Task = Relation Extraction
    # as input use textual frags with Opensearch
    K = recommended_k(doc_source_nm)

    print("Q:", query)

    for attempt in range(4):
        try:
            response = langchain_qa.search_and_answer(
                store, chain_qa, query, k=K, doc_source_contains=san
            )
            answer = response["response"]
            break  # Success
        except Exception as e:
            print(e)
            st.spinner(text=type(e).__name__)
            if type(e).__name__ == "ValidationException" and K > 1:
                print("Retrying using shorter context")
                K -= 1
            elif type(e).__name__ == "ThrottlingException":
                print("Retrying")
            else:
                # continue
                raise e

    print("A:", answer)
    st.write(f"**Answer**: :green[{answer}]")

    highlight_green = answer
    highlight_red = None

    # Print the source of evidence
    for i, doc in enumerate(response["docs"]):

        markd = doc.page_content

        if highlight_green:
            if len(highlight_green) < 10:
                markd = markdown(markd, highlight_green, bg_color="#90EE90")
            else:
                markd = markdown(markd, highlight_green, fg_color="green")
        if highlight_red:
            markd = markdown(markd, highlight_red, fg_color="red")

        st.markdown(markd, unsafe_allow_html=True)

        source = doc.metadata.get("source", "n/a")
        passage = doc.metadata.get("passage_id", "n/a")
        score = doc.metadata.get("score", "n/a")
        st.markdown(
            f"**Reference**:\n*Source = {source} | Passage = {passage} | K = {K} | Score = {score}*"
        )


main()
