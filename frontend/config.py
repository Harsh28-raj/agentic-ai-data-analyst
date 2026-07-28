import os

def get_backend_url():
    """
    Detects if the app is running inside Docker or locally and returns the correct backend URL.
    Returns:
        str: The backend URL.
    """
    # If the user explicitly sets BACKEND_URL in .env or environment, respect it first
    env_url = os.environ.get("BACKEND_URL")
    if env_url:
        # If running locally, don't use 'backend:8000' even if it's set in .env (like from docker-compose)
        if "backend" in env_url and not os.path.exists("/.dockerenv"):
            return "http://localhost:8000"
        return env_url

    # Automatic detection
    if os.path.exists("/.dockerenv"):
        # Running inside Docker, use the docker-compose service name
        return "http://backend:8000"
    else:
        # Running locally
        return "http://localhost:8000"

BACKEND_URL = get_backend_url()
