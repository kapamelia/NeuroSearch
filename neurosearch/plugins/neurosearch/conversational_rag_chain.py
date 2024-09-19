from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains.retrieval import create_retrieval_chain
from .history_aware_retriever import HistoryAwareRetriever
from .question_answer_chain import QuestionAnswerChain
from .message_history import MessageHistoryManager

class ConversationalRAGChain:
    def __init__(self):
        self.history_aware_retriever = HistoryAwareRetriever().create()
        self.question_answer_chain = QuestionAnswerChain().create()
        self.history_manager = MessageHistoryManager()

    def create_chain(self):
        rag_chain = create_retrieval_chain(self.history_aware_retriever, self.question_answer_chain)
        return RunnableWithMessageHistory(
            rag_chain,
            self.history_manager.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

conversational_rag_chain = ConversationalRAGChain().create_chain()

__all__ = ["conversational_rag_chain"]