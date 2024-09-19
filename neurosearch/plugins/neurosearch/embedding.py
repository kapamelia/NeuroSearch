from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from .config import Config

class Embedding:
    def __init__(self, model="text-embedding-v2"):
        self.embedding = DashScopeEmbeddings(model=model, dashscope_api_key=Config.get_dashscope_api_key())

    def get_embedding(self):
        return self.embedding
