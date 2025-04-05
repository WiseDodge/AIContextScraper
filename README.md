# AIContextScraper

A powerful and reusable Python scraper framework designed for efficiently crawling documentation websites and preparing content for AI training. It features async operations, structured output formats, and intelligent content processing.

## 🔑 Key Features

- 🔁 Recursive crawling from a single starting URL
- 🧠 Intelligent content extraction and structuring
- 📄 Multiple export formats (JSON, TXT, PDF)
- ⚡ Async operations for improved performance
- 🔄 Automatic retry mechanism
- 📊 Token counting and chunking
- 📁 Organized output structure

## 📋 Requirements

- Python 3.8+
- Required packages listed in `requirements.txt`

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd AIContextScraper
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

1. Run the scraper:
   ```bash
   python main.py
   ```

2. Follow the prompts:
   - Enter the documentation website URL
   - Specify a project name (or use default)
   - Choose whether to export PDFs

## 📁 Output Structure

```
D:/AI_Training_Corpora/PROJECT_NAME/
├── raw_html/           # Original HTML content
├── json/              # Structured content with metadata
├── txt/               # Chunked text content
├── pdf/               # PDF exports (optional)
├── logs/              # Execution logs
└── metadata.json      # Run statistics and summary
```

## 🧩 JSON Structure

```json
{
  "title": "Page Title",
  "url": "https://example.com/docs/page",
  "content": "Extracted and cleaned content...",
  "tokens": 184,
  "timestamp": "2023-12-25T20:15:23Z"
}
```

## ⚙️ Configuration

Adjust settings in `config.py`:
- HTTP request parameters
- Crawling limits
- Content processing options
- Output formatting

## 🔄 Future Enhancements

- Direct embedding export for vector databases
- Automatic content classification
- Markdown export support
- Browser-based crawling for JS-heavy sites
- Scheduled updates for documentation sites

## 📝 License

MIT License - feel free to use and modify for your needs.