from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from backend.app.core.llm import build_llm_via_langchain
from backend.app.core.retriever import build_retriever_from_args

def build_documentation_update_chain(code_args, doc_args):
    """Builds a specialized chain for identifying documentation updates needed."""
    llm = build_llm_via_langchain(code_args["llm_provider"], code_args["llm_model"])
    
    # Create retrievers for both code and documentation
    code_retriever = build_retriever_from_args(code_args)
    doc_retriever = build_retriever_from_args(doc_args)
    
    # First, create a chain to analyze code changes and find relevant documentation
    analyze_code_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert code analyzer. Given code changes in diff format, identify the key components and functionality that need documentation.
        
        The code changes are provided in the following format:
        - File paths are shown at the start of each diff
        - Lines starting with '+' indicate additions
        - Lines starting with '-' indicate deletions
        - Context lines are shown without any prefix
        
        Code Changes:
        {context}
        
        Analyze the changes and identify:
        1. Changed files and their significance
        2. Added/removed/modified functions and methods
        3. Changes in behavior or functionality
        4. New features or deprecations
        5. Areas that need documentation updates based on these changes
        
        Focus on changes that impact the public API, behavior, or user-facing functionality.
        """),
        ("human", "{input}")
    ])

    # Chain to analyze code changes
    code_analysis_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=analyze_code_prompt,
        document_variable_name="context"
    )

    # Then create a chain to suggest documentation updates
    update_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert documentation maintainer. Based on the code analysis and existing documentation, suggest precise updates. You should read the existing 

        Code Analysis:
        {code_analysis}

        Existing Documentation:
        {context}

        Suggest specific documentation updates that:
        1. Match the existing documentation's tone and style
        2. Are precise and technically accurate
        3. Include exact locations where updates should be made
        4. Maintain the current documentation structure
        5. Analyze the existing documentation to find the amount of details that is needed to be added and update the documentation accordingly.

        Format your response as:
        - Location: [file path and section]
        - Current Text: [existing text to be updated]
        - Suggested Update: [new text]
        - Reason: [brief explanation of why this update is needed]
        """),
        ("human", "{input}")
    ])

    # Chain to generate documentation updates
    doc_update_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=update_prompt,
        document_variable_name="context"
    )
    
    async def process_updates(code_changes: str):
        print("\n" + "="*50)
        print("Starting documentation update process")
        print("="*50)
        
        # Step 1: Get relevant code context
        print("\n📚 Getting relevant code context...")
        code_docs = await code_retriever.aget_relevant_documents(code_changes)
        print(f"Found {len(code_docs)} relevant code documents:")
        # for i, doc in enumerate(code_docs, 1):
        #     print(f"\n📄 Code Document {i}:")
        #     print(f"Path: {doc.metadata.get('file_path', 'N/A')}")
        #     print(f"Content Preview: {doc.page_content[:200]}...")
        
        # Format code documents
        # formatted_code_docs = []
        # for doc in code_docs:
        #     formatted_code_docs.append(f"File: {doc.metadata.get('file_path', 'N/A')}\n{doc.page_content}")
        # final_formatted_code = "\n\n---\n\n".join(formatted_code_docs)
        # print(final_formatted_code)
        # Step 2: Analyze code changes
        print("\n🔍 Analyzing code changes...")
        code_analysis = await code_analysis_chain.ainvoke({
            "input": code_changes,
            "context": code_docs
        })
        print("\nCode Analysis Result:")
        print(code_analysis)
        
        # Step 3: Get relevant documentation
        print("\n📖 Finding relevant documentation...")
        doc_docs = await doc_retriever.aget_relevant_documents(code_analysis)
        print(f"Found {len(doc_docs)} relevant documentation sections:", doc_docs)
        # for i, doc in enumerate(doc_docs, 1):
        #     print(f"\n📝 Documentation Section {i}:")
        #     print(f"Path: {doc.metadata.get('file_path', 'N/A')}")
        #     print(f"Content Preview: {doc.page_content[:200]}...")
        
        # Step 4: Format documentation
        # print("\n📋 Formatting documentation...")
        # formatted_docs = []
        # for doc in doc_docs:
        #     formatted_docs.append(f"File: {doc.metadata.get('file_path', 'N/A')}\n{doc.page_content}")
        
        # # Join all formatted documents with clear separators
        # final_formatted_docs = "\n\n---\n\n".join(formatted_docs)
        # print(final_formatted_docs)
        # Step 5: Generate documentation update suggestions
        print("\n✍️ Generating documentation updates...")
        update_suggestions = await doc_update_chain.ainvoke({
            "input": code_changes,
            "code_analysis": code_analysis,
            "context": doc_docs
        })
        print("\nUpdate Suggestions:")
        print(update_suggestions)
        
        print("\n" + "="*50)
        print("Documentation update process completed")
        print("="*50 + "\n")
        
        return {
            "code_analysis": code_analysis,
            "update_suggestions": update_suggestions
        }
    
    return process_updates