"""CVE Embedder - Generate semantic embeddings for CVE descriptions."""

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class CVEEmbedder:
    """Generate embeddings for CVE descriptions using sentence-transformers.

    Uses the all-MiniLM-L6-v2 model which provides a good balance of:
    - Speed: Fast inference even on CPU
    - Size: Only ~80MB model download
    - Quality: 384-dimensional embeddings with good semantic understanding

    The model is cached locally after first download.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedder with specified model.

        Args:
            model_name: HuggingFace model name. Default: all-MiniLM-L6-v2
                       Other options: all-mpnet-base-v2 (better quality, slower)
        """
        self.model_name = model_name
        logger.info(f"Loading sentence-transformers model: {model_name}")

        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def embed(self, text: str | list[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for text or list of texts.

        Args:
            text: Single text string or list of strings
            batch_size: Batch size for processing multiple texts (default: 32)

        Returns:
            numpy array of shape (n, embedding_dim) where n is number of input texts

        Examples:
            >>> embedder = CVEEmbedder()
            >>> embedding = embedder.embed("SQL injection vulnerability")
            >>> embedding.shape
            (384,)

            >>> embeddings = embedder.embed(["SQLi", "XSS", "RCE"])
            >>> embeddings.shape
            (3, 384)
        """
        if isinstance(text, str):
            text = [text]

        # Handle empty list
        if not text:
            logger.warning("Empty text list provided, returning empty array")
            return np.array([])

        # Filter out None/empty strings and track original indices
        valid_texts = []
        valid_indices = []
        for i, t in enumerate(text):
            if t and isinstance(t, str) and t.strip():
                valid_texts.append(t.strip())
                valid_indices.append(i)
            else:
                logger.warning(f"Skipping invalid text at index {i}: {repr(t)}")

        if not valid_texts:
            logger.warning("No valid texts to embed after filtering")
            return np.zeros((len(text), self.embedding_dim))

        try:
            # Generate embeddings
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                show_progress_bar=len(valid_texts) > 100,
                convert_to_numpy=True,
            )

            # If we filtered some texts, create full array with zeros for invalid entries
            if len(valid_texts) < len(text):
                full_embeddings = np.zeros((len(text), self.embedding_dim))
                for valid_idx, original_idx in enumerate(valid_indices):
                    full_embeddings[original_idx] = embeddings[valid_idx]
                embeddings = full_embeddings

            logger.info(f"Generated embeddings for {len(valid_texts)}/{len(text)} texts")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_cve_description(self, description: str, max_length: int = 512) -> np.ndarray:
        """Generate embedding for a CVE description with preprocessing.

        CVE descriptions can be very long. This method:
        1. Truncates to max_length tokens (model limit is ~512)
        2. Handles special cases (None, empty, very short)

        Args:
            description: CVE description text
            max_length: Maximum tokens to process (default: 512)

        Returns:
            numpy array of shape (embedding_dim,)
        """
        if not description or not isinstance(description, str):
            logger.warning(f"Invalid CVE description: {repr(description)}, returning zero vector")
            return np.zeros(self.embedding_dim)

        # Truncate long descriptions (rough token estimation: 1 token ≈ 4 chars)
        char_limit = max_length * 4
        if len(description) > char_limit:
            description = description[:char_limit]
            logger.debug(f"Truncated long description to {char_limit} characters")

        return self.embed(description).squeeze()

    def embed_cves_batch(
        self, descriptions: list[str], batch_size: int = 32, max_length: int = 512
    ) -> np.ndarray:
        """Generate embeddings for multiple CVE descriptions.

        Optimized for batch processing many CVEs at once.

        Args:
            descriptions: List of CVE description texts
            batch_size: Batch size for encoding (default: 32)
            max_length: Maximum tokens per description (default: 512)

        Returns:
            numpy array of shape (n, embedding_dim)
        """
        # Preprocess descriptions
        processed = []
        for desc in descriptions:
            if not desc or not isinstance(desc, str):
                processed.append("")
            else:
                char_limit = max_length * 4
                processed.append(desc[:char_limit] if len(desc) > char_limit else desc)

        return self.embed(processed, batch_size=batch_size)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def __repr__(self) -> str:
        return f"CVEEmbedder(model={self.model_name}, dim={self.embedding_dim})"
