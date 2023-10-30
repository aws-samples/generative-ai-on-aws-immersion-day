"""Custom serialization of HTML into text."""

import logging
from typing import Dict, List, Union
import re
from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from bs4 import BeautifulSoup, Comment, NavigableString

logger = logging.getLogger(__file__)


class BSHTMLLoaderEx(BaseLoader):
    """Loader that uses beautiful soup to parse HTML files."""

    block_level_elements = set(
        [
            "address",
            "article",
            "aside",
            "blockquote",
            "canvas",
            "dd",
            "div",
            "dl",
            "dt",
            "fieldset",
            "figcaption",
            "figure",
            "footer",
            "form",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "hr",
            "li",
            "main",
            "nav",
            "noscript",
            "ol",
            "p",
            "pre",
            "section",
            "table",
            "tfoot",
            "ul",
            "video",
            "body",
        ]
    )

    def __init__(
        self,
        file_path: str,
        open_encoding: Union[str, None] = None,
        bs_kwargs: Union[dict, None] = None,
    ) -> None:
        """Initialise with path, and optionally, file encoding to use, and any kwargs
        to pass to the BeautifulSoup object."""
        try:
            import bs4  # noqa:F401
        except ImportError:
            raise ValueError(
                "bs4 package not found, please install it with " "`pip install bs4`"
            )

        self.file_path = file_path
        self.open_encoding = open_encoding
        if bs_kwargs is None:
            bs_kwargs = {"features": "lxml"}
        self.bs_kwargs = bs_kwargs

    def load(self) -> List[Document]:

        """Load HTML document into document objects."""
        with open(self.file_path, "r", encoding=self.open_encoding) as f:
            soup = BeautifulSoup(f, **self.bs_kwargs)

        # text = soup.get_text()
        text = self._parse(soup)

        if soup.title:
            title = str(soup.title.string)
        else:
            title = ""

        metadata: Dict[str, Union[str, None]] = {
            "source": self.file_path,
            "title": title,
        }
        return [Document(page_content=text, metadata=metadata)]

    def _parse(self, soup):
        """Custom parser"""

        def __clean(s):
            s = s.replace(u"\xa0", u" ")
            return s

        # DFS post-order.
        # Adding a different delimeter at the end of each tag
        def dfs(tags, texts):
            for tag in tags:
                if isinstance(tag, Comment):
                    pass
                elif isinstance(tag, NavigableString):
                    texts += (tag.string,)

                else:
                    # Starting a new paragraph tag,
                    # terminate previous non-paragraph by the period.
                    if tag.name in type(self).block_level_elements:
                        # if texts:
                        #     print("'{}'".format(texts[-1][-10:]))
                        #     print(texts[-1][-1].isalnum())
                        if texts and texts[-1] and texts[-1][-1].isalnum():
                            texts[-1] += "."
                        texts += ("\n",)

                    # How to serialize a table?
                    # if tag.name in ['td']:
                    #     texts += '; ',

                    dfs(tag.children, texts)

        texts = []

        dfs([soup.find("body")], texts)

        s = "".join(texts)
        s = __clean(s)
        s = re.sub(r"[\.]+", ".", s)  # multiple dots

        return s
