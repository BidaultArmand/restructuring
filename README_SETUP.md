# Python Environment Setup Guide

This guide will help you recreate the Python virtual environment for this PDF extraction and structuring project.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Quick Setup (Automated)

### On macOS/Linux:

```bash
# Make the setup script executable
chmod +x setup_env.sh

# Run the setup script
bash setup_env.sh
```

### On Windows:

```powershell
# Remove existing venv (if exists)
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue

# Create new virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env
Copy-Item .env.example .env
```

## Manual Setup

### Step 1: Remove Existing Environment (if needed)

```bash
rm -rf venv
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```powershell
.\venv\Scripts\activate
```

### Step 4: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Blackbox AI API key:
   ```
   BLACKBOX_API_KEY=your_actual_api_key_here
   ```

## Installed Packages

The `requirements.txt` includes:

- **pdfplumber**: PDF text extraction
- **unstructured[pdf]**: Advanced PDF table extraction
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management
- **pillow**: Image processing (required by unstructured)
- **pdf2image**: PDF to image conversion
- **pytesseract**: OCR capabilities

## Usage

After setup, you can run the project:

```bash
# Activate the environment (if not already activated)
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows

# Run the main script
python main.py
```

## Deactivating the Environment

When you're done working:

```bash
deactivate
```

## Troubleshooting

### Issue: `unstructured` installation fails

Try installing system dependencies first:

**macOS:**
```bash
brew install poppler tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils tesseract-ocr
```

### Issue: Missing BLACKBOX_API_KEY

Make sure you've:
1. Created a `.env` file from `.env.example`
2. Added your actual API key to the `.env` file
3. The `.env` file is in the project root directory

## Project Structure

```
restructuring/
├── venv/                  # Virtual environment (created by setup)
├── data/                  # Input PDF files
├── outputs/               # Extracted text files
├── info_structured/       # Structured JSON output
├── main.py               # Main entry point
├── pdf_extract.py        # PDF extraction logic
├── llm_structure.py      # LLM structuring logic
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Environment variables template
└── setup_env.sh          # Automated setup script
