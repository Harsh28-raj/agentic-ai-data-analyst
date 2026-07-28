import os


def get_backend_url():
    """
    Get backend URL for local and production.
    """
    return os.getenv("BACKEND_URL", "http://localhost:8000")


BACKEND_URL = get_backend_url()
