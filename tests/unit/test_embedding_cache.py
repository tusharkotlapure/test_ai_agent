
import numpy as np

from unittest.mock import patch

from devpilot.embeddings import (
    clear_embedding_cache,
    embed_texts,
)


def test_embedding_cache():
    clear_embedding_cache()

    fake_embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
    ])

    with patch(
        "devpilot.embeddings.get_embedding_model"
    ) as mock_get_model:
        mock_model = mock_get_model.return_value
        mock_model.encode.return_value = fake_embeddings

        first = embed_texts(["hello", "world"])
        second = embed_texts(["hello", "world"])
        third = embed_texts(["hello", "new"])

        assert np.array_equal(first, second)
        assert np.array_equal(third[0], first[0])

        # First call encodes two texts; third call encodes only "new".
        assert mock_model.encode.call_count == 2
        assert mock_model.encode.call_args_list[1].args[0] == ["new"]

    clear_embedding_cache()
    print("Embedding cache test passed")


if __name__ == "__main__":
    test_embedding_cache()
