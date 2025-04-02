# AI-Powered Documentation Updater

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

</div>

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
- GitHub account with repository access
- OpenAI API key (for AI model integration)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-doc-updater.git
cd ai-doc-updater
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

1. Set up your GitHub credentials:
   - Generate a GitHub Personal Access Token
   - Add it to your `.env` file

2. Configure OpenAI API:
   - Get your API key from OpenAI
   - Add it to your `.env` file

## 💻 Usage

1. Start the application:
```bash
python main.py
```

2. Access the web interface (Streamlit):
   - Open your browser and navigate to `http://localhost:8501`
   - Input your codebase and documentation repository URLs
   - Configure any additional settings

3. The system will:
   - Analyze your codebase and documentation
   - Generate embeddings for both
   - Monitor for changes
   - Create documentation updates automatically

## 🏗️ Architecture

The system consists of several key components:

- **Input Module**: Handles repository URLs and authentication
- **Chunking Engine**: Splits code and documentation into manageable pieces
- **Embedding Generator**: Creates vector embeddings for AI processing
- **Change Tracker**: Monitors codebase modifications
- **Documentation Updater**: Generates and applies documentation updates
- **Embedding Updater**: Maintains synchronization of embeddings

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the AI models
- GitHub for repository integration
- The open-source community for various tools and libraries

## 📞 Support

For support, please:
- Open an issue in the GitHub repository
- Contact the maintainers
- Check the [documentation](docs/) for detailed guides

---

<div align="center">
Made with ❤️ by the AI-Powered Documentation Updater Team
</div>
