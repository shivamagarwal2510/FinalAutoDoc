# AI-Powered Documentation Updater


## 📝 Overview

The AI-Powered Documentation Updater is an intelligent tool that automates the process of keeping software documentation in sync with codebase changes. By leveraging advanced AI models and vector embeddings, it intelligently analyzes code changes and generates precise documentation updates, creating pull requests automatically to maintain accurate and up-to-date documentation.

## ✨ Key Features

- **Smart Change Detection**: Automatically monitors codebase changes using Git integration
- **Intelligent Documentation Updates**: Uses AI to generate context-aware documentation updates
- **Precise Location Targeting**: Pinpoints exact locations in documentation that need updates
- **Automated PR Creation**: Streamlines workflow by automatically creating documentation pull requests
- **Continuous Learning**: Maintains and updates embeddings for better context understanding over time
- **Tone and Style Consistency**: Preserves existing documentation style and depth

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for AI model integration)
- PINECONE API Key
- ANTHROPIC API Key
- MONGODB CONNECTION STRING
- Setup [AutoDocGithub App](https://github.com/ipriyanshi1708/AutoDocGithubApp)

### Configuration

1. Set up your environment variables.
2. Install dependencies using command:
```bash
pip install -r requirements.txt
```
3. Run the backend using command:
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
4. Run the frontend to generate embeddings using command:
```bash
streamlit run frontend/app.py
```


## 💻 Usage

1. Access the web interface (Streamlit):
   - Open your browser and navigate to `http://localhost:8501`
   - Input your codebase and documentation repository URLs to generate embeddings

2. The system will:
   - Analyze your codebase and documentation
   - Generate embeddings for both
   - Monitor for changes
   - Create documentation updates automatically

3. Add [Github App](https://github.com/ipriyanshi1708/AutoDocGithubApp) in your Github to track if any Pull request is created on the repository.
   
4. As soon as Pull Request is merged on the Codebase repository the github app will track the changes and analyze them to generate the documentation updates accordingly and finally creates a Pull Request on the Documentation repository mapped to the codebase repository.

## 🏗️ Architecture

The system consists of several key components:

- **Input Module**: Handles repository URLs
- **Chunking Engine**: Splits code and documentation into manageable pieces
- **Embedding Generator**: Creates vector embeddings for AI processing
- **Change Tracker**: Monitors codebase modifications
- **Documentation Updater**: Generates and applies documentation updates
- **Embedding Updater**: Maintains synchronization of embeddings

## 🙏 Acknowledgements

- OpenAI for providing the AI models
- GitHub for repository integration

---

<div align="center">
Made with ❤️ by <a href="https://github.com/shivamagarwal2510">Shivam Agarwal</a> & <a href="https://github.com/ipriyanshi1708">Priyanshi Agarwal</a>
</div>
