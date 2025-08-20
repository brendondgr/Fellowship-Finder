# Fellowship Helper

Fellowship Finder is a web scraping and data management application that helps users discover and organize fellowship opportunities from ProFellow.com.

## Core Features

- **Web Scraping**: Automated scraping of fellowship data from ProFellow.com using Selenium
- **Data Processing**: AI-powered refinement of scraped data using Google Gemini
- **Web Interface**: Flask-based web application for browsing and filtering fellowships
- **Data Management**: Persistent storage with CSV files and user interaction tracking
- **Filtering System**: Advanced filtering by categories, keywords, ratings, and favorites

## Common Commands

```bash
# Install dependencies
uv sync

# Run the Flask application
python app.py

# Run data scraping
python data_retrieval.py --browser firefox

# Process existing raw data
python data_retrieval.py --refine

# Clean temporary files
python data_retrieval.py --cleartmp

# Full cleanup (tmp + data)
python data_retrieval.py --cleanup
```


## Technology Stack

### Backend
- **Flask**: Web framework for API and web interface
- **Selenium**: Web scraping automation
- **Google Generative AI**: Data refinement and processing

### Frontend
- **Jinja2 Templates**: Server-side rendering
- **Tailwind CSS**: Styling framework
- **Vanilla JavaScript**: Client-side interactions

### Data Storage
- **CSV Files**: Primary data storage format
- **JSON Files**: Configuration and filter storage

## Project Structure

### Root Level
- **app.py**: Main Flask application with API endpoints and web routes
- **main.py**: Simple entry point (minimal implementation)
- **data_retrieval.py**: CLI script for scraping and data processing
- **config.ini**: Configuration file for paths and settings
- **pyproject.toml**: Modern Python project configuration
- **requirements.txt**: Python dependencies
- **uv.lock**: UV package manager lock file

### Configuration & Data
- **configs/**: JSON configuration files
  - `filters.json`: Scraping filters and categories
  - `login.json`: Authentication credentials (not in repo)
- **data/**: Data storage (created at runtime)
  - `raw/`: Raw scraped data
  - `processed/`: Refined fellowship data
- **tmp/**: Temporary files and caching

### Web Interface
- **templates/**: Jinja2 HTML templates
  - `index.html`: Main fellowship browser interface
  - `scrape.html`: Scraping configuration interface
- **static/**: Frontend assets
  - `index.css`: Custom styles
  - `index.js`: Client-side JavaScript
  - `svg/`: Icon assets

### Core Utilities
- **utils/**: Core business logic modules
  - `data_manager.py`: DataManager class for CSV operations and filtering
  - `scrape.py`: ProfellowBot class for web scraping
  - `data.py`: DataProcessor for raw data handling
  - `refinement.py`: GeminiRefiner for AI-powered data processing
  - `files_folders.py`: FileManager for directory operations

## Architecture Patterns