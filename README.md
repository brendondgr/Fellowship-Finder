# Fellowship Finder

<div align="center">

A web scraping and data management application to discover, organize, and refine fellowship opportunities from across the web.

</div>

<br>

<div align="center">
<img src="images/both_pages.png" alt="Fellowship Finder Interface" width="800">
</div>

## ✨ About The Project

Fellowship Finder automates the tedious process of searching for professional fellowships. It began by targeting ProFellow.com and is expanding to include private resources, job boards, and other major platforms. The core mission is to provide a centralized, efficient tool for users to discover and manage opportunities with the help of AI-powered data refinement.

## 🚀 Key Features

* **🤖 Automated Discovery**: Deploys web scrapers to automatically find and retrieve fellowship listings.

* **🧠 AI-Powered Refinement**: Uses Google's Generative AI to clean, standardize, and enhance the quality of scraped data.

* **🗂️ User-Friendly Management**: An intuitive web interface for organizing, favoriting, and filtering opportunities.

* **⚙️ Streamlined Workflow**: Simple command-line operations for data retrieval, processing, and cleanup.

## 🛠️ Built With

* **Backend**: Flask, Selenium, Pandas, Google Generative AI

* **Frontend**: Jinja2, Tailwind CSS, Vanilla JavaScript

* **Data Storage**: CSV and JSON files

## 🏁 Getting Started

Follow these steps to get a local copy up and running.

### Prerequisites

* Python 3.10+

* A modern web browser (e.g., Firefox, Chrome)

* `uv` or `conda` package manager

### Installation

1. **Clone the repository:**

   ```
   git clone https://github.com/brendondgr/Fellowship-Finder.git
   cd Fellowship-Finder
   ```

   Alternative (SSH):

   ```
   git clone git@github.com:brendondgr/Fellowship-Finder.git
   cd Fellowship-Finder
   ```

2. **Set up your API keys and credentials:**

   * Copy your Google Gemini API key into `configs/api_key.json`.

   * Add your ProFellow.com login details to `configs/login.json` (this file is git-ignored).

3. **Install dependencies using your preferred package manager:**

   **Option A: `uv` (Recommended)**

   ```
   # Install dependencies
   uv sync
   
   # Run the application
   uv run app.py
   ```

   **Option B: `conda`**

   ```
   # Create and activate a new environment
   conda create -n fellowship python=3.10
   conda activate fellowship
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run the application
   python app.py
   ```

## 🖥️ Usage

The `data_retrieval.py` script provides a command-line interface for all data operations.

| **Command** | **Description** | 
|---|---|
| `python data_retrieval.py --browser [name]` | Scrape for new data using the specified browser (e.g., `firefox`). | 
| `python data_retrieval.py --refine` | Process and clean the raw data using the AI refinement module. | 
| `python data_retrieval.py --cleartmp` | Clean out temporary files from the `tmp/` directory. | 
| `python data_retrieval.py --cleanup` | Perform a full cleanup of all temporary and raw data files. | 

## 📂 Project Structure

```
Fellowship-Finder/
├── app.py                 # Main Flask application
├── data_retrieval.py      # CLI for data scraping and processing
├── requirements.txt       # Project dependencies
├── configs/               # Configuration files (API keys, filters)
├── data/                  # Raw and processed data
├── static/                # Static assets (CSS, JS, icons)
├── templates/             # Jinja2 HTML templates
└── utils/                 # Core application logic
