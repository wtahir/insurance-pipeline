import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="chroma_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_collection(
    name="insurance_claims",
    embedding_function=embedding_fn
)

results = collection.query(
    query_texts=["water damage claim"],
    n_results=3
)

for i, doc in enumerate(results["documents"][0]):
    print(f"\n--- Result {i+1} ---")
    print(doc[:300])
    print("Claim:", results["metadatas"][0][i].get("claim_number"))
    print("Urgency:", results["metadatas"][0][i].get("urgency"))


# results = collection.get(where={"urgency": "high"})
# print(len(results["ids"]))
# # %%
