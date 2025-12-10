import numpy as np
from sklearn.decomposition import PCA
from pathlib import Path
import joblib

PCA_PATH = Path("pca_2048_to_1998.pkl")
TARGET_DIM = 1998
ORIGINAL_DIM = 2048

_pca_model = None

def load_pca():
    global _pca_model
    if PCA_PATH.exists():
        _pca_model = joblib.load(PCA_PATH)
    return _pca_model

def train_pca(vectors_2048: list[list[float]]):
    global _pca_model

    arr = np.array(vectors_2048)
    pca = PCA(n_components=TARGET_DIM)
    pca.fit(arr)

    joblib.dump(pca, PCA_PATH)
    _pca_model = pca

def reduce_embedding(vec_2048: list[float]) -> list[float]:
    global _pca_model

    vec = np.array(vec_2048)

    if _pca_model is None:
        _pca_model = load_pca()

    if _pca_model is not None:
        reduced = _pca_model.transform(vec.reshape(1, -1))[0]
        return reduced.tolist()

    return vec[:TARGET_DIM].tolist()
