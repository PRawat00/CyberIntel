"""Tests for CVE Embedder."""

import numpy as np
import pytest

from llm_engine.embedder import CVEEmbedder


@pytest.fixture
def embedder():
    """Create a CVEEmbedder instance for testing."""
    return CVEEmbedder()


class TestCVEEmbedder:
    """Test suite for CVEEmbedder class."""

    def test_model_loading(self, embedder):
        """Test that the model loads successfully."""
        assert embedder.model is not None
        assert embedder.model_name == "all-MiniLM-L6-v2"
        assert embedder.embedding_dim == 384

    def test_embedding_dimension(self, embedder):
        """Test that embeddings have correct dimension."""
        text = "SQL injection vulnerability"
        embedding = embedder.embed(text)

        assert embedding.shape == (1, 384)
        assert isinstance(embedding, np.ndarray)

    def test_embed_single_text(self, embedder):
        """Test embedding generation for single text."""
        text = "Cross-site scripting (XSS) vulnerability in web application"
        embedding = embedder.embed(text)

        # Check shape
        assert embedding.shape == (1, 384)

        # Check it's not all zeros (actual embedding generated)
        assert np.any(embedding != 0)

        # Check values are reasonable (normalized embeddings typically in [-1, 1])
        assert np.all(np.abs(embedding) <= 2)

    def test_embed_batch(self, embedder):
        """Test batch embedding generation."""
        texts = [
            "SQL injection vulnerability",
            "Cross-site scripting (XSS)",
            "Remote code execution (RCE)",
            "Authentication bypass",
        ]

        embeddings = embedder.embed(texts, batch_size=2)

        # Check shape
        assert embeddings.shape == (4, 384)

        # Check all embeddings are different
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                # Embeddings should be different (cosine similarity < 1)
                similarity = embedder.similarity(embeddings[i], embeddings[j])
                assert similarity < 0.99  # Not identical

    def test_embed_empty_input(self, embedder):
        """Test handling of empty inputs."""
        # Empty string
        embedding = embedder.embed("")
        assert embedding.shape == (0,)  # Returns empty array

        # Empty list
        embeddings = embedder.embed([])
        assert embeddings.shape == (0,)

        # List with empty strings
        embeddings = embedder.embed(["", "", ""])
        assert embeddings.shape == (3, 384)
        # Should be zero vectors
        assert np.allclose(embeddings, 0)

    def test_embed_none_input(self, embedder):
        """Test handling of None inputs."""
        # Single None
        embeddings = embedder.embed([None, "valid text", None])

        assert embeddings.shape == (3, 384)
        # None entries should be zero vectors
        assert np.allclose(embeddings[0], 0)
        assert np.allclose(embeddings[2], 0)
        # Valid text should have non-zero embedding
        assert np.any(embeddings[1] != 0)

    def test_embed_cve_description(self, embedder):
        """Test CVE-specific embedding with preprocessing."""
        description = "A vulnerability in the authentication module allows remote attackers to bypass security controls."

        embedding = embedder.embed_cve_description(description)

        # Should return 1D array (single embedding)
        assert embedding.shape == (384,)
        assert np.any(embedding != 0)

    def test_embed_long_text(self, embedder):
        """Test handling of very long text (>512 tokens)."""
        # Create very long description (simulate CVE with lots of detail)
        long_description = " ".join(
            ["This is a very detailed CVE description." for _ in range(200)]
        )

        # Should not crash, should truncate
        embedding = embedder.embed_cve_description(long_description, max_length=512)

        assert embedding.shape == (384,)
        assert np.any(embedding != 0)

    def test_embed_cves_batch(self, embedder):
        """Test batch processing of CVE descriptions."""
        descriptions = [
            "SQL injection in login form",
            "XSS vulnerability in comment system",
            "Buffer overflow in image parser",
            "Path traversal in file upload",
            "Privilege escalation in admin panel",
        ]

        embeddings = embedder.embed_cves_batch(descriptions, batch_size=2)

        assert embeddings.shape == (5, 384)

        # All should be non-zero
        for i in range(5):
            assert np.any(embeddings[i] != 0)

    def test_similarity(self, embedder):
        """Test cosine similarity calculation."""
        # Create two embeddings
        text1 = "SQL injection vulnerability"
        text2 = "SQL injection attack"
        text3 = "Cross-site scripting XSS"

        emb1 = embedder.embed(text1).squeeze()
        emb2 = embedder.embed(text2).squeeze()
        emb3 = embedder.embed(text3).squeeze()

        # Similar texts should have high similarity
        sim_12 = embedder.similarity(emb1, emb2)
        assert sim_12 > 0.7  # Very similar

        # Different texts should have lower similarity
        sim_13 = embedder.similarity(emb1, emb3)
        assert sim_13 < sim_12  # Less similar

        # Similarity should be in [-1, 1]
        assert -1 <= sim_12 <= 1
        assert -1 <= sim_13 <= 1

    def test_similarity_identical(self, embedder):
        """Test similarity of identical embeddings."""
        text = "Authentication bypass vulnerability"
        emb = embedder.embed(text).squeeze()

        # Self-similarity should be ~1.0
        sim = embedder.similarity(emb, emb)
        assert 0.99 < sim <= 1.0

    def test_similarity_zero_vectors(self, embedder):
        """Test similarity with zero vectors."""
        zero_vec = np.zeros(384)
        valid_emb = embedder.embed("test").squeeze()

        # Similarity with zero vector should be 0
        sim = embedder.similarity(zero_vec, valid_emb)
        assert sim == 0.0

        # Two zero vectors
        sim = embedder.similarity(zero_vec, zero_vec)
        assert sim == 0.0

    def test_embed_special_characters(self, embedder):
        """Test handling of special characters."""
        texts = [
            "SQL injection: SELECT * FROM users WHERE id='1' OR '1'='1'",
            "<script>alert('XSS')</script>",
            "../../etc/passwd",
            "rm -rf / --no-preserve-root",
        ]

        embeddings = embedder.embed(texts)

        assert embeddings.shape == (4, 384)
        # All should generate valid embeddings
        for i in range(4):
            assert np.any(embeddings[i] != 0)

    def test_repr(self, embedder):
        """Test string representation."""
        repr_str = repr(embedder)
        assert "CVEEmbedder" in repr_str
        assert "all-MiniLM-L6-v2" in repr_str
        assert "384" in repr_str

    def test_embed_unicode(self, embedder):
        """Test handling of unicode characters."""
        texts = [
            "Vulnerabilité de sécurité",  # French
            "セキュリティの脆弱性",  # Japanese
            "Уязвимость безопасности",  # Russian
            "安全漏洞",  # Chinese
        ]

        embeddings = embedder.embed(texts)

        assert embeddings.shape == (4, 384)
        for i in range(4):
            assert np.any(embeddings[i] != 0)

    def test_batch_size_larger_than_data(self, embedder):
        """Test batch processing when batch_size > number of texts."""
        texts = ["CVE 1", "CVE 2"]

        # Batch size larger than data
        embeddings = embedder.embed(texts, batch_size=100)

        assert embeddings.shape == (2, 384)

    def test_embed_whitespace_only(self, embedder):
        """Test handling of whitespace-only strings."""
        texts = ["   ", "\t\t", "\n\n", "  \t  \n  "]

        embeddings = embedder.embed(texts)

        # Should return zero vectors for whitespace
        assert embeddings.shape == (4, 384)
        for i in range(4):
            assert np.allclose(embeddings[i], 0)

    def test_embed_mixed_valid_invalid(self, embedder):
        """Test batch with mix of valid and invalid inputs."""
        texts = [
            "Valid CVE description",
            "",
            None,
            "   ",
            "Another valid CVE",
        ]

        embeddings = embedder.embed(texts)

        assert embeddings.shape == (5, 384)

        # Valid entries should have embeddings
        assert np.any(embeddings[0] != 0)
        assert np.any(embeddings[4] != 0)

        # Invalid entries should be zero
        assert np.allclose(embeddings[1], 0)
        assert np.allclose(embeddings[2], 0)
        assert np.allclose(embeddings[3], 0)
