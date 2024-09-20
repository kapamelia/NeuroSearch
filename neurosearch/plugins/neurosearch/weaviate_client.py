import weaviate
from langchain_weaviate.vectorstores import WeaviateVectorStore

from .config import Config
from .embedding import Embedding
class WeaviateClient:
    def __init__(self):
        self.client = weaviate.connect_to_custom(
            http_host=Config.get_weaviate_host(),
            http_port=8080,
            http_secure=False,
            grpc_host=Config.get_weaviate_host(),
            grpc_port=50051,
            grpc_secure=False,
            skip_init_checks=True,
        )

    def get_client(self):
        return self.client
    
    def get_collection(self, collection_name: str):
        return self.client.collections.get(collection_name)
    

class WeaviateStoreClient:
    def __init__(self):
        self.client = weaviate.connect_to_custom(
            http_host=Config.get_weaviate_host(),
            http_port=8080,
            http_secure=False,
            grpc_host=Config.get_weaviate_host(),
            grpc_port=50051,
            grpc_secure=False,
            skip_init_checks=True,
        )
        self.create_store()

    def create_store(self):
        self.weaviate_vector_store = WeaviateVectorStore(
            client=self.client,
            index_name="article_vector_index",
            text_key="text",
            embedding=Embedding().get_embedding(),
        )