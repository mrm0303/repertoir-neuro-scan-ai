import os
import struct
import math

try:
    from PIL import Image
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_AI = True
except ImportError:
    HAS_AI = False

_model = None

def get_model():
    global _model
    if _model is None and HAS_AI:
        # clip-ViT-B-32 is fast and effective for standard zero-shot image/text retrieval
        try:
            import warnings
            warnings.filterwarnings("ignore")
            _model = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            print("Erreur chargement modèle AI:", e)
            return None
    return _model

def encode_image(image_path):
    if not HAS_AI: return None
    model = get_model()
    if not model: return None
    try:
        img = Image.open(image_path)
        vec = model.encode(img)
        # normalize
        norm = np.linalg.norm(vec)
        if norm > 0: vec = vec / norm
        return vec.astype(np.float32)
    except Exception as e:
        print(f"Erreur encodage image {image_path}:", e)
        return None

def encode_text(text):
    if not HAS_AI: return None
    model = get_model()
    if not model: return None
    try:
        vec = model.encode(text)
        norm = np.linalg.norm(vec)
        if norm > 0: vec = vec / norm
        return vec.astype(np.float32)
    except Exception as e:
        print("Erreur encodage texte:", e)
        return None

def serialize_vector(vec):
    """Convertit un numpy array float32 en BLOB (bytes)."""
    if vec is None: return None
    return vec.tobytes()

def deserialize_vector(blob):
    """Convertit un BLOB en numpy array float32."""
    if not blob: return None
    if not HAS_AI: return None
    return np.frombuffer(blob, dtype=np.float32)

def compute_similarity(vec1, vec2):
    """Cosine similarity de deux vecteurs normalisés."""
    if vec1 is None or vec2 is None or not HAS_AI: return 0.0
    return float(np.dot(vec1, vec2))

