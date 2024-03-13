
from typing import Optional, Iterable, List, Any
from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStore
from convex import ConvexClient
from dotenv import load_dotenv
import os
import multiprocessing
import uuid
import copy
from langchain.docstore.document import Document

load_dotenv()

class ConvexDocStore(VectorStore):
    def __init__(self, index, embeddings, convex_url) -> None:
        super().__init__()
        self._embeddings = embeddings
        self._index = index
        self._convex_client = ConvexClient(convex_url)

    @property
    def embeddings(self) -> Optional[Embeddings]:
        """Access the query embedding object if available."""
        if isinstance(self._embeddings, Embeddings):
            return self._embeddings
        return None
    
    def _embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        """Embed search docs."""
        if isinstance(self._embeddings, Embeddings):
            return self._embeddings.embed_documents(list(texts))
        return [self._embeddings(t) for t in texts]

    def _embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        if isinstance(self._embeddings, Embeddings):
            return self._embeddings.embed_query(text)
        return self._embeddings(text)

    @classmethod
    def from_texts(
        cls, 
        texts: List[str],
        embedding: Embeddings,
        company_name: str = None,
        convex_url: str = os.getenv('CONVEX_URL')
    ):
        convex_client = ConvexClient(convex_url)
        embedded_texts = copy.deepcopy(texts)
        embedded_texts = cls.parallel_vectorize(embedded_texts, embedding)

        for i in range(len(embedded_texts)):
            convex_client.action("docs:insert", args={'name':f'{company_name}_{i}', 
                                                      'company_name':company_name, 
                                                      'description':'description', 
                                                      'content':texts[i].page_content, 
                                                      'embeddings':embedded_texts[i].page_content})

    def vectorize(self, embeddings, page_content, result_queue):
        vectors = embeddings.embed_query(page_content)
        result_queue.put(vectors)

    def parallel_vectorize(self, pages, embeddings):
        vec_queue = multiprocessing.Queue()
        processes = []

        for page in pages:
            process = multiprocessing.Process(target=self.vectorize, args=(embeddings, page, vec_queue))
            processes.append(process)
            process.start()

        # Retrieve results from the queue
        for page in pages:
            page = vec_queue.get()      

        # Wait till all the processes run completely before going on
        for process in processes:
            process.join()
        
        return pages
    
    def similarity_search(self, query: str) -> List[Document]:
        convex_client = ConvexClient(os.getenv('CONVEX_URL'))
        embeds = self._embeddings.embed_query(query)
        as_output = convex_client.action("docs:doc_search", args={'query_embedding':embeds, 'company_name':self._index})
        return [Document(page_content=d.get('content'), metadata={'id':d.get('_id'), 'score':d.get('_score')}) for d in as_output]
    
    def add_texts(self, texts: Iterable[str], 
                  ids: Optional[List[str]] = None,
                  company_name: Optional[List[str]] = None,
                ) :
            texts = list(texts)
            embedded_texts = copy.deepcopy(texts)
            embedded_texts = self.parallel_vectorize(embedded_texts, self._embeddings)

            for i in range(len(ids)):
                res = self._convex_client.action("docs:insert", args={'name':ids[i], 
                                                                      'company_name':company_name, 
                                                                      'content':texts[i].page_content, 
                                                                      'embeddings':embedded_texts[i].page_content})

