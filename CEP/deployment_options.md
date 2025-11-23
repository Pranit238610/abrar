# Deployment Options for AQI Alert System

Here are the best options for deploying your Django application, ranging from beginner-friendly to professional.

## 1. PythonAnywhere (Recommended for Beginners)
**Best for:** Simplicity and keeping SQLite.
- **Pros:**
    -   Supports SQLite out of the box (no need to switch to PostgreSQL).x
    -   Very easy to set up (upload code, run a few commands).
    -   Free tier available.
-   **Cons:**
    -   Free tier has limited CPU/bandwidth.
    -   No custom domain on free tier (yourname.pythonanywhere.com).
-   **Steps:**
    1.  Sign up.
    2.  Upload code (git clone or zip).
    3.  Create virtualenv.
    4.  Configure WSGI file.

## 2. Render (Modern Standard)
**Best for:** Professional workflow and scalability.
-   **Pros:**
    -   Modern, Git-based workflow (push to GitHub -> auto deploy).
    -   Free tier for web services and PostgreSQL.
    -   Great documentation.
-   **Cons:**
    -   **Ephemeral Filesystem:** You **MUST** switch from SQLite to PostgreSQL (Render provides a free Postgres DB).
    -   Free tier "spins down" after inactivity (slow first load).
-   **Steps:**
    1.  Add `gunicorn`, `psycopg2-binary`, `dj-database-url`, `whitenoise` to requirements.
    2.  Configure `settings.py` for Postgres and Static files.
    3.  Push to GitHub.
    4.  Connect Render to GitHub.

## 3. Railway
**Best for:** Developer experience and speed.
-   **Pros:**
    -   Extremely fast setup.
    -   Good free trial (credits).
    -   Handles database creation automatically.
-   **Cons:**
    -   Eventually becomes paid (usage-based).
    -   Requires Postgres (like Render).

## 4. Firebase (Advanced / Google Cloud)
**Best for:** Scalability and Google ecosystem integration.
**WARNING:** You cannot use SQLite. You MUST switch to PostgreSQL (Cloud SQL or Neon).
-   **Architecture:**
    -   **Frontend:** Firebase Hosting (serves static files).
    -   **Backend:** Cloud Run (runs Django container).
    -   **Database:** Cloud SQL (Postgres) or Neon.tech (Free Postgres).
-   **Pros:**
    -   Infinite scalability.
    -   Professional Google Cloud infrastructure.
-   **Cons:**
    -   **Most Complex Setup:** Requires Docker, gcloud CLI, and database configuration.
3.  **Static Files:** Install `whitenoise` to serve CSS/JS.
4.  **Environment Variables:** Hide your `SECRET_KEY` and `EMAIL_PASSWORD`.
