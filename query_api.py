# -*- coding: utf-8 -*-
"""query_api.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NU5YM59MlpC9ulPT__NIW3fW6fHd0IeO
"""

from flask import Flask, request, jsonify
from transformers import TFAutoModel, AutoTokenizer
from pinecone import Pinecone
import tensorflow as tf

app = Flask(__name__)

model_name = "sentence-transformers/distiluse-base-multilingual-cased-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
tf_model = TFAutoModel.from_pretrained(model_name)

print("Model and tokenizer successfully loaded!")

from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(
    api_key="pcsk_5dUkk6_C9U9wDrh339aAZwzekpGVKHHGU2Zsq4FGSPCvo5FWhShFJ67oQg5yxPF4WgvmfH"
)
index_name = "cultural-insights"

index = pc.Index(index_name)
print("Pinecone initialized successfully!")

def generate_query_embedding(user_query):
    inputs = tokenizer(user_query, padding=True, truncation=True, return_tensors="tf")
    outputs = tf_model(**inputs)
    query_embedding = outputs.last_hidden_state[:, 0, :].numpy()[0]
    return query_embedding

def query_pinecone(query_embedding, top_k=3):
    results = index.query(
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )
    contexts = [
        {
            "score": match["score"],
            "metadata": match["metadata"]
        }
        for match in results["matches"]
    ]
    return contexts

@app.route('/query', methods=['POST'])
def query_endpoint():
    try:
        data = request.json
        user_query = data.get('query')
        if not user_query:
            return jsonify({"error": "Query is required"}), 400

        query_embedding = generate_query_embedding(user_query)
        contexts = query_pinecone(query_embedding)

        return jsonify({"contexts": contexts}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500