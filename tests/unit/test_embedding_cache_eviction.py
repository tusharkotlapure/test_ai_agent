
from unittest.mock import patch

import numpy as np

import devpilot.embeddings as embeddings


def test_embedding_cache_evicts_least_recently_used():
    embeddings.clear_embedding_cache()

    with (
        patch.object(
            embeddings,
            "MAX_EMBEDDING_CACHE_SIZE",
            2,
        ),
        patch.object(
            embeddings,
            "get_embedding_model",
        ) as mock_get_model,
    ):
        mock_model = mock_get_model.return_value

        def fake_encode(texts, **kwargs):
            return np.array([
                [float(ord(text[0])), 1.0]
                for text in texts
            ])

        mock_model.encode.side_effect = fake_encode

        # Fill the cache: a, b
        embeddings.embed_texts(["a", "b"])
        assert list(embeddings._EMBEDDING_CACHE) == ["a", "b"]

        # Access a, making b the least recently used.
        embeddings.embed_texts(["a"])
        assert list(embeddings._EMBEDDING_CACHE) == ["b", "a"]

        # Add c; b should be evicted.
        embeddings.embed_texts(["c"])
        assert list(embeddings._EMBEDDING_CACHE) == ["a", "c"]

        # b was evicted, so it must be embedded again.
        embeddings.embed_texts(["b"])
        assert list(embeddings._EMBEDDING_CACHE) == ["c", "b"]
        assert mock_model.encode.call_count == 3

    embeddings.clear_embedding_cache()
    print("Embedding cache eviction test passed")


if __name__ == "__main__":
    test_embedding_cache_evicts_least_recently_used()
