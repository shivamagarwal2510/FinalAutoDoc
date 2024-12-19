"""A gradio app that enables users to chat with their codebase.
"""

import logging
import gradio as gr
from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.schema import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from backend.app.core.llm import build_llm_via_langchain
from backend.app.core.retriever import build_retriever_from_args

load_dotenv()


def build_rag_chain(args):
    """Builds a RAG chain via LangChain."""
    llm = build_llm_via_langchain(args["llm_provider"], args["llm_model"])
    retriever = build_retriever_from_args(args)

    # Prompt to contextualize the latest query based on the chat history.
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question which might reference context in the chat history, "
        "formulate a standalone question which can be understood without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    contextualize_q_llm = llm.with_config(tags=["contextualize_q_llm"])
    history_aware_retriever = create_history_aware_retriever(contextualize_q_llm, retriever, contextualize_q_prompt)

    qa_system_prompt = (
        f"You are my coding buddy, helping me quickly understand a GitHub repository called {args["repo_id"]}."
        "Assume I am an advanced developer and answer my questions in the most succinct way possible."
        "\n\n"
        "Here are some snippets from the codebase."
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain


def main():
    args = {
        "repo_id": "shadcn-ui/ui",
        "llm_provider": "anthropic",
        "llm_model": "claude-3-5-sonnet-20241022",
        "share": True,
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-large",
        "vector_store_provider": "pinecone",
        "index_namespace": "codeshadcnuiui",
        "index_name": "codeembeddings",
        "retriever_top_k": 5,
        "retrieval_alpha": 0.9,
        "multi_query_retriever": False,
        "embedding_size": 3072,
    }
    rag_chain = build_rag_chain(args)

    def source_md(file_path: str, url: str) -> str:
        """Formats a context source in Markdown."""
        return f"[{file_path}]({url})"

    async def _predict(message, history):
        """Performs one RAG operation."""
        history_langchain_format = []
        for human, ai in history:
            history_langchain_format.append(HumanMessage(content=human))
            history_langchain_format.append(AIMessage(content=ai))
        history_langchain_format.append(HumanMessage(content=message))

        query_rewrite = ""
        response = ""
        async for event in rag_chain.astream_events(
            {
                "input": message,
                "chat_history": history_langchain_format,
            },
            version="v1",
        ):
            if event["name"] == "retrieve_documents" and "output" in event["data"]:
                sources = [(doc.metadata["file_path"], doc.metadata["url"]) for doc in event["data"]["output"]]
                # Deduplicate while preserving the order.
                sources = list(dict.fromkeys(sources))
                response += "## Sources:\n" + "\n".join([source_md(s[0], s[1]) for s in sources]) + "\n## Response:\n"

            elif event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content

                if "contextualize_q_llm" in event["tags"]:
                    query_rewrite += chunk
                else:
                    # This is the actual response to the user query.
                    if not response:
                        logging.info(f"Query rewrite: {query_rewrite}")
                    response += chunk
                    yield response

    gr.ChatInterface(
        _predict,
        title=args["repo_id"],
        examples=["What does this repo do?", "Give me some sample code."],
    ).launch(share=args["share"])


if __name__ == "__main__":
    main()
