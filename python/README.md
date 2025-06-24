# Bible Database Python Client

This Python module provides a client for connecting to the Bible Database in
MariaDB.

## Setup Instructions

Note that you will need a MySQL password to connect to the database. This
assumes that you have followed the instructions in the `docker-compose.yml`
file and set a specific password.

### Set up your environment

Create a virtual environment and install the required packages. Windows:

```pwsh
# Create virtual environment
python -m venv .venv

# Activate the virtual environment
& .venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

Linux:

```bash
# Create virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```


### Configure environment variables

- Copy the example environment file `.env.example` to `.env`
- Add your database credentials to the `.env` file

### Run the example

From the virtual environment:

```
python example.py
```

## Usage

```python
from bible_db import BibleDatabase

# Create a connection to the database
db = BibleDatabase()

# Set logging level to DEBUG, for detailed output of SQL queries
db.set_log_level("DEBUG")

# Get verses from YLT
verses = db.get_verses(ref="John 3:16", translation="YLT")

# Get all available translations
translations = db.get_available_translations()
```

## Available Translations

- KJV (King James Version)
- ASV (American Standard Version)
- BBE (Bible in Basic English)
- WEB (World English Bible)
- YLT (Young's Literal Translation)
