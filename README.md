# Team Project Repository

This repository contains the codebase for our team project, which involves interacting with the Spotify and Genius APIs to create a music-related application.

## Getting Started

### Prerequisites

Ensure you have Python and pip installed. The following packages are required:

- `django`: Web framework.
- `psycopg2_binary`: PostgreSQL adapter for Python.
- `spotipy`: A lightweight Python library for the Spotify Web API.
- `lyricsgenius`: A Python client for the Genius.com API.
- `python-dotenv`: A Python module that allows you to specify environment variables in traditional UNIX-like `.env` files.

Install the prerequisites using pip:

```bash
pip install django psycopg2_binary spotipy lyricsgenius python-dotenv
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

### For Collaborators

Ensure to create your own `.env` file and populate it with your own Spotify and Genius API credentials.

## Development and Usage

### Running the Django Application

[Include steps on running the Django app, applying migrations, creating a superuser, etc.]

### Interacting with APIs

[Details regarding API interactions, endpoints utilized, and any additional configurations or considerations should be documented here.]