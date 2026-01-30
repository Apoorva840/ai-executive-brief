import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# ============================
# LOAD ARTICLES
# ============================

print("Loading articles...")

with open("data/raw_news.json", "r", encoding="utf-8") as f:
    articles = json.load(f)

print(f"Loaded {len(articles)} articles")

# Exit if no articles to process
if not articles:
    print("No articles to deduplicate. Exiting AI deduplication.")
    exit(0)

# ============================
# LOAD AI MODEL
# ============================

print("Loading FREE local AI model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [
    article["title"] + " " + article.get("summary", "")
    for article in articles
]

print("Generating embeddings...")
embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

# ============================
# AI-BASED DEDUPLICATION USING FAISS
# ============================

SIMILARITY_THRESHOLD = 0.85

# Normalize embeddings for cosine similarity
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

d = embeddings.shape[1]  # dimension of embeddings
index = faiss.IndexFlatIP(d)  # Inner product = cosine similarity after normalization
index.add(embeddings)

kept_indices = set()
all_indices = set(range(len(articles)))

print("Running AI-based deduplication with FAISS...")

for i in range(len(articles)):
    if i in kept_indices:
        continue

    # Query similar vectors (self + others)
    x = embeddings[i].reshape(1, -1).astype('float32')
    D, I = index.search(x, len(articles))  # get all similarities
    # I contains indices sorted by inner product (cosine similarity)

    for j, score in zip(I[0], D[0]):
        if score > SIMILARITY_THRESHOLD:
            kept_indices.add(j)
        else:
            break  # embeddings are sorted, so rest are below threshold

# Keep only first occurrence of each cluster
kept_articles = [articles[i] for i in sorted(kept_indices)]

# ============================
# SAVE DEDUPLICATED ARTICLES
# ============================

with open("data/deduped_news.json", "w", encoding="utf-8") as f:
    json.dump(kept_articles, f, indent=2, ensure_ascii=False)

print(f"After AI deduplication: {len(kept_articles)} articles")
print("AI deduplication completed successfully")
