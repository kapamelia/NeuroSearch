import weaviate
from .config import Config

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
