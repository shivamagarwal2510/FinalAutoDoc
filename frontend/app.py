import streamlit as st
import requests

st.title("AutoDocs")

st.write("Welcome to AutoDocs! This is a tool that helps you automatically generate documentation for your code.")

codebase_repo_id = st.text_input("Enter the GitHub repo id of your codebase:")
codebase_branch = st.text_input("Enter the Branch name of your codebase:")
docs_repo_id = st.text_input("Enter the GitHub repo id of your documentation:")
docs_branch = st.text_input("Enter the Branch name of your documentation:")
docs_folder_path = st.text_input("Enter the folder path of documentation (if its root folder then Enter /):")

if codebase_repo_id and docs_repo_id and docs_branch and codebase_branch and docs_folder_path:
    st.write("indexing codebase and documentation...")
    response = requests.post("http://localhost:8000/setup", json={
        "code_repo": {
            "url": codebase_repo_id,
            "branch": codebase_branch or "main",
            "type": "code"
        },
        "docs_repo": {
            "url": docs_repo_id,
            "branch": docs_branch or "main",
            "type": "docs",
            "folder_path": docs_folder_path
        }
    })
    if response.status_code == 200:
        st.write("Codebase and documentation indexed successfully")
    else:
        st.write("Failed to index codebase and documentation", response)
        
    
