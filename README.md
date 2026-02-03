# Doc Simplifier

A beautiful web application that takes any technical documentation URL, scrapes all content, and uses OpenAI GPT-4 to generate a simplified, plain-English report for non-technical users.

## Features

- **Smart Crawling** - Automatically crawls related pages to get the full picture
- **AI-Powered Simplification** - Uses GPT-4 to translate technical jargon
- **Beautiful Reports** - Clean, modern UI with organized sections
- **Report History** - Save and browse previous reports

## Report Sections

Each generated report includes:
- **What is this?** - Plain English explanation
- **Who is this for?** - Target audience and skill level
- **Key Features** - Main capabilities in simple terms
- **Use Cases** - Real-world examples
- **Getting Started** - Step-by-step guide for beginners
- **Common Operations** - Most useful things you can do
- **Pricing/Limits** - Cost and usage limits
- **Alternatives** - Similar tools for comparison

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd ~/doc-simplifier
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your OpenAI API key.

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Open in browser:**
   Navigate to http://localhost:8000

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Web framework
- **BeautifulSoup4** - HTML parsing
- **httpx** - Async HTTP client
- **OpenAI API** - GPT-4 for simplification
- **Jinja2** - HTML templating
- **TailwindCSS** - Styling (via CDN)
- **SQLite** - Report storage

## Usage

1. Enter a documentation URL on the home page
2. Click "Simplify" to start processing
3. Wait for the crawling and AI analysis
4. View your simplified report
5. Print or copy sections as needed

## Project Structure

```
doc-simplifier/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLite connection
│   ├── scraper/
│   │   ├── crawler.py       # URL crawling logic
│   │   └── parser.py        # Content extraction
│   ├── processor/
│   │   ├── cleaner.py       # Clean/structure content
│   │   └── chunker.py       # Split large docs
│   ├── ai/
│   │   ├── openai_client.py # OpenAI API wrapper
│   │   └── prompts.py       # System prompts
│   └── models/
│       └── schemas.py       # Pydantic models
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS styles
├── requirements.txt
└── .env.example
```

## API Endpoints

- `GET /` - Home page
- `POST /simplify` - Submit URL for processing
- `GET /processing/{id}` - View progress
- `GET /report/{id}` - View completed report
- `GET /history` - Browse all reports
- `DELETE /report/{id}` - Delete a report
- `GET /api/status/{id}` - Get processing status (JSON)

## License

MIT
