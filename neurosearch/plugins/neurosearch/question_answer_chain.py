from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_models.baidu_qianfan_endpoint import QianfanChatEndpoint
from .config import Config


class QuestionAnswerChain:
    def __init__(self):
        self.llm = QianfanChatEndpoint(
            model="ERNIE-Speed-Pro-128K",
            temperature=0.1,
            max_tokens=2048,
            api_key=Config.get_qianfan_api_key(),
            secret_key=Config.get_qianfan_secret_key(),
        )
        self.qa_prompt = self._create_qa_prompt()

    def _create_qa_prompt(self):
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise.\n\n{context}"
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def create(self):
        return create_stuff_documents_chain(self.llm, self.qa_prompt)
