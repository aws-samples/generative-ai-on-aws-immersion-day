import os
from typing import Dict, List
import json
import platform
import yaml
import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import RequestsHttpConnection

from langchain.chains.question_answering import load_qa_chain
from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.schema import Document

import sys

from langchain.embeddings import SagemakerEndpointEmbeddings
from langchain.embeddings.sagemaker_endpoint import EmbeddingsContentHandler
from langchain.vectorstores import OpenSearchVectorSearch
sys.path.append("../")

with open("../src/config.yml", "r") as file:
    config = yaml.safe_load(file)


def validate_environment():
    assert platform.python_version() >= "3.10"


class SageMakerContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        input_str = json.dumps({"text_inputs": prompt, **model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json["generated_texts"][0]


class EmbedContentHandler(EmbeddingsContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, inputs, model_kwargs: Dict) -> bytes:
        input_str = json.dumps({"text_inputs": inputs, **model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes) -> List[List[float]]:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json["embedding"]


def sagemaker_endpoint_embeddings():
    content_handler = EmbedContentHandler()
    return SagemakerEndpointEmbeddings(
        endpoint_name=config["llm"]["embedding_endpoint"],
        region_name="us-east-1",
        content_handler=content_handler,
    )


def amazon_opensearch_docsearch(aos_config, docs, embeddings):
    _aos_host = aos_config["aos_host"]
    port = 443
    region = os.environ.get("AWS_REGION")  # e.g. us-west-1  # e.g. us-west-1

    service = "es"
    credentials = boto3.Session().get_credentials()

    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token,
    )

    docsearch = OpenSearchVectorSearch.from_texts(
        texts=[d.page_content for d in docs],
        embedding=embeddings,
        metadatas=[d.metadata for d in docs],
        opensearch_url=[{"host": _aos_host, "port": port}],
        index_name=aos_config["aos_index"],
        http_auth=awsauth,
        use_ssl=True,
        pre_delete_index=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=100000,
    )
    return docsearch


def create_vector_store(model__, embed_model, docs, aos_config):
    if embed_model == "GPT-J":
        embeddings = sagemaker_endpoint_embeddings()
    else:
        assert False

    return amazon_opensearch_docsearch(
        aos_config=aos_config, docs=docs, embeddings=embeddings
    )


def amazon_kendra_retriever(kendra_config):
    return boto3.client("kendra")


def sagemaker_endpoint(endpoint_name):
    """T5-XXL"""
    return SagemakerEndpoint(
        endpoint_name=endpoint_name, 
        region_name="us-east-1", 
        model_kwargs={"temperature": 1e-10, }, 
        content_handler=SageMakerContentHandler(), 
    )


def chain_qa(llm, verbose=False):
    return load_qa_chain(llm, chain_type="stuff", verbose=verbose)


def search_and_answer(store, chain, query, k=1, doc_source_contains=None):

    if isinstance(store, OpenSearchVectorSearch):
        docs = store.similarity_search(
            query,
            k=k,
            # include_metadata=False,
            verbose=False,
        )
    elif store.__class__.__name__ == "kendra":
        response = store.retrieve(IndexId=config["kendra"]["index_id"], QueryText=query)
        docs = [Document(page_content=r["Content"]) for r in response["ResultItems"]]
    else:
        assert False, f"Unknown doc store {type(store)}"

    response = chain.run(input_documents=docs, question=query)
    return {"response": response, "docs": docs}
