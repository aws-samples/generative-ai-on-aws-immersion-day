"""Abstact the different ways to load the SEC 14A docs"""

from typing import Any, List
from abc import ABC, abstractmethod

import load2
import load3
import langchain_qa
import utils_os
import utils_14a_ext


class DocSource(ABC):
    @abstractmethod
    def recommended_k(self) -> int:
        pass

    def rerank(self, sans):
        sans.sort()

        # Historically we like that doc, put it at the top
        top1 = next(x for x in sans if "0000003153-20-000004" in x)
        sans.insert(0, sans.pop(sans.index(top1)))
        return sans


class OpensearchTextFrags(DocSource):
    def __init__(self, config):
        print("Created", self.__class__.__name__)
        self.path = config["corpus"]["path14A_frag"]
        self.aos_config = config["aos"]

    def __str__(self):
        return "OpenSearch (Text fragments)"

    def recommended_k(self) -> int:
        return 1  # 2022 data is precise

    def list_14A(self) -> List[str]:
        print("list_14A", self.__class__.__name__)
        sans = load3.list_14A(self.path)
        return super(OpensearchTextFrags, self).rerank(sans)

    def load_14A(self, model: str, embed_model: str, san: str) -> Any:
        """ Create vector store"""

        print("Load3...")
        docs = load3.load_14A(self.path, san)

        # To save on cost, take just top 50 passages
        if len(docs) > 50:
            docs = docs[:50]

        print("Creating vector store", self.__class__.__name__)
        return langchain_qa.create_vector_store(
            model, embed_model, docs, self.aos_config
        )


class OpenSearchHTML(DocSource):
    def __init__(self, config):
        print("Created", self.__class__.__name__)
        self.path = config["corpus"]["path14A_html"]
        self.aos_config = config["aos"]

    def __str__(self):
        return "OpenSearch (HTML)"

    def recommended_k(self) -> int:
        return 4

    def list_14A(self) -> List[str]:
        print("list_14A", self.__class__.__name__)
        sans = load2.list_14A(self.path)
        return super(OpenSearchHTML, self).rerank(sans)

    def load_14A(self, model: str, embed_model: str, san: str) -> Any:
        """ Create vector store"""

        print("Load2...")
        docs = load2.load_14A(self.path, san)

        # To save on cost, take just top 30 passages
        if len(docs) > 30:
            docs = docs[:30]

        print("Creating vector store", self.__class__.__name__)
        return langchain_qa.create_vector_store(
            model, embed_model, docs, self.aos_config
        )


class KendraHTML(DocSource):
    def __init__(self, config):
        print("Created", self.__class__.__name__)
        self.kendra_config = config["kendra"]

    def __str__(self):
        return "Kendra (HTML)"

    def recommended_k(self) -> int:
        return 1  # answer only

    def list_14A(self) -> List[str]:
        """List files on Kendra s3 data source"""
        print("list_14A", self.__class__.__name__)
        files = utils_os.iterate_bucket(
            self.kendra_config["data_source"], extension=".html"
        )
        sans = [utils_14a_ext.to_san(f) for f in files]
        return super(KendraHTML, self).rerank(sans)

    def load_14A(self, model: str, embed_model: str, san: str) -> Any:
        """ Create kendra retriever"""
        print("Creating kendra store", self.__class__.__name__)
        return langchain_qa.amazon_kendra_retriever(self.kendra_config)
