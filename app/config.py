"""
Application configuration loaded from environment variables.
Supports both local MongoDB and MongoDB Atlas URIs.
"""
import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()


def _format_mongo_uri(raw_uri: str, db_name: str) -> str:
    """Format MongoDB URI to ensure database name is correctly included."""
    if not raw_uri:
        raw_uri = "mongodb://localhost:27017"
    if not db_name:
        db_name = "gesaivan_market"

    raw_uri = raw_uri.strip()
    parsed = urlparse(raw_uri)
    path = parsed.path.strip("/")

    # If database is not present in path, insert it before query parameters
    if not path:
        new_path = f"/{db_name}"
        return urlunparse(parsed._replace(path=new_path))
    return raw_uri


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-secret")
    _RAW_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    _DB_NAME = os.environ.get("MONGO_DB", "gesaivan_market")
    MONGO_URI = _format_mongo_uri(_RAW_URI, _DB_NAME)

    # Pagination
    ITEMS_PER_PAGE = 10

