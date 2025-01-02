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

    # Create chain to suggest documentation updates
    update_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical documentation writer. Your task is to maintain accurate and consistent documentation by analyzing code changes and suggesting precise updates.

        CONTEXT INFORMATION:
        1. Code Context (Existing Codebase):
        {code_context}

        2. Documentation Context (Existing Documentation):
        {docs_context}

        YOUR RESPONSIBILITIES:
        1. Documentation Style Analysis:
           - Identify the current documentation's technical depth
           - Note the writing style and tone
           - Observe formatting patterns and structure
           - Understand the level of detail typically provided

        2. Code Change Impact Analysis:
           - Review the code changes provided in the user input
           - Compare changes against existing codebase context
           - Identify which documentation sections need updates
           - Determine if the changes affect public APIs, behaviors, or user-facing features

        3. Generate Documentation Updates:
           - Maintain consistent style and depth with existing documentation
           - Provide exact file paths and sections for updates
           - Ensure technical accuracy
           - Keep the same formatting patterns

        OUTPUT REQUIREMENTS:

        If documentation updates are needed, use this format:        ```
        Documentation Analysis:
        - Current Style: [tone, language, and formatting patterns]
        - Technical Depth: [level of technical detail typically provided]
        - Documentation Structure: [how information is organized]

        Required Updates:
        1. Location: [exact file path and section identifier]
           Current Text: [text to be updated]
           Suggested Update: [new text that matches existing style]
           Reason: [specific justification for this update]

        2. [Additional updates if needed, following same format]        ```

        If no updates are needed, use this format:        ```
        Documentation Analysis:
        - Current Style: [tone, language, and formatting patterns]
        - Technical Depth: [level of technical detail typically provided]

        No Updates Required
        Reason: [detailed explanation why the code changes don't require documentation updates]        ```
        """),
        ("human", "Review these code changes and suggest appropriate documentation updates:\n{input}")
    ])

    # Chain to generate documentation updates
    doc_update_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=update_prompt,
        document_variable_name="docs_context"  # This is for the documentation context
    )

    xml_update_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical documentation writer. Your task is to convert documentation update suggestions into a structured XML format.

        CONTEXT INFORMATION:
        Existing Documentation:
        {context}

        RULES FOR XML CONVERSION:
        1. Extract exact content matches from existing documentation for original_content
        2. Use appropriate change types:
           - "replace": When updating existing content
           - "delete": When removing existing content
           - "append": When adding content to existing file
           - "new_file": When creating a new documentation file
        3. For "new_file" type, omit original_content
        4. For "delete" type, omit suggested_content
        5. file_path must be exact and match the documentation structure

        OUTPUT FORMAT:
        <documentation_update>
            <changes>
                <change type="[replace|delete|append|new_file]" file_path="[exact_file_path]">
                    <original_content>[exact_matching_content_from_docs]</original_content>
                    <suggested_content>[new_content_maintaining_style]</suggested_content>
                </change>
                <!-- Additional changes as needed -->
            </changes>
        </documentation_update>

        IMPORTANT:
        - Always validate that original_content exists in the documentation context
        - Ensure file_path matches the documentation structure
        - Maintain consistent formatting and style
        - Each change must be precise and actionable
        """),
        ("human", """Convert the following documentation update suggestions into XML format:
        {input}
        
        Remember to:
        1. Use exact matches for original_content
        2. Choose appropriate change types
        3. Follow the XML structure precisely
        4. Validate against existing documentation context""")
    ])

    xml_update_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=xml_update_prompt,
    )
    
    async def process_updates(code_changes: str):
        print("\n" + "="*50)
        print("Starting documentation update process")
        print("="*50)
        
        # Step 1: Get relevant code context
        print("\n📚 Getting relevant code context...")
        code_docs = await code_retriever.aget_relevant_documents(code_changes)
        print(f"Found {len(code_docs)} relevant code documents:")

        # Step 2: Analyze code changes
        print("\n🔍 Analyzing code changes...")
        # code_analysis = await code_analysis_chain.ainvoke({
        #     "input": code_changes,
        #     "context": code_docs
        # })
        # print("\nCode Analysis Result:")
        # print(code_analysis)
        
        # Format code documents
        formatted_code_docs = []
        for doc in code_docs:
            formatted_code_docs.append(f"File: {doc.metadata.get('file_path', 'N/A')}\n{doc.page_content}")
        final_formatted_code = "\n\n---\n\n".join(formatted_code_docs)
        print(final_formatted_code)

        
        # Step 3: Get relevant documentation
        print("\n📖 Finding relevant documentation...")
        doc_docs = await doc_retriever.aget_relevant_documents(code_changes)
        print(f"Found {len(doc_docs)} relevant documentation sections:", doc_docs)
       
        # Step 5: Generate documentation update suggestions
        print("\n✍️ Generating documentation updates...")
        update_suggestions = await doc_update_chain.ainvoke({
            "input": code_changes,
            "code_context": code_docs,
            "docs_context": doc_docs
        })

        xml_update_suggestions = await xml_update_chain.ainvoke({
            "input": update_suggestions,
            "context": doc_docs
        })
        print("\nXML Update Suggestions:")
        print(xml_update_suggestions)
        print("\nUpdate Suggestions:")
        print(update_suggestions)
        
        print("\n" + "="*50)
        print("Documentation update process completed")
        print("="*50 + "\n")
        
        return xml_update_suggestions
    
    return process_updates