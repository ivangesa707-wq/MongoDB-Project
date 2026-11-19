"""
Shared helper utilities.
"""
import math
from datetime import datetime, timezone
from bson import ObjectId


# ── Pagination ──────────────────────────────────────────────────────────────

class Pagination:
    def __init__(self, total: int, page: int, per_page: int):
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = max(1, math.ceil(total / per_page))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1

    def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (self.page - left_current - 1 < num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


# ── Date/time helpers ────────────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def fmt_date(dt) -> str:
    if not dt:
        return "—"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%d %b %Y")


def fmt_datetime(dt) -> str:
    if not dt:
        return "—"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%d %b %Y, %H:%M")


# ── ObjectId helpers ─────────────────────────────────────────────────────────

def to_oid(value):
    """Convert string to ObjectId, or return None on failure."""
    try:
        return ObjectId(str(value))
    except Exception:
        return None


# ── Query helpers ────────────────────────────────────────────────────────────

def build_sort(sort_param: str, default: str = "created_at"):
    """Return (field, direction) tuple for pymongo sort."""
    if sort_param and sort_param.startswith("-"):
        return sort_param[1:], -1
    return (sort_param or default), 1


def paginate_cursor(cursor, page: int, per_page: int):
    """Slice a pymongo cursor and return (docs, total)."""
    total = cursor.count() if hasattr(cursor, "count") else 0
    docs = list(cursor.skip((page - 1) * per_page).limit(per_page))
    return docs, total
