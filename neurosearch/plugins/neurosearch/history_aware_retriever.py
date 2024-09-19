from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_weaviate.vectorstores import WeaviateVectorStore
from .weaviate_client import WeaviateClient
from .embedding import Embedding
from .config import Config


class HistoryAwareRetriever:
    def __init__(self):
        self.embedding = Embedding().get_embedding()
        self.weaviate_client = WeaviateClient().get_client()
        self.llm = ChatTongyi(
            model="llama3.1-70b-instruct",
            temperature=0,
            max_tokens=2048,
            api_key=Config.get_dashscope_api_key(),
        )
        self.contextualize_question_prompt = (
            self._create_contextualize_question_prompt()
        )

    def _create_contextualize_question_prompt(self):
        contextualize_question_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_question_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def create(self):
        weaviate_vector_store = WeaviateVectorStore(
            client=self.weaviate_client,
            index_name="article_vector_index",
            text_key="text",
            embedding=self.embedding,
        )
        return create_history_aware_retriever(
            self.llm,
            weaviate_vector_store.as_retriever(),
            self.contextualize_question_prompt,
        )
