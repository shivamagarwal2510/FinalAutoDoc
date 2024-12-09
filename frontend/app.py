import streamlit as st
import requests

st.title("AutoDocs")

st.write("Welcome to AutoDocs! This is a tool that helps you automatically generate documentation for your code.")

codebase_url = st.text_input("Enter the GitHub URL of your codebase:")
codebase_branch = st.text_input("Enter the Branch name of your codebase:")
docs_url = st.text_input("Enter the GitHub URL of your documentation:")
docs_branch = st.text_input("Enter the Branch name of your documentation:")

if codebase_url and docs_url and docs_branch and codebase_branch:
    st.write("indexing codebase and documentation...")
    response = requests.post("http://localhost:8000/setup", json={
        "code_repo": {
            "url": codebase_url,
            "branch": codebase_branch or "main",
            "type": "code"
        },
        "docs_repo": {
            "url": docs_url,
            "branch": docs_branch or "main",
            "type": "docs"
        }
    })
    if response.status_code == 200:
        st.write("Codebase and documentation indexed successfully")
    else:
        st.write("Failed to index codebase and documentation", response)
        
    
