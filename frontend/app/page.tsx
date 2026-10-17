"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type DocumentItem = { id: number; filename: string; status: string; page_count?: number };
type SearchResult = { document_name: string; text: string; score: number };
type QAResult = { answer: string; citations: { document_name: string; excerpt: string }[] };

export default function Home() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<QAResult | null>(null);
  const [message, setMessage] = useState("");

  async function loadDocuments() {
    const response = await fetch(`${API_URL}/api/v1/documents`);
    if (!response.ok) throw new Error("Could not load documents");
    setDocuments((await response.json()).documents);
  }

  useEffect(() => {
    loadDocuments().catch((error: Error) => setMessage(error.message));
  }, []);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    const response = await fetch(`${API_URL}/api/v1/documents`, { method: "POST", body });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail ?? "Upload failed");
      return;
    }
    setMessage(`${data.filename} is indexed and ready.`);
    await loadDocuments();
  }

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    const response = await fetch(`${API_URL}/api/v1/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail ?? "Search failed");
      return;
    }
    setResults(data.results);
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    const response = await fetch(`${API_URL}/api/v1/qa/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail ?? "Question failed");
      return;
    }
    setAnswer(data);
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">PRIVATE DOCUMENT INTELLIGENCE</p>
        <h1>Ask your documents.</h1>
        <p className="subtitle">Upload locally, search instantly, and get answers grounded in your files.</p>
      </header>

      <section className="card upload">
        <div>
          <h2>Your library</h2>
          <p>{documents.length} document{documents.length === 1 ? "" : "s"} indexed</p>
        </div>
        <label className="button">
          Upload document
          <input type="file" accept=".pdf,.docx,.txt,.md" onChange={upload} />
        </label>
        {documents.length > 0 && <ul>{documents.map((doc) => <li key={doc.id}>{doc.filename} <span>{doc.status}</span></li>)}</ul>}
      </section>

      <section className="grid">
        <div className="card">
          <h2>Search</h2>
          <form onSubmit={search} className="form">
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your documents..." />
            <button type="submit">Search</button>
          </form>
          {results.map((result, index) => <article className="result" key={`${result.document_name}-${index}`}><strong>{result.document_name}</strong><small>{Math.round(result.score * 100)}% match</small><p>{result.text}</p></article>)}
        </div>
        <div className="card">
          <h2>Ask a question</h2>
          <form onSubmit={ask} className="form">
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What do the documents say?" rows={4} />
            <button type="submit">Ask</button>
          </form>
          {answer && <div className="answer"><p>{answer.answer}</p>{answer.citations.map((citation, index) => <small key={index}>[{index + 1}] {citation.document_name}: {citation.excerpt}</small>)}</div>}
        </div>
      </section>
      {message && <p className="message">{message}</p>}
    </main>
  );
}
