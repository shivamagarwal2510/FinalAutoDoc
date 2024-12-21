import streamlit as st
import requests

st.title("AutoDocs")

st.write("Welcome to AutoDocs! This is a tool that helps you automatically generate documentation for your code.")

codebase_repo_id = st.text_input("Enter the GitHub repo id of your codebase:")
docs_repo_id = st.text_input("Enter the GitHub repo id of your documentation:")

diffs = st.text_area("Enter the diffs of your code changes:")

if st.button("Generate Documentation Updates") and codebase_repo_id and docs_repo_id and diffs:
    with st.spinner("Analyzing code changes and generating documentation updates..."):
        try:
            response = requests.post(
                "http://localhost:8000/changes", 
                json={
                    "code_repo_id": codebase_repo_id,
                    "docs_repo_id": docs_repo_id,
                    "diffs": diffs,
                }
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            
            result = response.json()
            
            # Display code analysis
            st.subheader("Code Analysis")
            st.markdown(result["code_analysis"])
            
            # Display documentation update suggestions
            st.subheader("Documentation Update Suggestions")
            st.markdown(result["update_suggestions"])
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {str(e)}")
            if hasattr(e.response, 'json'):
                st.error(f"Server response: {e.response.json()}")
        
    
