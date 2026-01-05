# 🏆 RAG in Production: Operations & Case Studies

Theory is great, but production is where the rubber meets the road. This section
curates deep-dive engineering blogs, whitepapers, and talks from companies
running Retrieval-Augmented Generation at scale.

> **Criteria:** We only include resources that discuss *architecture, latency,
> evaluation, or scaling challenges*. No marketing fluff.

---

## 🦄 High-Scale Consumer Apps

### **[Perplexity.ai](https://www.perplexity.ai/)**

- **[Perplexity's Online LLM Inference](https://www.perplexity.ai/blog/perplexity-70b-improving-on-llama-2-70b)**
  - Insights into serving 70B models with low latency for search.
  - *Key Takeaways:* Speculative decoding, aggressive caching, and search index optimization.

### **[Notion AI](https://www.notion.so/)**

- **[Design & Engineering behind Notion AI](https://www.notion.com/blog/how-we-built-notion-ai)**
  - How Notion integrated RAG into a collaborative workspace with millions of non-technical users.
  - *Key Takeaways:* Privacy-first architecture, context window management for large docs.

### **[Discord](https://discord.com/)**

- **[How Discord Scaled Vector Search](https://discord.com/blog/how-discord-stores-trillions-of-messages)**
  - Not strictly RAG, but a masterclass in handling trillions of vectors for retrieval
    (used in Clyde and search).
  - *Key Takeaways:* Rust-based microservices, ScyllaDB for metadata.

---

## 🏢 Enterprise & B2B

### **[Stripe](https://stripe.com/)**

- **[Stripe Radar & ML Infrastructure](https://stripe.com/blog/how-we-built-it-stripe-radar)**
  - Using embeddings for fraud detection (retrieval-based classification).
  - *Key Takeaways:* Real-time feature extraction, low-latency vector lookups.

### **[Airbnb](https://www.airbnb.com/)**

- **[Building Airbnb's AI Search](https://medium.com/airbnb-engineering/improving-deep-learning-for-search-at-airbnb-5415757912)**
  - The evolution of search ranking using embeddings.
  - *Key Takeaways:* Hard negative mining, custom listing embeddings.

---

## 🛠️ Lessons from the Trenches (Engineering Blogs)

- **[DoorDash] - [Personalized Store Feed with Vector Retrieval](https://doordash.engineering/2023/08/01/improving-store-feed-ranking-with-vector-retrieval/)**
  - *Focus:* Replacing heuristic rules with semantic retrieval for better recommendations.
- **[LinkedIn] - [Approximate Nearest Neighbor Search at Scale](https://engineering.linkedin.com/blog/2020/scaling-approximate-nearest-neighbor-search-with-galene)**
  - *Focus:* Custom ANN implementation (Galene) for massive scale.
- **[Pinterest] - [Pinsage: Graph Convolutional Networks](https://medium.com/pinterest-engineering/pinsage-a-new-graph-convolutional-network-for-web-scale-recommender-systems-887955e85fa3)**
  - *Focus:* Combining graph structures with embeddings (precursor to GraphRAG).

---

## 📹 Must-Watch Talks

- **[Building RAG at Enterprise Scale (NVIDIA)](https://www.youtube.com/watch?v=1F2b6k32b3U)**
  - Focus on security and governance.


---

([back to main resource](README.md#contents))
