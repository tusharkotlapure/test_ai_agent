
from unittest.mock import patch

from devpilot.index_cache import (
    CACHE_TTL_SECONDS,
    clear_index_cache,
    get_repository_index,
)


def test_repository_index_ttl():
    clear_index_cache()

    first_chunks = [{"path": "example.py", "text": "version 1"}]
    second_chunks = [{"path": "example.py", "text": "version 2"}]

    with (
        patch(
            "devpilot.index_cache.build_repository_index",
            side_effect=[first_chunks, second_chunks],
        ) as mock_build,
        patch("devpilot.index_cache.time.monotonic") as mock_clock,
    ):
        mock_clock.return_value = 100.0
        first = get_repository_index("example", "demo", ["example.py"])

        # Still fresh: reuse the first index.
        mock_clock.return_value = 100.0 + CACHE_TTL_SECONDS - 1
        second = get_repository_index("example", "demo", ["example.py"])

        assert first == first_chunks
        assert second == first_chunks
        assert mock_build.call_count == 1

        # Expired: rebuild the index.
        mock_clock.return_value = 100.0 + CACHE_TTL_SECONDS
        third = get_repository_index("example", "demo", ["example.py"])

        assert third == second_chunks
        assert mock_build.call_count == 2

    clear_index_cache()
    print("Repository index TTL test passed")


if __name__ == "__main__":
    test_repository_index_ttl()
