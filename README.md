# Team Project repo

for supabse and postgres client run, install
```pip install psycogp2_binary```

for Spotify API usage install
```pip install spotipy```

## Setup: Managing Environment Variables

### Overview
This project utilizes environment variables to securely manage sensitive information such as API keys, ensuring they are not exposed or tracked within the version control system.

### Using .env File for Local Development
1. **Create .env File:**
   Create a file named `.env` in the root of your project directory.

2. **Add Variables:**
   Inside the `.env` file, specify the `CLIENT_ID` and `CLIENT_SECRET` from the Spotify API.

   ```env
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   ```

   Replace `your_client_id` and `your_client_secret` with your actual Spotify API credentials.

3. **Ensure .env Is Ignored:**
   Make sure that your `.gitignore` file includes the `.env` file to prevent it from being tracked by Git.

   ```gitignore
   .env
   ```

### In Your Code
The application is configured to load these variables from the `.env` file using the `python-dotenv` package. If set up correctly, you should not need to make any adjustments in the codebase for local development.

```python
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
```

### For Collaborators
If you're collaborating on this project, ensure to create your own `.env` file and populate it with your own Spotify API credentials.

### Deployment Note
When deploying the application, make sure to set the `CLIENT_ID` and `CLIENT_SECRET` directly in your production environment’s configuration (not using the `.env` file) to ensure the security of your API credentials.