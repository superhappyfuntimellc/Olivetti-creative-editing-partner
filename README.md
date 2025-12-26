# 🎨 Olivetti Creative Editing Partner

Professional-grade AI writing assistant inspired by the elegance of Olivetti typewriters.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys), then:

**Option A: Edit `.streamlit/secrets.toml` (Recommended)**
```toml
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxx"
```

**Option B: Environment Variable**
```bash
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxx"
```

See [SETUP_API_KEY.md](SETUP_API_KEY.md) for detailed instructions.

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📚 Documentation

- **[SETUP_API_KEY.md](SETUP_API_KEY.md)** - Detailed API key setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture
- **[QUICK_START.md](QUICK_START.md)** - Wake-up summary and features

## ⚠️ Troubleshooting

### "OpenAI SDK Not Installed" Error

```bash
pip install openai>=2.0.0
```

### "OpenAI API Key Not Configured" Warning

1. Get your API key from https://platform.openai.com/api-keys
2. Edit `.streamlit/secrets.toml`
3. Replace `"your-api-key-here"` with your actual key
4. Refresh the page

### Dependencies Installation Failed

Make sure you have Python 3.8+ installed:
```bash
python3 --version
pip install --upgrade pip
pip install -r requirements.txt
```

## ✨ Features

- **Multi-Bay Project System** - NEW → ROUGH → EDIT → FINAL workflow
- **Voice Bible** - AI intensity, writing style, and genre controls
- **Voice Vault** - Store and retrieve writing samples with semantic search
- **Style Banks** - Exemplar-based style training
- **Story Bible** - Canon management for characters, world, and outline
- **Import/Export** - DOCX, EPUB, PDF, and plain text support
- **AI-Powered Writing Actions** - Write, Rewrite, Expand, Trim, and more

## 🎯 System Requirements

- Python 3.8 or higher
- OpenAI API key (for AI features)
- 1GB+ free disk space (for dependencies)
- Internet connection (for AI API calls)

## 📦 Core Dependencies

- `streamlit>=1.52.0` - Web UI framework
- `openai>=2.0.0` - OpenAI API client
- `python-docx>=1.1.2` - DOCX import/export
- `ebooklib>=0.18` - EPUB export
- `fpdf2>=2.7` - PDF export

## 🔐 Security Note

Never commit your `.streamlit/secrets.toml` file or share your API key publicly. The file is already in `.gitignore` for your protection.

## 🐛 Reporting Issues

If you encounter problems:

1. Check the logs in `olivetti.log`
2. Review error messages in the UI (they're now persistent and detailed)
3. Verify your API key is configured correctly
4. Ensure all dependencies are installed

## 📄 License

See the repository for license information.

---

**Made with ❤️ and the spirit of Olivetti craftsmanship**
