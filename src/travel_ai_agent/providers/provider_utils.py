import time

def with_retry(fn, max_retries=1, timeout_seconds=15):
    """Call fn, retry once on failure. SerpAPI timeout set externally."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == max_retries:
                raise
