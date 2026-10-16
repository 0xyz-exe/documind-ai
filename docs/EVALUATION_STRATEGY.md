# Evaluation Strategy — DocuMind AI

## Purpose

Measure retrieval quality, citation integrity, and answer faithfulness.

## Evaluation Framework

### Test Dataset Structure

```json
{
  "name": "Contract QA Evaluation",
  "version": "1.0",
  "created": "2026-10-16",
  "documents": [
    {"id": 1, "filename": "contract_a.pdf", "hash": "sha256:..."}
  ],
  "questions": [
    {
      "id": 1,
      "question": "Can the contract be terminated early?",
      "expected_answer": "Yes, with 30 days written notice per Section 5.3",
      "relevant_document_ids": [1],
      "relevant_chunk_ids": [42],
      "relevant_pages": [3],
      "difficulty": "easy",
      "category": "factual"
    },
    {
      "id": 2,
      "question": "What is the penalty for late payment?",
      "expected_answer": "2% per month per Section 7.2",
      "relevant_document_ids": [1],
      "relevant_chunk_ids": [58],
      "relevant_pages": [5],
      "difficulty": "medium",
      "category": "factual"
    },
    {
      "id": 3,
      "question": "Who is the CEO of the company?",
      "expected_answer": null,
      "relevant_document_ids": [],
      "relevant_chunk_ids": [],
      "difficulty": "easy",
      "category": "unanswerable"
    }
  ]
}
```

### Question Categories

1. **Factual:** Direct answer in documents
2. **Inferential:** Requires reasoning over multiple chunks
3. **Unanswerable:** No relevant information in corpus

### Difficulty Levels

- **Easy:** Single chunk, direct match
- **Medium:** Multiple chunks or paraphrased
- **Hard:** Requires cross-document reasoning

## Metrics

### 1. Retrieval Recall@K

**Definition:** % of relevant chunks retrieved in top-k

**Formula:**
```
Recall@K = (# relevant chunks in top-K) / (# total relevant chunks)
```

**Implementation:**
```python
def recall_at_k(retrieved_chunk_ids: list[int], relevant_chunk_ids: list[int], k: int) -> float:
    if not relevant_chunk_ids:
        return 1.0  # No relevant chunks = perfect recall
    
    top_k = retrieved_chunk_ids[:k]
    relevant_retrieved = set(top_k) & set(relevant_chunk_ids)
    
    return len(relevant_retrieved) / len(relevant_chunk_ids)
```

**Target:** >70% Recall@5 for easy questions

### 2. Retrieval Precision@K

**Definition:** % of retrieved chunks that are relevant

**Formula:**
```
Precision@K = (# relevant chunks in top-K) / K
```

**Implementation:**
```python
def precision_at_k(retrieved_chunk_ids: list[int], relevant_chunk_ids: list[int], k: int) -> float:
    if not retrieved_chunk_ids:
        return 0.0
    
    top_k = retrieved_chunk_ids[:k]
    relevant_retrieved = set(top_k) & set(relevant_chunk_ids)
    
    return len(relevant_retrieved) / len(top_k)
```

**Target:** >40% Precision@5

### 3. Mean Reciprocal Rank (MRR)

**Definition:** Average of 1/rank of first relevant chunk

**Formula:**
```
MRR = (1/N) * Σ (1 / rank_i)
```

**Implementation:**
```python
def mean_reciprocal_rank(retrieved_chunk_ids: list[int], relevant_chunk_ids: list[int]) -> float:
    for i, chunk_id in enumerate(retrieved_chunk_ids, start=1):
        if chunk_id in relevant_chunk_ids:
            return 1.0 / i
    return 0.0  # No relevant chunk found
```

**Target:** >0.5 MRR

### 4. Citation Precision

**Definition:** % of citations that reference real retrieved chunks

**Formula:**
```
Citation Precision = (# valid citations) / (# total citations)
```

**Implementation:**
```python
def citation_precision(answer: str, retrieved_chunk_count: int) -> float:
    citations = extract_citations(answer)  # [1, 2, 3, ...]
    
    if not citations:
        return 1.0  # No citations = no fabrication
    
    valid_range = range(1, retrieved_chunk_count + 1)
    valid_citations = [c for c in citations if c in valid_range]
    
    return len(valid_citations) / len(citations)
```

**Target:** 100% (hard requirement)

### 5. Answer Faithfulness

**Definition:** Answer supported by retrieved evidence

**Method:** LLM-as-judge

**Prompt:**
```
Given the following sources and answer, rate how well the answer is supported by the sources.

SOURCES:
[1] <chunk 1 text>
[2] <chunk 2 text>

ANSWER:
<answer text>

Rate the faithfulness on a scale of 1-5:
1 = Completely contradicts sources or fabricated
2 = Partially supported but includes unsupported claims
3 = Mostly supported with minor additions
4 = Well supported with clear citations
5 = Perfectly grounded in sources

Rating: <1-5>
Reasoning: <brief explanation>
```

**Implementation:**
```python
def evaluate_faithfulness(sources: list[str], answer: str, judge_llm) -> float:
    prompt = build_faithfulness_prompt(sources, answer)
    response = judge_llm.generate(prompt)
    
    # Parse rating
    match = re.search(r'Rating:\s*(\d)', response)
    if match:
        rating = int(match.group(1))
        return rating / 5.0  # Normalize to 0-1
    
    return 0.0
```

**Target:** >0.8 (4/5 average)

### 6. Abstention Rate

**Definition:** % of unanswerable questions where system abstains

**Formula:**
```
Abstention Accuracy = (# correct abstentions) / (# unanswerable questions)
```

**Detection:**
```python
def is_abstention(answer: str) -> bool:
    abstention_phrases = [
        "don't have enough information",
        "sources don't contain",
        "can't find relevant information",
        "insufficient evidence"
    ]
    
    answer_lower = answer.lower()
    return any(phrase in answer_lower for phrase in abstention_phrases)
```

**Target:** >80% correct abstentions

## Evaluation Run

### Execution

```python
# app/services/evaluation.py

class EvaluationService:
    def __init__(self, qa_service: QAService):
        self.qa = qa_service
    
    def run_evaluation(
        self,
        db: Session,
        dataset: dict
    ) -> dict:
        results = []
        
        for question in dataset["questions"]:
            # Run QA
            response = self.qa.ask(db, question["question"])
            
            # Extract retrieved chunk IDs
            retrieved_ids = [c["chunk_id"] for c in response["citations"]]
            
            # Compute metrics
            recall = recall_at_k(
                retrieved_ids,
                question["relevant_chunk_ids"],
                k=5
            )
            
            precision = precision_at_k(
                retrieved_ids,
                question["relevant_chunk_ids"],
                k=5
            )
            
            mrr = mean_reciprocal_rank(
                retrieved_ids,
                question["relevant_chunk_ids"]
            )
            
            citation_prec = citation_precision(
                response["answer"],
                len(response["citations"])
            )
            
            faithfulness = evaluate_faithfulness(
                [c["excerpt"] for c in response["citations"]],
                response["answer"],
                self.qa.llm
            )
            
            is_unanswerable = not question["relevant_chunk_ids"]
            abstained = is_abstention(response["answer"])
            abstention_correct = (is_unanswerable == abstained)
            
            results.append({
                "question_id": question["id"],
                "question": question["question"],
                "answer": response["answer"],
                "retrieved_chunks": len(retrieved_ids),
                "recall_at_5": recall,
                "precision_at_5": precision,
                "mrr": mrr,
                "citation_precision": citation_prec,
                "faithfulness": faithfulness,
                "abstention_correct": abstention_correct
            })
        
        # Aggregate metrics
        aggregate = {
            "recall_at_5": np.mean([r["recall_at_5"] for r in results]),
            "precision_at_5": np.mean([r["precision_at_5"] for r in results]),
            "mrr": np.mean([r["mrr"] for r in results]),
            "citation_precision": np.mean([r["citation_precision"] for r in results]),
            "faithfulness": np.mean([r["faithfulness"] for r in results]),
            "abstention_accuracy": np.mean([r["abstention_correct"] for r in results])
        }
        
        return {
            "dataset": dataset["name"],
            "total_questions": len(results),
            "aggregate_metrics": aggregate,
            "per_question_results": results
        }
```

### Baseline Results (Expected)

**Random Retrieval:**
- Recall@5: ~10%
- Precision@5: ~5%
- MRR: ~0.05

**No Citation LLM:**
- Citation Precision: 0%

**Always Answer:**
- Abstention Accuracy: 0%

### Target Results (MVP)

- Recall@5: >60%
- Precision@5: >40%
- MRR: >0.5
- Citation Precision: 100%
- Faithfulness: >80%
- Abstention Accuracy: >80%

## Ablation Studies

### Test Configuration Impact

**Vary:**
1. Embedding model (MiniLM vs mpnet)
2. Chunk size (200, 500, 1000 tokens)
3. Chunk overlap (0, 50, 100 tokens)
4. Top-k (3, 5, 10)
5. Retrieval method (semantic, keyword, hybrid)
6. LLM model (gpt-3.5, gpt-4)
7. Temperature (0.0, 0.1, 0.5)

**Hold constant:** Test dataset, evaluation metrics

## Regression Testing

**After changes, verify:**
- Citation Precision ≥ 100% (hard gate)
- Recall@5 not decreased >5%
- No new failures on passing questions

## Error Analysis

**For failed questions:**
1. Categorize failure mode:
   - Retrieval miss (relevant chunk not retrieved)
   - Retrieval noise (irrelevant chunks ranked high)
   - Generation hallucination (fabricated info)
   - Citation error (invalid reference)
   - Abstention error (answered unanswerable or vice versa)

2. Root cause:
   - Query-document mismatch (paraphrasing, synonyms)
   - Chunk boundary splits key info
   - Multi-hop reasoning required
   - Ambiguous question
   - Missing context

3. Remediation:
   - Improve chunking strategy
   - Add keyword fallback
   - Tune similarity threshold
   - Improve system prompt
   - Add question clarification

## Continuous Evaluation

**Triggers:**
- Code change (pre-merge gate)
- Config change (chunk size, model)
- Weekly scheduled run
- After document re-indexing

**Alerts:**
- Citation Precision < 100%
- Recall@5 drop >10%
- Faithfulness < 70%

## Human Evaluation (P1)

**Sample 50 random Q&A pairs, rate:**
1. Answer correctness (1-5)
2. Citation relevance (1-5)
3. Clarity (1-5)

**Inter-rater agreement:** Cohen's kappa > 0.6

---

**Status:** Design complete. Datasets TBD post-MVP.
