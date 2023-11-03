# Team Project Repository

This repository contains the codebase for our team project, which involves interacting with the Spotify and Genius APIs to create a music-related application.

[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/Wednesday-Fall2023-Team-1.svg?branch=develop)](https://app.travis-ci.com/gcivil-nyu-org/Wednesday-Fall2023-Team-1)

[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/Wednesday-Fall2023-Team-1/badge.svg?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/Wednesday-Fall2023-Team-1?branch=develop)

## Getting Started

### Prerequisites

Ensure you have Python and pip installed. The following packages are required:

- `django`: Web framework.
- `psycopg2_binary`: PostgreSQL adapter for Python.
- `spotipy`: A lightweight Python library for the Spotify Web API.
- `lyricsgenius`: A Python client for the Genius.com API.
- `python-dotenv`: A Python module that allows you to specify environment variables in traditional UNIX-like `.env` files.
- `plotly`: An interactive graphing library for Python
- `openai`
- `django-extensions`
- `supabase`

Install the prerequisites using pip:

```bash
pip install django psycopg2_binary spotipy lyricsgenius python-dotenv plotly openai django-extensions supabase
```
Install the Bootstrap-Icons using npm:

```bash
npm i bootstrap-icons
```

### Configuring API Credentials

#### Spotify API

1. **Retrieve API Credentials:**
   Obtain the `CLIENT_ID` and `CLIENT_SECRET` from your Spotify Developer Dashboard.

2. **Local Development:**
   - Create a `.env` file in the project root and add your Spotify API credentials:
     ```env
     SPOTIPY_CLIENT_ID=your_client_id
     SPOTIPY_CLIENT_SECRET=your_client_secret
     ```
   - Ensure `.env` is listed in your `.gitignore` file to prevent it from being tracked by Git.

   Example usage in code:
   ```python
   import os
   from dotenv import load_dotenv

   load_dotenv()

   CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
   CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
   ```

3. **Production Deployment:**
   Set the `CLIENT_ID` and `CLIENT_SECRET` directly in your production environment’s configuration.

#### Genius API

1. Replace the `GENIUS_CLIENT_ACCESS_TOKEN` in your `.env` file.

   Example usage:
   ```python
   import lyricsgenius
   import os
   from dotenv import load_dotenv

   load_dotenv()
   token = os.getenv('GENIUS_CLIENT_ACCESS_TOKEN')

   genius = lyricsgenius.Genius(token)
   song = genius.search_song("Fairy Fountain (Link to the Past)", "Juke Remix")
   print(song.lyrics)
   ```

#### OpenAI API
1. Replace the `OPEN_AI_TOKEN` in your `.env` file.

### For Collaborators

- Ensure to create your own `.env` file and populate it with your own Spotify, Genius, and OpenAI API credentials.
- Do check lines 11-15 in `vibecheck/settings.py` while working on your local machine.
- Before pushing `develop` branch into `master`, make sure the AWS Elastic Beanstalk environment is restarted with `Health:OK`. 

## Development and Usage

### Running the Django Application

[Include steps on running the Django app, applying migrations, creating a superuser, etc.]

### Interacting with APIs

[Details regarding API interactions, endpoints utilized, and any additional configurations or considerations should be documented here.]
