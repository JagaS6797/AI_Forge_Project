from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import chat_llm


def build_chat_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a concise, helpful assistant for a web chatbot.",
            ),
            (
                "human",
                "Conversation history:\n{history}\n\nUser message:\n{message}",
            ),
        ]
    )
    return prompt | chat_llm | StrOutputParser()
