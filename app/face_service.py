import numpy as np

def euclidean(vec1, vec2) -> float:
    """Compute Euclidean distance between two embedding vectors."""
    v1, v2 = np.array(vec1), np.array(vec2)
    return float(np.linalg.norm(v1 - v2))
