"""
Script to generate all 11 SVG diagrams for NexusRAG Interview Handbook.
"""
import os

DOCS_DIR = r"D:\Academic-Projects\RAG\docs\interview"
NEXUS_DIR = r"D:\Academic-Projects\RAG\NexusRag\docs\interview"

SVG_COVER_ABSTRACT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 280" width="100%" height="280">
  <defs>
    <linearGradient id="covBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0F172A" />
      <stop offset="50%" stop-color="#1E1B4B" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>
    <linearGradient id="covNodeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#818CF8" />
      <stop offset="100%" stop-color="#C084FC" />
    </linearGradient>
    <linearGradient id="covLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#4F46E5" stop-opacity="0.3" />
      <stop offset="50%" stop-color="#818CF8" stop-opacity="0.8" />
      <stop offset="100%" stop-color="#C084FC" stop-opacity="0.3" />
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <rect width="800" height="280" rx="14" fill="url(#covBg)" />
  
  <!-- Subtle Grid -->
  <g opacity="0.08" stroke="#FFFFFF" stroke-width="1">
    <line x1="0" y1="70" x2="800" y2="70" />
    <line x1="0" y1="140" x2="800" y2="140" />
    <line x1="0" y1="210" x2="800" y2="210" />
    <line x1="160" y1="0" x2="160" y2="280" />
    <line x1="320" y1="0" x2="320" y2="280" />
    <line x1="480" y1="0" x2="480" y2="280" />
    <line x1="640" y1="0" x2="640" y2="280" />
  </g>

  <!-- Constellation Network Edges -->
  <g stroke="url(#covLineGrad)" stroke-width="1.5" stroke-dasharray="4,4">
    <line x1="100" y1="140" x2="220" y2="80" />
    <line x1="100" y1="140" x2="220" y2="200" />
    <line x1="220" y1="80" x2="360" y2="140" />
    <line x1="220" y1="200" x2="360" y2="140" />
    <line x1="360" y1="140" x2="480" y2="80" />
    <line x1="360" y1="140" x2="480" y2="200" />
    <line x1="480" y1="80" x2="620" y2="140" />
    <line x1="480" y1="200" x2="620" y2="140" />
    <line x1="620" y1="140" x2="720" y2="140" />
    <line x1="220" y1="80" x2="480" y2="80" opacity="0.4" />
    <line x1="220" y1="200" x2="480" y2="200" opacity="0.4" />
  </g>

  <!-- Vector Field Waves -->
  <path d="M 50 140 Q 200 40 350 140 T 650 140 T 750 140" fill="none" stroke="#6366F1" stroke-width="2" opacity="0.4" />
  <path d="M 50 140 Q 200 240 350 140 T 650 140 T 750 140" fill="none" stroke="#A855F7" stroke-width="2" opacity="0.3" />

  <!-- Nodes with Glowing Centers -->
  <!-- Node 1: Raw Knowledge -->
  <g transform="translate(100, 140)">
    <circle r="22" fill="#1E293B" stroke="#818CF8" stroke-width="2" filter="url(#glow)" />
    <circle r="10" fill="#4F46E5" />
    <text y="38" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="10" font-weight="700" text-anchor="middle">INGESTION</text>
    <text y="50" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="8" text-anchor="middle">PDF/TXT/MD</text>
  </g>

  <!-- Node 2: Chunks -->
  <g transform="translate(220, 80)">
    <circle r="18" fill="#1E293B" stroke="#6366F1" stroke-width="2" />
    <circle r="7" fill="#6366F1" />
    <text y="32" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="9" font-weight="600" text-anchor="middle">CHUNKING</text>
    <text y="42" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="7.5" text-anchor="middle">800 / 100 char</text>
  </g>

  <!-- Node 3: Cache -->
  <g transform="translate(220, 200)">
    <circle r="18" fill="#1E293B" stroke="#10B981" stroke-width="2" />
    <circle r="7" fill="#10B981" />
    <text y="32" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="9" font-weight="600" text-anchor="middle">REDIS CACHE</text>
    <text y="42" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="7.5" text-anchor="middle">TTL 3600s</text>
  </g>

  <!-- Node 4: Dense Vectors (Core Hub) -->
  <g transform="translate(360, 140)">
    <circle r="30" fill="#1E1B4B" stroke="url(#covNodeGlow)" stroke-width="3" filter="url(#glow)" />
    <circle r="14" fill="#818CF8" />
    <text y="46" fill="#F8FAFC" font-family="'Inter', sans-serif" font-size="11" font-weight="800" text-anchor="middle">DENSE VECTORS</text>
    <text y="58" fill="#C7D2FE" font-family="'JetBrains Mono', monospace" font-size="8" text-anchor="middle">768-DIM CHROMADB</text>
  </g>

  <!-- Node 5: Similarity Search -->
  <g transform="translate(480, 80)">
    <circle r="18" fill="#1E293B" stroke="#A855F7" stroke-width="2" />
    <circle r="7" fill="#A855F7" />
    <text y="32" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="9" font-weight="600" text-anchor="middle">RETRIEVAL</text>
    <text y="42" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="7.5" text-anchor="middle">Top-K = 4 L2</text>
  </g>

  <!-- Node 6: Grounding Prompt -->
  <g transform="translate(480, 200)">
    <circle r="18" fill="#1E293B" stroke="#EC4899" stroke-width="2" />
    <circle r="7" fill="#EC4899" />
    <text y="32" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="9" font-weight="600" text-anchor="middle">PROMPT</text>
    <text y="42" fill="#94A3B8" font-family="'JetBrains Mono', monospace" font-size="7.5" text-anchor="middle">Anti-Hallucination</text>
  </g>

  <!-- Node 7: Reasoning Engine (LLM) -->
  <g transform="translate(620, 140)">
    <circle r="24" fill="#1E293B" stroke="#F59E0B" stroke-width="2.5" filter="url(#glow)" />
    <circle r="11" fill="#F59E0B" />
    <text y="40" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="10" font-weight="700" text-anchor="middle">GEMINI 2.5</text>
    <text y="52" fill="#FCD34D" font-family="'JetBrains Mono', monospace" font-size="8" text-anchor="middle">via OpenRouter</text>
  </g>

  <!-- Node 8: Grounded Output -->
  <g transform="translate(730, 140)">
    <circle r="16" fill="#1E293B" stroke="#10B981" stroke-width="2" />
    <circle r="7" fill="#10B981" />
    <text y="30" fill="#E2E8F0" font-family="'Inter', sans-serif" font-size="9" font-weight="700" text-anchor="middle">CITATIONS</text>
    <text y="40" fill="#6EE7B7" font-family="'JetBrains Mono', monospace" font-size="7.5" text-anchor="middle">Page-Level</text>
  </g>
</svg>"""

SVG_DIAGRAM_A = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 440" width="100%" height="440">
  <defs>
    <linearGradient id="layerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F8FAFC" />
      <stop offset="100%" stop-color="#F1F5F9" />
    </linearGradient>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <marker id="arrowIndigo" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#4F46E5" />
    </marker>
    <marker id="arrowEmerald" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#10B981" />
    </marker>
    <marker id="arrowSlate" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#64748B" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="820" height="440" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Layer 1: Client Layer -->
  <rect x="20" y="20" width="180" height="400" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" stroke-dasharray="3,3" />
  <text x="30" y="42" font-family="'Inter', sans-serif" font-size="10" font-weight="800" fill="#475569" letter-spacing="0.05em">1. CLIENT LAYER</text>

  <!-- Client Box 1 -->
  <g transform="translate(35, 60)" filter="url(#cardShadow)">
    <rect width="150" height="85" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="12" y="22" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">React 18 SPA</text>
    <text x="12" y="38" font-family="'Inter', sans-serif" font-size="8.5" fill="#64748B">Vite Bundler · Vanilla CSS</text>
    <line x1="12" y1="46" x2="138" y2="46" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="60" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">• ChatPage.jsx</text>
    <text x="12" y="74" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">• DocumentsPage.jsx</text>
  </g>

  <!-- Client Box 2 -->
  <g transform="translate(35, 160)" filter="url(#cardShadow)">
    <rect width="150" height="75" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">State & Context</text>
    <text x="12" y="34" font-family="'Inter', sans-serif" font-size="8" fill="#64748B">ConversationContext</text>
    <rect x="12" y="44" width="126" height="20" rx="4" fill="#EEF2FF" />
    <text x="18" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#4F46E5">localStorage :v1</text>
  </g>

  <!-- Client Box 3: HTTP Client -->
  <g transform="translate(35, 250)" filter="url(#cardShadow)">
    <rect width="150" height="60" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">API Client Layer</text>
    <text x="12" y="36" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">services/api.js</text>
    <text x="12" y="50" font-family="'Inter', sans-serif" font-size="7.5" fill="#94A3B8">Fetch API · Timeout Abort</text>
  </g>

  <!-- Arrow: Client -> Gateway -->
  <path d="M 185 100 L 225 100" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowIndigo)" />
  <text x="190" y="92" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#4F46E5">JSON</text>

  <!-- Layer 2: API Gateway & FastAPI -->
  <rect x="230" y="20" width="180" height="400" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" stroke-dasharray="3,3" />
  <text x="240" y="42" font-family="'Inter', sans-serif" font-size="10" font-weight="800" fill="#475569" letter-spacing="0.05em">2. FASTAPI BACKEND</text>

  <!-- FastAPI Router Box -->
  <g transform="translate(245, 60)" filter="url(#cardShadow)">
    <rect width="150" height="110" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="12" y="22" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">API Router Layer</text>
    <text x="12" y="36" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">Uvicorn ASGI (:8000)</text>
    <line x1="12" y1="44" x2="138" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">POST /api/v1/chat</text>
    <text x="12" y="72" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">POST /upload</text>
    <text x="12" y="86" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">GET|PUT|DEL /docs</text>
    <text x="12" y="100" font-family="'JetBrains Mono', monospace" font-size="8" fill="#10B981">GET /health</text>
  </g>

  <!-- DI Container -->
  <g transform="translate(245, 185)" filter="url(#cardShadow)">
    <rect width="150" height="85" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">Dependency Injection</text>
    <text x="12" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">api/dependencies.py</text>
    <line x1="12" y1="42" x2="138" y2="42" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="56" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• @lru_cache singletons</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Clean Test Overrides</text>
  </g>

  <!-- Config & Logging -->
  <g transform="translate(245, 285)" filter="url(#cardShadow)">
    <rect width="150" height="80" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">Core Config & Logs</text>
    <text x="12" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">config.yaml + .env</text>
    <rect x="12" y="44" width="126" height="24" rx="4" fill="#FEF2F2" />
    <text x="18" y="58" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#991B1B">SensitiveDataFilter</text>
    <text x="18" y="66" font-family="'Inter', sans-serif" font-size="6.5" fill="#991B1B">API Key Redaction</text>
  </g>

  <!-- Arrow: Gateway -> Orchestration -->
  <path d="M 395 110 L 435 110" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowIndigo)" />

  <!-- Layer 3: Orchestration & Domain -->
  <rect x="440" y="20" width="170" height="400" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" stroke-dasharray="3,3" />
  <text x="450" y="42" font-family="'Inter', sans-serif" font-size="10" font-weight="800" fill="#475569" letter-spacing="0.05em">3. ORCHESTRATION</text>

  <!-- RAG Pipeline -->
  <g transform="translate(450, 60)" filter="url(#cardShadow)">
    <rect width="150" height="95" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="12" y="22" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#4F46E5">RAGPipeline</text>
    <text x="12" y="36" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">rag/pipeline.py</text>
    <line x1="12" y1="44" x2="138" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Query normalization</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Cache lookup & set</text>
    <text x="12" y="82" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Prompt grounding</text>
  </g>

  <!-- Document Service -->
  <g transform="translate(450, 170)" filter="url(#cardShadow)">
    <rect width="150" height="95" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">DocumentService</text>
    <text x="12" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">ingestion/pipeline.py</text>
    <line x1="12" y1="42" x2="138" y2="42" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="56" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Safe file staging</text>
    <text x="12" y="68" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• 800/100 Chunking</text>
    <text x="12" y="80" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Atomic replacement</text>
  </g>

  <!-- Retriever Component -->
  <g transform="translate(450, 280)" filter="url(#cardShadow)">
    <rect width="150" height="75" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">Retriever</text>
    <text x="12" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">retrieval/retriever.py</text>
    <rect x="12" y="44" width="126" height="20" rx="4" fill="#F5F3FF" />
    <text x="18" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#7C3AED">Top-K=4 Similarity</text>
  </g>

  <!-- Arrow: Orchestration -> Infrastructure -->
  <path d="M 600 110 L 640 110" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowIndigo)" />
  <path d="M 600 220 L 640 220" fill="none" stroke="#64748B" stroke-width="1.5" marker-end="url(#arrowSlate)" />

  <!-- Layer 4: Storage, Cache & External AI -->
  <rect x="645" y="20" width="155" height="400" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" stroke-dasharray="3,3" />
  <text x="655" y="42" font-family="'Inter', sans-serif" font-size="10" font-weight="800" fill="#475569" letter-spacing="0.05em">4. STORAGE & AI</text>

  <!-- Redis Cache Box -->
  <g transform="translate(655, 60)" filter="url(#cardShadow)">
    <rect width="135" height="75" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#065F46">Redis Query Cache</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">Port :6379 (Docker)</text>
    <rect x="10" y="44" width="115" height="20" rx="4" fill="#ECFDF5" />
    <text x="14" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#065F46">TTL 3600s · FailOpen</text>
  </g>

  <!-- ChromaDB Box -->
  <g transform="translate(655, 150)" filter="url(#cardShadow)">
    <rect width="135" height="85" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#4F46E5">ChromaDB Store</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">PersistentClient</text>
    <text x="10" y="50" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• SQLite metadata</text>
    <text x="10" y="62" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• HNSW dense index</text>
    <text x="10" y="74" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Euclidean distance</text>
  </g>

  <!-- External AI: Gemini Embeddings -->
  <g transform="translate(655, 250)" filter="url(#cardShadow)">
    <rect width="135" height="75" rx="6" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#7C3AED">Google GenAI</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">gemini-embedding-2</text>
    <rect x="10" y="44" width="115" height="20" rx="4" fill="#F5F3FF" />
    <text x="14" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#7C3AED">768 Dim · Batch 100</text>
  </g>

  <!-- External AI: OpenRouter LLM -->
  <g transform="translate(655, 340)" filter="url(#cardShadow)">
    <rect width="135" height="70" rx="6" fill="#FFFFFF" stroke="#F59E0B" stroke-width="1.5" />
    <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#92400E">OpenRouter API</text>
    <text x="10" y="32" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">gemini-2.5-flash</text>
    <rect x="10" y="40" width="115" height="18" rx="4" fill="#FFFBEB" />
    <text x="14" y="53" font-family="'JetBrains Mono', monospace" font-size="7" font-weight="600" fill="#92400E">Temp 0.2 · Max 4096</text>
  </g>
</svg>"""

SVG_DIAGRAM_B = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 360" width="100%" height="360">
  <defs>
    <filter id="boxShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#4F46E5" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="800" height="360" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Top Flow Row 1 (Steps 1 to 4) -->
  <!-- Step 1: Upload -->
  <g transform="translate(30, 30)" filter="url(#boxShadow)">
    <rect width="160" height="110" rx="8" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#EEF2FF" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#4F46E5" text-anchor="middle">1</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Upload Action</text>
    <line x1="12" y1="44" x2="148" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="60" font-family="'Inter', sans-serif" font-size="8.5" fill="#475569">POST /api/v1/upload</text>
    <text x="12" y="74" font-family="'Inter', sans-serif" font-size="8" fill="#64748B">PDF, TXT, or Markdown</text>
    <rect x="12" y="82" width="136" height="18" rx="4" fill="#EEF2FF" />
    <text x="18" y="94" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#4F46E5">Limit: 10 MB Max</text>
  </g>

  <!-- Arrow 1 -> 2 -->
  <path d="M 190 85 L 220 85" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Step 2: Validation & Staging -->
  <g transform="translate(225, 30)" filter="url(#boxShadow)">
    <rect width="160" height="110" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#F1F5F9" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#475569" text-anchor="middle">2</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Validate &amp; Stage</text>
    <line x1="12" y1="44" x2="148" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="60" font-family="'Inter', sans-serif" font-size="8.5" fill="#475569">Extension Whitelist</text>
    <text x="12" y="74" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">./data/uploads/{uuid}</text>
    <rect x="12" y="82" width="136" height="18" rx="4" fill="#FEF2F2" />
    <text x="18" y="94" font-family="'Inter', sans-serif" font-size="7" font-weight="700" fill="#991B1B">Unlinked on Failure</text>
  </g>

  <!-- Arrow 2 -> 3 -->
  <path d="M 385 85 L 415 85" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Step 3: Document Loader -->
  <g transform="translate(420, 30)" filter="url(#boxShadow)">
    <rect width="160" height="110" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#F1F5F9" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#475569" text-anchor="middle">3</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Format Loader</text>
    <line x1="12" y1="44" x2="148" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• PDF: PyPDFLoader</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• TXT/MD: TextLoader</text>
    <rect x="12" y="82" width="136" height="18" rx="4" fill="#F5F3FF" />
    <text x="18" y="94" font-family="'Inter', sans-serif" font-size="7.5" font-weight="600" fill="#7C3AED">Page metadata tagged</text>
  </g>

  <!-- Arrow 3 -> 4 -->
  <path d="M 580 85 L 610 85" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Step 4: Text Cleaning -->
  <g transform="translate(615, 30)" filter="url(#boxShadow)">
    <rect width="155" height="110" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#F1F5F9" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#475569" text-anchor="middle">4</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Text Sanitization</text>
    <line x1="12" y1="44" x2="143" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• Strip leading/trailing</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• Collapse whitespace</text>
    <rect x="12" y="82" width="131" height="18" rx="4" fill="#FFFBEB" />
    <text x="16" y="94" font-family="'Inter', sans-serif" font-size="7" font-weight="700" fill="#92400E">Reject empty text</text>
  </g>

  <!-- Arrow 4 Down to 5 -->
  <path d="M 692 140 L 692 185 L 692 205" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Bottom Flow Row 2 (Steps 5 to 8) -->
  <!-- Step 5: Recursive Chunking -->
  <g transform="translate(615, 215)" filter="url(#boxShadow)">
    <rect width="155" height="115" rx="8" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#EEF2FF" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#4F46E5" text-anchor="middle">5</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Chunking Splitter</text>
    <line x1="12" y1="44" x2="143" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">chunk_size = 800</text>
    <text x="12" y="72" font-family="'JetBrains Mono', monospace" font-size="8" fill="#4F46E5">chunk_overlap = 100</text>
    <rect x="12" y="82" width="131" height="24" rx="4" fill="#EEF2FF" />
    <text x="16" y="94" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#4F46E5">Separators: ["\\n\\n",</text>
    <text x="16" y="103" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#4F46E5">"\\n", " ", ""]</text>
  </g>

  <!-- Arrow 5 <- 6 -->
  <path d="M 615 272 L 585 272" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Step 6: Metadata Injection -->
  <g transform="translate(420, 215)" filter="url(#boxShadow)">
    <rect width="160" height="115" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#F1F5F9" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#475569" text-anchor="middle">6</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Metadata Inject</text>
    <line x1="12" y1="44" x2="148" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#475569">• source: filename</text>
    <text x="12" y="70" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#475569">• page: int (1-based)</text>
    <text x="12" y="82" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#475569">• chunk_index: int</text>
    <text x="12" y="94" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#475569">• indexed_at: ISO8601</text>
  </g>

  <!-- Arrow 6 <- 7 -->
  <path d="M 420 272 L 390 272" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Step 7: Batch Embedding -->
  <g transform="translate(225, 215)" filter="url(#boxShadow)">
    <rect width="160" height="115" rx="8" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#F5F3FF" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#7C3AED" text-anchor="middle">7</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#7C3AED">Gemini Embed</text>
    <line x1="12" y1="44" x2="148" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">gemini-embedding-2</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="8" fill="#475569">Batch Size: 100 chunks</text>
    <rect x="12" y="82" width="136" height="22" rx="4" fill="#F5F3FF" />
    <text x="16" y="96" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#7C3AED">768 Dim Dense Vector</text>
  </g>

  <!-- Arrow 7 <- 8 -->
  <path d="M 225 272 L 195 272" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow)" />

  <!-- Step 8: ChromaDB Store & Cache Invalidate -->
  <g transform="translate(30, 215)" filter="url(#boxShadow)">
    <rect width="160" height="115" rx="8" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <circle cx="24" cy="24" r="12" fill="#ECFDF5" />
    <text x="24" y="28" font-family="'JetBrains Mono', monospace" font-size="10" font-weight="800" fill="#065F46" text-anchor="middle">8</text>
    <text x="44" y="28" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#065F46">Index &amp; Purge</text>
    <line x1="12" y1="44" x2="148" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• ChromaStore.upsert()</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• redis_cache.clear()</text>
    <rect x="12" y="82" width="136" height="22" rx="4" fill="#ECFDF5" />
    <text x="16" y="96" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#065F46">Knowledge Active</text>
  </g>
</svg>"""

SVG_DIAGRAM_C = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 380" width="100%" height="380">
  <defs>
    <filter id="qShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <marker id="arrowC" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#4F46E5" />
    </marker>
    <marker id="arrowGreen" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#10B981" />
    </marker>
  </defs>

  <rect width="800" height="380" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Query Start Box -->
  <g transform="translate(30, 140)" filter="url(#qShadow)">
    <rect width="130" height="80" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="12" y="24" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">User Question</text>
    <text x="12" y="40" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">POST /api/v1/chat</text>
    <rect x="10" y="48" width="110" height="22" rx="4" fill="#EEF2FF" />
    <text x="16" y="62" font-family="'Inter', sans-serif" font-size="7.5" font-weight="600" fill="#4F46E5">Normalized Input</text>
  </g>

  <!-- Arrow to Redis Check -->
  <path d="M 160 180 L 195 180" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowC)" />

  <!-- Decision Diamond: Redis Cache -->
  <g transform="translate(200, 140)" filter="url(#qShadow)">
    <polygon points="55,0 110,40 55,80 0,40" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <text x="55" y="38" font-family="'Inter', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">Cache</text>
    <text x="55" y="50" font-family="'Inter', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">HIT?</text>
  </g>

  <!-- Branch 1: Cache HIT (Upwards) -->
  <path d="M 255 140 L 255 70 L 640 70" fill="none" stroke="#10B981" stroke-width="2" stroke-dasharray="4,4" marker-end="url(#arrowGreen)" />
  <text x="270" y="62" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#10B981">YES: CACHE HIT (&lt; 10ms)</text>

  <!-- Branch 2: Cache MISS (Rightwards) -->
  <path d="M 310 180 L 340 180" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowC)" />
  <text x="315" y="172" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#EF4444">NO</text>

  <!-- Vector Retrieval Steps -->
  <!-- Step 1: Query Embed -->
  <g transform="translate(345, 140)" filter="url(#qShadow)">
    <rect width="125" height="80" rx="6" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#7C3AED">1. Embed Query</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">Gemini Embed 2</text>
    <rect x="8" y="44" width="109" height="24" rx="4" fill="#F5F3FF" />
    <text x="12" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#7C3AED">768d Vector</text>
  </g>

  <!-- Arrow -->
  <path d="M 470 180 L 495 180" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowC)" />

  <!-- Step 2: ChromaDB Similarity -->
  <g transform="translate(500, 140)" filter="url(#qShadow)">
    <rect width="130" height="80" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#4F46E5">2. Vector Search</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">ChromaStore (L2)</text>
    <rect x="8" y="44" width="114" height="24" rx="4" fill="#EEF2FF" />
    <text x="12" y="58" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#4F46E5">Top-K = 4 Chunks</text>
  </g>

  <!-- Arrow Down to Generation -->
  <path d="M 565 220 L 565 260" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowC)" />

  <!-- Bottom Row: Prompt & LLM -->
  <!-- Step 3: Prompt Grounding -->
  <g transform="translate(480, 265)" filter="url(#qShadow)">
    <rect width="170" height="85" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#0F172A">3. Prompt Grounding</text>
    <text x="10" y="34" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Injects 4 context chunks</text>
    <text x="10" y="48" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• "Answer ONLY from context"</text>
    <text x="10" y="62" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• "Say 'I don't know' if absent"</text>
    <text x="10" y="74" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">templates.py</text>
  </g>

  <!-- Arrow to LLM -->
  <path d="M 480 307 L 440 307" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowC)" />

  <!-- Step 4: OpenRouter LLM -->
  <g transform="translate(270, 265)" filter="url(#qShadow)">
    <rect width="165" height="85" rx="6" fill="#FFFFFF" stroke="#F59E0B" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#92400E">4. LLM Generation</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">OpenRouter Gateway</text>
    <text x="10" y="48" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">google/gemini-2.5-flash</text>
    <rect x="8" y="56" width="149" height="20" rx="4" fill="#FFFBEB" />
    <text x="12" y="70" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#92400E">Temp 0.2 · Max 4096</text>
  </g>

  <!-- Arrow to Cache SET -->
  <path d="M 270 307 L 220 307" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowC)" />

  <!-- Step 5: Cache SET -->
  <g transform="translate(80, 265)" filter="url(#qShadow)">
    <rect width="135" height="85" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#065F46">5. Cache SET</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">Redis SET with TTL</text>
    <text x="10" y="48" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">TTL = 3600 seconds</text>
    <rect x="8" y="56" width="119" height="20" rx="4" fill="#ECFDF5" />
    <text x="12" y="70" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#065F46">JSON Serialized</text>
  </g>

  <!-- Final RAG Response Box (Top Right) -->
  <g transform="translate(645, 45)" filter="url(#qShadow)">
    <rect width="130" height="75" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="2" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="800" fill="#4F46E5">RAGResponse</text>
    <text x="10" y="36" font-family="'Inter', sans-serif" font-size="8" fill="#0F172A">• Grounded Answer</text>
    <text x="10" y="48" font-family="'Inter', sans-serif" font-size="8" fill="#0F172A">• Deduplicated Sources</text>
    <text x="10" y="60" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#10B981">• Page Citations</text>
  </g>

  <!-- Connect Cache SET to Response -->
  <path d="M 147 265 L 147 240 L 710 240 L 710 125" fill="none" stroke="#4F46E5" stroke-width="1.5" stroke-dasharray="3,3" marker-end="url(#arrowC)" />
</svg>"""

SVG_DIAGRAM_D = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 320" width="100%" height="320">
  <defs>
    <filter id="dShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <marker id="arrowD" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#4F46E5" />
    </marker>
    <marker id="arrowGreenD" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#10B981" />
    </marker>
    <marker id="arrowRedD" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#EF4444" />
    </marker>
  </defs>

  <rect width="720" height="320" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Input Query -->
  <g transform="translate(25, 120)" filter="url(#dShadow)">
    <rect width="130" height="75" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="12" y="22" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">Raw User Query</text>
    <text x="12" y="38" font-family="'Inter', sans-serif" font-size="8" fill="#64748B">"What is remote work?"</text>
    <line x1="12" y1="46" x2="118" y2="46" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="60" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">strip().lower()</text>
  </g>

  <!-- Arrow to Hash Key -->
  <path d="M 155 157 L 185 157" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowD)" />

  <!-- Hash Key Box -->
  <g transform="translate(190, 115)" filter="url(#dShadow)">
    <rect width="145" height="85" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#0F172A">Key Generator</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7" fill="#4F46E5">nexusrag:cache:v1:</text>
    <text x="10" y="46" font-family="'JetBrains Mono', monospace" font-size="7" fill="#64748B">sha256(norm_query)</text>
    <rect x="8" y="54" width="129" height="22" rx="4" fill="#EEF2FF" />
    <text x="12" y="68" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#4F46E5">Deterministic Hash</text>
  </g>

  <!-- Arrow to Diamond -->
  <path d="M 335 157 L 365 157" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowD)" />

  <!-- Decision Diamond -->
  <g transform="translate(370, 117)" filter="url(#dShadow)">
    <polygon points="55,0 110,40 55,80 0,40" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <text x="55" y="36" font-family="'Inter', sans-serif" font-size="9" font-weight="800" fill="#065F46" text-anchor="middle">Redis Key</text>
    <text x="55" y="48" font-family="'Inter', sans-serif" font-size="9" font-weight="800" fill="#065F46" text-anchor="middle">Exists?</text>
  </g>

  <!-- Top Path: HIT -->
  <path d="M 425 117 L 425 65 L 500 65" fill="none" stroke="#10B981" stroke-width="2" marker-end="url(#arrowGreenD)" />
  <text x="435" y="55" font-family="'JetBrains Mono', monospace" font-size="8.5" font-weight="700" fill="#10B981">YES: CACHE HIT</text>

  <!-- Cache HIT Box -->
  <g transform="translate(505, 25)" filter="url(#dShadow)">
    <rect width="190" height="85" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#065F46">Instant Return (&lt; 10ms)</text>
    <text x="12" y="36" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Deserialize JSON string</text>
    <text x="12" y="50" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. Reconstruct RAGResponse</text>
    <rect x="12" y="58" width="166" height="18" rx="4" fill="#ECFDF5" />
    <text x="18" y="70" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#065F46">Bypasses ChromaDB &amp; LLM</text>
  </g>

  <!-- Bottom Path: MISS -->
  <path d="M 425 197 L 425 245 L 500 245" fill="none" stroke="#EF4444" stroke-width="2" marker-end="url(#arrowRedD)" />
  <text x="435" y="235" font-family="'JetBrains Mono', monospace" font-size="8.5" font-weight="700" fill="#EF4444">NO: CACHE MISS</text>

  <!-- Cache MISS Box -->
  <g transform="translate(505, 205)" filter="url(#dShadow)">
    <rect width="190" height="95" rx="6" fill="#FFFFFF" stroke="#EF4444" stroke-width="1.5" />
    <text x="12" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#991B1B">Full Pipeline (~1.8s)</text>
    <text x="12" y="34" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Query Embedding</text>
    <text x="12" y="46" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. ChromaDB Top-4 Retrieval</text>
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#475569">3. Gemini 2.5 Flash Generation</text>
    <rect x="12" y="66" width="166" height="20" rx="4" fill="#FEF2F2" />
    <text x="18" y="80" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#991B1B">Redis SET (TTL 3600s)</text>
  </g>

  <!-- Fail Open Note (Bottom Left) -->
  <g transform="translate(25, 230)">
    <rect width="310" height="65" rx="6" fill="#FFFBEB" stroke="#FDE68A" stroke-width="1" />
    <text x="10" y="18" font-family="'Inter', sans-serif" font-size="8.5" font-weight="700" fill="#92400E">FAIL-OPEN RESILIENCE GUARANTEE</text>
    <text x="10" y="32" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">If Redis crashes or timeouts, exception is caught.</text>
    <text x="10" y="44" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Pipeline logs warning and automatically executes</text>
    <text x="10" y="56" font-family="'Inter', sans-serif" font-size="7.5" font-weight="600" fill="#92400E">full RAG flow without user downtime.</text>
  </g>
</svg>"""

SVG_DIAGRAM_E = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 380" width="100%" height="380">
  <defs>
    <filter id="eShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <marker id="arrowE" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#4F46E5" />
    </marker>
  </defs>

  <rect width="800" height="380" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- App Entrypoint -->
  <g transform="translate(30, 150)" filter="url(#eShadow)">
    <rect width="110" height="70" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="2" />
    <text x="10" y="24" font-family="'Inter', sans-serif" font-size="11" font-weight="800" fill="#4F46E5">FastAPI App</text>
    <text x="10" y="42" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">main.py</text>
    <text x="10" y="56" font-family="'Inter', sans-serif" font-size="7.5" fill="#94A3B8">Lifespan context</text>
  </g>

  <!-- Arrow to Dependencies -->
  <path d="M 140 185 L 175 185" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowE)" />

  <!-- Dependencies Container -->
  <g transform="translate(180, 40)" filter="url(#eShadow)">
    <rect width="170" height="300" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" stroke-dasharray="3,3" />
    <text x="14" y="26" font-family="'Inter', sans-serif" font-size="10" font-weight="800" fill="#0F172A">dependencies.py</text>
    <text x="14" y="40" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">Singleton Provider (@lru_cache)</text>
    <line x1="10" y1="48" x2="160" y2="48" stroke="#E2E8F0" stroke-width="1" />

    <rect x="10" y="55" width="150" height="26" rx="4" fill="#FFFFFF" stroke="#E2E8F0" />
    <text x="16" y="72" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">get_settings()</text>

    <rect x="10" y="88" width="150" height="26" rx="4" fill="#FFFFFF" stroke="#E2E8F0" />
    <text x="16" y="105" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">get_redis_cache()</text>

    <rect x="10" y="121" width="150" height="26" rx="4" fill="#FFFFFF" stroke="#E2E8F0" />
    <text x="16" y="138" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">get_embedding_service()</text>

    <rect x="10" y="154" width="150" height="26" rx="4" fill="#FFFFFF" stroke="#E2E8F0" />
    <text x="16" y="171" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">get_chroma_store()</text>

    <rect x="10" y="187" width="150" height="26" rx="4" fill="#FFFFFF" stroke="#E2E8F0" />
    <text x="16" y="204" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">get_retriever()</text>

    <rect x="10" y="220" width="150" height="26" rx="4" fill="#FFFFFF" stroke="#E2E8F0" />
    <text x="16" y="237" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#4F46E5">get_llm_service()</text>

    <rect x="10" y="253" width="150" height="32" rx="4" fill="#EEF2FF" stroke="#4F46E5" />
    <text x="16" y="268" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#4F46E5">get_rag_pipeline()</text>
    <text x="16" y="279" font-family="'JetBrains Mono', monospace" font-size="7" fill="#4F46E5">get_document_service()</text>
  </g>

  <!-- Arrow to Domain Layer -->
  <path d="M 350 185 L 385 185" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowE)" />

  <!-- Domain Services Layer -->
  <g transform="translate(390, 50)" filter="url(#eShadow)">
    <rect width="180" height="120" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="12" y="22" font-family="'Inter', sans-serif" font-size="10.5" font-weight="800" fill="#4F46E5">RAGPipeline</text>
    <text x="12" y="36" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">rag/pipeline.py</text>
    <line x1="12" y1="44" x2="168" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• query(text)</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Injects Retriever</text>
    <text x="12" y="82" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Injects LLMService</text>
    <text x="12" y="94" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Injects RedisQueryCache</text>
    <text x="12" y="106" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Deduplicates Citations</text>
  </g>

  <g transform="translate(390, 195)" filter="url(#eShadow)">
    <rect width="180" height="125" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <text x="12" y="22" font-family="'Inter', sans-serif" font-size="10.5" font-weight="800" fill="#0F172A">DocumentService</text>
    <text x="12" y="36" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">ingestion/pipeline.py</text>
    <line x1="12" y1="44" x2="168" y2="44" stroke="#F1F5F9" stroke-width="1" />
    <text x="12" y="58" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• ingest_file(path)</text>
    <text x="12" y="70" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• replace_document(target)</text>
    <text x="12" y="82" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• delete_document(source)</text>
    <text x="12" y="94" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• list_documents()</text>
    <text x="12" y="106" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">• Clears Redis on Mutation</text>
  </g>

  <!-- Arrow to Storage Abstractions -->
  <path d="M 570 110 L 605 110" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowE)" />
  <path d="M 570 255 L 605 255" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowE)" />

  <!-- Storage Abstractions Layer -->
  <g transform="translate(610, 40)" filter="url(#eShadow)">
    <rect width="165" height="70" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#065F46">RedisQueryCache</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">cache/redis_cache.py</text>
    <text x="10" y="48" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Wraps redis.Redis client</text>
    <text x="10" y="60" font-family="'Inter', sans-serif" font-size="7.5" fill="#065F46">Fail-open error handler</text>
  </g>

  <g transform="translate(610, 120)" filter="url(#eShadow)">
    <rect width="165" height="70" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#4F46E5">ChromaStore</text>
    <text x="10" y="34" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">vectordb/chroma_store.py</text>
    <text x="10" y="48" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">PersistentClient abstraction</text>
    <text x="10" y="60" font-family="'Inter', sans-serif" font-size="7.5" fill="#4F46E5">Collection isolation</text>
  </g>

  <g transform="translate(610, 200)" filter="url(#eShadow)">
    <rect width="165" height="65" rx="6" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" />
    <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#7C3AED">GeminiEmbedder</text>
    <text x="10" y="32" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">embeddings/embedder.py</text>
    <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Google GenAI SDK wrapper</text>
    <text x="10" y="58" font-family="'Inter', sans-serif" font-size="7.5" fill="#7C3AED">Batching &amp; dim override</text>
  </g>

  <g transform="translate(610, 275)" filter="url(#eShadow)">
    <rect width="165" height="65" rx="6" fill="#FFFFFF" stroke="#F59E0B" stroke-width="1.5" />
    <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#92400E">OpenRouterService</text>
    <text x="10" y="32" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">llm/openrouter.py</text>
    <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">LangChain ChatOpenAI base</text>
    <text x="10" y="58" font-family="'Inter', sans-serif" font-size="7.5" fill="#92400E">Retry on 429/5xx</text>
  </g>
</svg>"""

SVG_DIAGRAM_F = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 340" width="100%" height="340">
  <defs>
    <filter id="fShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
  </defs>

  <rect width="800" height="340" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Quadrant 1: CREATE (Upload) -->
  <g transform="translate(25, 20)" filter="url(#fShadow)">
    <rect width="360" height="135" rx="8" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <rect x="12" y="12" width="75" height="20" rx="4" fill="#EEF2FF" />
    <text x="49" y="26" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="800" fill="#4F46E5" text-anchor="middle">CREATE</text>
    <text x="95" y="26" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Upload Document</text>
    <text x="345" y="26" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B" text-anchor="end">POST /upload</text>
    <line x1="12" y1="38" x2="348" y2="38" stroke="#F1F5F9" stroke-width="1" />
    <text x="14" y="54" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Stage file to ./data/uploads/{uuid}_{filename}</text>
    <text x="14" y="68" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. Load &amp; Clean text (PyPDFLoader / TextLoader)</text>
    <text x="14" y="82" font-family="'Inter', sans-serif" font-size="8" fill="#475569">3. Split recursively into 800-char chunks (overlap 100)</text>
    <text x="14" y="96" font-family="'Inter', sans-serif" font-size="8" fill="#475569">4. Embed batch with Gemini Embedding 2 (768d)</text>
    <text x="14" y="110" font-family="'Inter', sans-serif" font-size="8" fill="#475569">5. Upsert to ChromaDB &amp; invalidate Redis query cache</text>
    <text x="14" y="124" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#065F46">✓ Staged file unlinked in finally block</text>
  </g>

  <!-- Quadrant 2: READ (List) -->
  <g transform="translate(415, 20)" filter="url(#fShadow)">
    <rect width="360" height="135" rx="8" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
    <rect x="12" y="12" width="60" height="20" rx="4" fill="#ECFDF5" />
    <text x="42" y="26" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="800" fill="#065F46" text-anchor="middle">READ</text>
    <text x="80" y="26" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">List Knowledge Base</text>
    <text x="345" y="26" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B" text-anchor="end">GET /documents</text>
    <line x1="12" y1="38" x2="348" y2="38" stroke="#F1F5F9" stroke-width="1" />
    <text x="14" y="54" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Query ChromaDB collection metadata</text>
    <text x="14" y="68" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. Extract unique source filenames (strip legacy UUIDs)</text>
    <text x="14" y="82" font-family="'Inter', sans-serif" font-size="8" fill="#475569">3. Count physical vectors per document (source of truth)</text>
    <text x="14" y="96" font-family="'Inter', sans-serif" font-size="8" fill="#475569">4. Extract earliest indexed_at ISO timestamp</text>
    <text x="14" y="110" font-family="'Inter', sans-serif" font-size="8" fill="#475569">5. Return DocumentSummary list with chunk counts</text>
    <text x="14" y="124" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#065F46">✓ Physical records prevent metadata drift</text>
  </g>

  <!-- Quadrant 3: UPDATE (Safe Replace) -->
  <g transform="translate(25, 175)" filter="url(#fShadow)">
    <rect width="360" height="145" rx="8" fill="#FFFFFF" stroke="#F59E0B" stroke-width="1.5" />
    <rect x="12" y="12" width="75" height="20" rx="4" fill="#FFFBEB" />
    <text x="49" y="26" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="800" fill="#92400E" text-anchor="middle">UPDATE</text>
    <text x="95" y="26" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Safe Replacement</text>
    <text x="345" y="26" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B" text-anchor="end">PUT /documents/{name}</text>
    <line x1="12" y1="38" x2="348" y2="38" stroke="#F1F5F9" stroke-width="1" />
    <text x="14" y="54" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Verify target document currently exists in ChromaDB</text>
    <text x="14" y="68" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. Stage new file to isolated temporary path</text>
    <text x="14" y="82" font-family="'Inter', sans-serif" font-size="8" fill="#475569">3. Ingest, chunk, and embed new file FIRST</text>
    <text x="14" y="96" font-family="'Inter', sans-serif" font-size="8" fill="#475569">4. On success: delete old document's vectors</text>
    <text x="14" y="110" font-family="'Inter', sans-serif" font-size="8" fill="#475569">5. Invalidate entire Redis query cache</text>
    <rect x="14" y="118" width="332" height="18" rx="3" fill="#FFFBEB" />
    <text x="18" y="130" font-family="'Inter', sans-serif" font-size="7" font-weight="700" fill="#92400E">CRITICAL: If embedding fails, old document is kept untouched</text>
  </g>

  <!-- Quadrant 4: DELETE (Purge) -->
  <g transform="translate(415, 175)" filter="url(#fShadow)">
    <rect width="360" height="145" rx="8" fill="#FFFFFF" stroke="#EF4444" stroke-width="1.5" />
    <rect x="12" y="12" width="75" height="20" rx="4" fill="#FEF2F2" />
    <text x="49" y="26" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="800" fill="#991B1B" text-anchor="middle">DELETE</text>
    <text x="95" y="26" font-family="'Inter', sans-serif" font-size="11" font-weight="700" fill="#0F172A">Purge Vectors</text>
    <text x="345" y="26" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B" text-anchor="end">DELETE /documents/{name}</text>
    <line x1="12" y1="38" x2="348" y2="38" stroke="#F1F5F9" stroke-width="1" />
    <text x="14" y="54" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Verify document exists; return 404 if absent</text>
    <text x="14" y="68" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. Query ChromaDB for all chunk IDs matching source</text>
    <text x="14" y="82" font-family="'Inter', sans-serif" font-size="8" fill="#475569">3. Execute collection.delete(ids=[...])</text>
    <text x="14" y="96" font-family="'Inter', sans-serif" font-size="8" fill="#475569">4. Clear Redis query cache to purge stale answers</text>
    <text x="14" y="110" font-family="'Inter', sans-serif" font-size="8" fill="#475569">5. Return 200 OK with deleted chunk count</text>
    <rect x="14" y="118" width="332" height="18" rx="3" fill="#FEF2F2" />
    <text x="18" y="130" font-family="'Inter', sans-serif" font-size="7" font-weight="700" fill="#991B1B">Stops RAG from citing deleted enterprise documents</text>
  </g>
</svg>"""

SVG_DIAGRAM_G = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 340" width="100%" height="340">
  <defs>
    <filter id="gShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <marker id="arrowG" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#4F46E5" />
    </marker>
    <marker id="arrowRedG" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#EF4444" />
    </marker>
    <marker id="arrowGreenG" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L6,3 z" fill="#10B981" />
    </marker>
  </defs>

  <rect width="760" height="340" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Step 1: Check Target -->
  <g transform="translate(25, 40)" filter="url(#gShadow)">
    <rect width="140" height="75" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">1. Verify Target</text>
    <text x="10" y="34" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Check old document</text>
    <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">exists in ChromaDB</text>
    <text x="10" y="60" font-family="'JetBrains Mono', monospace" font-size="7" fill="#EF4444">404 if absent</text>
  </g>

  <!-- Arrow -->
  <path d="M 165 77 L 195 77" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowG)" />

  <!-- Step 2: Stage New File -->
  <g transform="translate(200, 40)" filter="url(#gShadow)">
    <rect width="140" height="75" rx="6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">2. Stage New File</text>
    <text x="10" y="34" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Save to isolated path</text>
    <text x="10" y="46" font-family="'JetBrains Mono', monospace" font-size="7" fill="#64748B">{uuid}_{filename}</text>
    <text x="10" y="60" font-family="'Inter', sans-serif" font-size="7.5" fill="#10B981">Zero collision</text>
  </g>

  <!-- Arrow -->
  <path d="M 340 77 L 370 77" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowG)" />

  <!-- Step 3: Index New File -->
  <g transform="translate(375, 40)" filter="url(#gShadow)">
    <rect width="145" height="75" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
    <text x="10" y="20" font-family="'Inter', sans-serif" font-size="10" font-weight="700" fill="#0F172A">3. Ingest &amp; Embed</text>
    <text x="10" y="34" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Load, split, embed</text>
    <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">and upsert new vectors</text>
    <text x="10" y="60" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="600" fill="#4F46E5">Done BEFORE delete</text>
  </g>

  <!-- Arrow -->
  <path d="M 520 77 L 550 77" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrowG)" />

  <!-- Decision Diamond: Success? -->
  <g transform="translate(555, 37)" filter="url(#gShadow)">
    <polygon points="55,0 110,40 55,80 0,40" fill="#FFFFFF" stroke="#F59E0B" stroke-width="1.5" />
    <text x="55" y="36" font-family="'Inter', sans-serif" font-size="9" font-weight="800" fill="#92400E" text-anchor="middle">Ingestion</text>
    <text x="55" y="48" font-family="'Inter', sans-serif" font-size="9" font-weight="800" fill="#92400E" text-anchor="middle">Succeeded?</text>
  </g>

  <!-- NO Path: Failure / Rollback -->
  <path d="M 610 117 L 610 170" fill="none" stroke="#EF4444" stroke-width="2" marker-end="url(#arrowRedG)" />
  <text x="618" y="145" font-family="'JetBrains Mono', monospace" font-size="8.5" font-weight="800" fill="#EF4444">NO</text>

  <!-- Failure Box -->
  <g transform="translate(480, 180)" filter="url(#gShadow)">
    <rect width="250" height="125" rx="8" fill="#FEF2F2" stroke="#EF4444" stroke-width="1.5" />
    <text x="14" y="24" font-family="'Inter', sans-serif" font-size="10.5" font-weight="800" fill="#991B1B">FAILURE: OLD DOCUMENT PRESERVED</text>
    <text x="14" y="42" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• Embedding provider timed out or returned 429</text>
    <text x="14" y="56" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• Staged file unlinked in finally block</text>
    <text x="14" y="70" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• Old vectors in ChromaDB NEVER deleted</text>
    <text x="14" y="84" font-family="'Inter', sans-serif" font-size="8" fill="#475569">• Returns HTTP 500/502 to user</text>
    <rect x="12" y="94" width="226" height="20" rx="4" fill="#FFFFFF" stroke="#FECACA" />
    <text x="18" y="108" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#991B1B">ZERO DATA LOSS · ZERO DOWNTIME</text>
  </g>

  <!-- YES Path: Success (Leftwards down) -->
  <path d="M 665 77 L 700 77 L 700 140 L 320 140 L 320 170" fill="none" stroke="#10B981" stroke-width="2" marker-end="url(#arrowGreenG)" />
  <text x="705" y="110" font-family="'JetBrains Mono', monospace" font-size="8.5" font-weight="800" fill="#10B981">YES</text>

  <!-- Success Box -->
  <g transform="translate(60, 180)" filter="url(#gShadow)">
    <rect width="380" height="125" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5" />
    <text x="14" y="24" font-family="'Inter', sans-serif" font-size="10.5" font-weight="800" fill="#065F46">SUCCESS: PURGE OLD &amp; INVALIDATE CACHE</text>
    <text x="14" y="44" font-family="'Inter', sans-serif" font-size="8" fill="#475569">1. Delete all old vectors matching source filename from ChromaDB</text>
    <text x="14" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#475569">2. Invalidate entire Redis query cache (purge stale query answers)</text>
    <text x="14" y="72" font-family="'Inter', sans-serif" font-size="8" fill="#475569">3. Unlink staged file from disk</text>
    <text x="14" y="86" font-family="'Inter', sans-serif" font-size="8" fill="#475569">4. Return HTTP 200 with new chunk count and timestamp</text>
    <rect x="12" y="96" width="356" height="20" rx="4" fill="#FFFFFF" stroke="#A7F3D0" />
    <text x="18" y="110" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#065F46">ATOMIC-LIKE REPLACEMENT GUARANTEE IN CHROMADB</text>
  </g>
</svg>"""

SVG_DIAGRAM_H = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 360" width="100%" height="360">
  <defs>
    <filter id="hShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
  </defs>

  <rect width="800" height="360" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />

  <!-- Left Half: CURRENT DEVELOPMENT -->
  <g transform="translate(20, 20)">
    <rect width="365" height="320" rx="8" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" />
    <rect x="16" y="16" width="160" height="24" rx="4" fill="#EEF2FF" />
    <text x="24" y="32" font-family="'Inter', sans-serif" font-size="9" font-weight="800" fill="#4F46E5">CURRENT DEVELOPMENT</text>
    <text x="16" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#64748B">Single-Host Docker Compose / Local Dev</text>

    <!-- Dev Component Box -->
    <g transform="translate(16, 70)" filter="url(#hShadow)">
      <rect width="333" height="50" rx="6" fill="#FFFFFF" stroke="#CBD5E1" />
      <text x="12" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#0F172A">Frontend (Vite Dev Server)</text>
      <text x="12" y="36" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">localhost:5173 · React 18 · Client SPA</text>
    </g>

    <g transform="translate(16, 128)" filter="url(#hShadow)">
      <rect width="333" height="55" rx="6" fill="#FFFFFF" stroke="#4F46E5" />
      <text x="12" y="20" font-family="'Inter', sans-serif" font-size="9.5" font-weight="700" fill="#4F46E5">FastAPI Backend (Uvicorn)</text>
      <text x="12" y="34" font-family="'JetBrains Mono', monospace" font-size="8" fill="#64748B">localhost:8000 · Single Process · Async I/O</text>
      <text x="12" y="46" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">RAGPipeline + DocumentService domain layer</text>
    </g>

    <g transform="translate(16, 191)" filter="url(#hShadow)">
      <rect width="160" height="60" rx="6" fill="#FFFFFF" stroke="#10B981" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9" font-weight="700" fill="#065F46">Redis Container</text>
      <text x="10" y="32" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">Port :6379</text>
      <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7" fill="#475569">In-memory query cache</text>
    </g>

    <g transform="translate(186, 191)" filter="url(#hShadow)">
      <rect width="163" height="60" rx="6" fill="#FFFFFF" stroke="#4F46E5" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9" font-weight="700" fill="#4F46E5">ChromaDB Store</text>
      <text x="10" y="32" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">Local Disk SQLite</text>
      <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7" fill="#475569">./data/chroma_db HNSW</text>
    </g>

    <g transform="translate(16, 258)">
      <rect width="333" height="46" rx="6" fill="#FFFFFF" stroke="#E2E8F0" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="8" font-weight="700" fill="#64748B">EXTERNAL MODEL APIS</text>
      <text x="10" y="32" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#475569">Google GenAI (768d) · OpenRouter (Gemini 2.5)</text>
    </g>
  </g>

  <!-- Right Half: FUTURE PRODUCTION -->
  <g transform="translate(410, 20)">
    <rect width="370" height="320" rx="8" fill="#F8FAFC" stroke="#4F46E5" stroke-width="1.5" />
    <rect x="16" y="16" width="160" height="24" rx="4" fill="#4F46E5" />
    <text x="24" y="32" font-family="'Inter', sans-serif" font-size="9" font-weight="800" fill="#FFFFFF">FUTURE PRODUCTION</text>
    <text x="16" y="58" font-family="'Inter', sans-serif" font-size="8" fill="#64748B">Auto-Scaling Cloud Infrastructure (AWS)</text>

    <!-- CloudFront & CDN -->
    <g transform="translate(16, 70)" filter="url(#hShadow)">
      <rect width="338" height="42" rx="6" fill="#FFFFFF" stroke="#CBD5E1" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9" font-weight="700" fill="#0F172A">CloudFront CDN + S3 Static Hosting</text>
      <text x="10" y="32" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">Global Edge Caching · TLS 1.3 · Custom Domain</text>
    </g>

    <!-- ALB + Fargate Tasks -->
    <g transform="translate(16, 120)" filter="url(#hShadow)">
      <rect width="338" height="60" rx="6" fill="#FFFFFF" stroke="#4F46E5" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="9" font-weight="700" fill="#4F46E5">AWS ALB + ECS Fargate Auto-Scaling Tasks</text>
      <text x="10" y="32" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Multiple FastAPI worker pods (CPU/Memory scaling)</text>
      <text x="10" y="46" font-family="'JetBrains Mono', monospace" font-size="7.5" fill="#64748B">Asynchronous Ingestion Workers (Celery / SQS)</text>
    </g>

    <!-- Managed DBs -->
    <g transform="translate(16, 188)" filter="url(#hShadow)">
      <rect width="165" height="60" rx="6" fill="#FFFFFF" stroke="#10B981" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="8.5" font-weight="700" fill="#065F46">AWS ElastiCache</text>
      <text x="10" y="32" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">Multi-AZ Redis Cluster</text>
      <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7" fill="#475569">Auto-failover &amp; replicas</text>
    </g>

    <g transform="translate(189, 188)" filter="url(#hShadow)">
      <rect width="165" height="60" rx="6" fill="#FFFFFF" stroke="#7C3AED" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="8.5" font-weight="700" fill="#7C3AED">Dedicated Vector DB</text>
      <text x="10" y="32" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">Qdrant / Milvus Cluster</text>
      <text x="10" y="46" font-family="'Inter', sans-serif" font-size="7" fill="#475569">Horizontal sharding</text>
    </g>

    <!-- Observability & Storage -->
    <g transform="translate(16, 255)">
      <rect width="338" height="48" rx="6" fill="#FFFFFF" stroke="#E2E8F0" />
      <text x="10" y="18" font-family="'Inter', sans-serif" font-size="8" font-weight="700" fill="#64748B">S3 OBJECT STORAGE &amp; DATADOG OBSERVABILITY</text>
      <text x="10" y="32" font-family="'Inter', sans-serif" font-size="7.5" fill="#475569">Document vault · Structured JSON logs · Distributed tracing</text>
    </g>
  </g>
</svg>"""

SVG_DIAGRAM_I = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 350" width="100%" height="350">
  <defs>
    <filter id="iShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.08" />
    </filter>
    <marker id="arrowRedI" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#EF4444" />
    </marker>
    <marker id="arrowIndigoI" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#4F46E5" />
    </marker>
    <marker id="arrowGreenI" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#10B981" />
    </marker>
  </defs>

  <!-- Background Canvas -->
  <rect width="860" height="350" rx="10" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" />

  <!-- Title Header -->
  <g transform="translate(20, 15)">
    <rect x="0" y="0" width="150" height="18" rx="9" fill="#EEF2FF" stroke="#C7D2FE" />
    <text x="75" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#4F46E5">PARADIGM COMPARISON</text>
    <text x="162" y="13" font-family="'Inter', sans-serif" font-size="11.5" font-weight="800" fill="#0F172A">NAIVE FOUNDATION LLM vs. NEXUSRAG GROUNDED ARCHITECTURE</text>
    <text x="162" y="25" font-family="'Inter', sans-serif" font-size="8" fill="#64748B">Comparing direct parameter recall failure modes against deterministic vector retrieval with source attribution</text>
  </g>

  <!-- ========================================== -->
  <!-- LEFT PANEL: NAIVE FOUNDATION LLM           -->
  <!-- ========================================== -->
  <g transform="translate(20, 48)">
    <rect width="395" height="288" rx="8" fill="#FFFBEB" stroke="#FDE68A" stroke-width="1.5" />
    <rect x="14" y="12" width="175" height="20" rx="4" fill="#FEF3C7" stroke="#F59E0B" />
    <text x="22" y="25.5" font-family="'Inter', sans-serif" font-size="8.5" font-weight="800" fill="#92400E">NAIVE FOUNDATION LLM</text>
    <text x="380" y="25" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#DC2626">Unsafe Baseline</text>

    <!-- Flow: Question -> Standard LLM -> Unverified Answer -->
    <!-- Step 1: Question -->
    <g transform="translate(14, 42)" filter="url(#iShadow)">
      <rect width="105" height="46" rx="6" fill="#FFFFFF" stroke="#CBD5E1" />
      <text x="8" y="16" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#0F172A">User Question</text>
      <text x="8" y="28" font-family="'Inter', sans-serif" font-size="7" fill="#64748B">"What is our policy?"</text>
      <text x="8" y="39" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="600" fill="#94A3B8">Input String</text>
    </g>

    <!-- Arrow 1 -> 2 -->
    <path d="M 120 65 L 140 65" fill="none" stroke="#EF4444" stroke-width="1.5" marker-end="url(#arrowRedI)" />

    <!-- Step 2: Standard LLM -->
    <g transform="translate(143, 42)" filter="url(#iShadow)">
      <rect width="112" height="46" rx="6" fill="#FFFFFF" stroke="#EF4444" stroke-width="1.5" />
      <text x="8" y="16" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#991B1B">Standard LLM</text>
      <text x="8" y="28" font-family="'Inter', sans-serif" font-size="7" fill="#64748B">Pre-trained weights</text>
      <text x="8" y="39" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="600" fill="#DC2626">No External Context</text>
    </g>

    <!-- Arrow 2 -> 3 -->
    <path d="M 256 65 L 276 65" fill="none" stroke="#EF4444" stroke-width="1.5" marker-end="url(#arrowRedI)" />

    <!-- Step 3: Fabricated Output -->
    <g transform="translate(279, 42)" filter="url(#iShadow)">
      <rect width="102" height="46" rx="6" fill="#FEF2F2" stroke="#F87171" stroke-dasharray="3,2" />
      <text x="8" y="16" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#B91C1C">Unverified Text</text>
      <text x="8" y="28" font-family="'Inter', sans-serif" font-size="7" fill="#64748B">Plausible fabrication</text>
      <text x="8" y="39" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#DC2626">Zero Citations</text>
    </g>

    <!-- Down arrow to Risk Box -->
    <path d="M 199 88 L 199 100" fill="none" stroke="#EF4444" stroke-width="1.5" marker-end="url(#arrowRedI)" />

    <!-- Critical Risks Box -->
    <g transform="translate(14, 102)">
      <rect width="367" height="172" rx="6" fill="#FFFFFF" stroke="#FECACA" />
      <text x="12" y="18" font-family="'Inter', sans-serif" font-size="8" font-weight="800" fill="#991B1B">CRITICAL SYSTEM DEFECTS &amp; RISKS:</text>

      <g transform="translate(12, 28)">
        <text x="0" y="10" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#DC2626">✖ Hallucination: </tspan><tspan fill="#475569">Fabricates plausible but false facts with high confidence</tspan></text>
        <text x="0" y="26" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#DC2626">✖ Knowledge Cutoff: </tspan><tspan fill="#475569">Blind to internal updates, recent guidelines, &amp; new files</tspan></text>
        <text x="0" y="42" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#DC2626">✖ Private Data Blindness: </tspan><tspan fill="#475569">Zero access to enterprise PDFs, internal reports, or docs</tspan></text>
        <text x="0" y="58" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#DC2626">✖ Zero Attribution: </tspan><tspan fill="#475569">Provides no document name, page number, or audit trail</tspan></text>
        <text x="0" y="74" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#DC2626">✖ Silent Fallback Failure: </tspan><tspan fill="#475569">Guesses instead of refusing when context is absent</tspan></text>
        <text x="0" y="90" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#DC2626">✖ High API Cost: </tspan><tspan fill="#475569">Repeats identical full LLM calls with zero caching layer</tspan></text>
      </g>

      <!-- Verdict Banner -->
      <rect x="10" y="138" width="347" height="22" rx="4" fill="#FEE2E2" stroke="#FCA5A5" />
      <text x="183.5" y="152.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#991B1B">CRITICAL DEFECT: UNSAFE FOR ENTERPRISE DECISION MAKING</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- RIGHT PANEL: NEXUSRAG GROUNDED SYSTEM      -->
  <!-- ========================================== -->
  <g transform="translate(425, 48)">
    <rect width="415" height="288" rx="8" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1.5" />
    <rect x="14" y="12" width="190" height="20" rx="4" fill="#DCFCE7" stroke="#10B981" />
    <text x="22" y="25.5" font-family="'Inter', sans-serif" font-size="8.5" font-weight="800" fill="#166534">NEXUSRAG GROUNDED SYSTEM</text>
    <text x="400" y="25" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#059669">Verified Production</text>

    <!-- 4 Clear Step Boxes: Question -> Retrieval -> Grounding -> LLM + Citations -->
    <!-- Step 1: Query Input -->
    <g transform="translate(14, 42)" filter="url(#iShadow)">
      <rect width="82" height="46" rx="6" fill="#FFFFFF" stroke="#3B82F6" />
      <text x="6" y="15" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#1D4ED8">1. Query</text>
      <text x="6" y="27" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">ChatInput.jsx</text>
      <text x="6" y="38" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="600" fill="#2563EB">Redis Check</text>
    </g>

    <!-- Arrow 1 -> 2 -->
    <path d="M 97 65 L 109 65" fill="none" stroke="#4F46E5" stroke-width="1.5" marker-end="url(#arrowIndigoI)" />

    <!-- Step 2: Dense Retrieval -->
    <g transform="translate(111, 42)" filter="url(#iShadow)">
      <rect width="96" height="46" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" />
      <text x="6" y="15" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#4338CA">2. Retrieval</text>
      <text x="6" y="27" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">ChromaDB Top-4</text>
      <text x="6" y="38" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="600" fill="#4F46E5">768d Vector L2</text>
    </g>

    <!-- Arrow 2 -> 3 -->
    <path d="M 208 65 L 220 65" fill="none" stroke="#4F46E5" stroke-width="1.5" marker-end="url(#arrowIndigoI)" />

    <!-- Step 3: Context Guard & Prompt -->
    <g transform="translate(222, 42)" filter="url(#iShadow)">
      <rect width="88" height="46" rx="6" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" />
      <text x="6" y="15" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#6D28D9">3. Grounding</text>
      <text x="6" y="27" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">Strict QA Prompt</text>
      <text x="6" y="38" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="600" fill="#7C3AED">Context Guard</text>
    </g>

    <!-- Arrow 3 -> 4 -->
    <path d="M 311 65 L 323 65" fill="none" stroke="#10B981" stroke-width="1.5" marker-end="url(#arrowGreenI)" />

    <!-- Step 4: Grounded LLM + Citations -->
    <g transform="translate(325, 42)" filter="url(#iShadow)">
      <rect width="76" height="46" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" />
      <text x="6" y="15" font-family="'Inter', sans-serif" font-size="7.5" font-weight="700" fill="#047857">4. Response</text>
      <text x="6" y="27" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">Gemini 2.5 Flash</text>
      <text x="6" y="38" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="700" fill="#059669">+ Citations</text>
    </g>

    <!-- Down arrow to Advantages Box -->
    <path d="M 266 88 L 266 100" fill="none" stroke="#10B981" stroke-width="1.5" marker-end="url(#arrowGreenI)" />

    <!-- Engineering Advantages Box -->
    <g transform="translate(14, 102)">
      <rect width="387" height="172" rx="6" fill="#FFFFFF" stroke="#A7F3D0" />
      <text x="12" y="18" font-family="'Inter', sans-serif" font-size="8" font-weight="800" fill="#065F46">NEXUSRAG PRODUCTION ADVANTAGES:</text>

      <g transform="translate(12, 28)">
        <text x="0" y="10" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#059669">✔ Strict Grounded Context: </tspan><tspan fill="#475569">LLM reasons purely over retrieved Top-4 passages</tspan></text>
        <text x="0" y="26" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#059669">✔ Real-Time Freshness: </tspan><tspan fill="#475569">New PDFs indexed in seconds (800/100) without re-training</tspan></text>
        <text x="0" y="42" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#059669">✔ Full Source Attribution: </tspan><tspan fill="#475569">Exact (filename, page) citation pills clickable in UI</tspan></text>
        <text x="0" y="58" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#059669">✔ Refusal on Absent Info: </tspan><tspan fill="#475569">Context Guard returns deterministic fallback refusal</tspan></text>
        <text x="0" y="74" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#059669">✔ Sub-5ms Query Cache: </tspan><tspan fill="#475569">Redis short-circuits repeated queries (1-hour TTL)</tspan></text>
        <text x="0" y="90" font-family="'Inter', sans-serif" font-size="7.5"><tspan font-weight="700" fill="#059669">✔ Deterministic Testing: </tspan><tspan fill="#475569">236 automated tests verify pipeline &amp; schema contracts</tspan></text>
      </g>

      <!-- Verdict Banner -->
      <rect x="10" y="138" width="367" height="22" rx="4" fill="#DCFCE7" stroke="#86EFAC" />
      <text x="193.5" y="152.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#166534">VERDICT: ENTERPRISE-GRADE FACTUAL INTEGRITY &amp; AUDIT TRAIL</text>
    </g>
  </g>
</svg>"""

SVG_DIAGRAM_J = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 570" width="100%" height="570">
  <defs>
    <filter id="jShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#0F172A" flood-opacity="0.08" />
    </filter>
    <marker id="arrow-gray" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#94A3B8" />
    </marker>
    <marker id="arrow-indigo" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#4F46E5" />
    </marker>
    <marker id="arrow-purple" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#7C3AED" />
    </marker>
    <marker id="arrow-green" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#10B981" />
    </marker>
    <marker id="arrow-red" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#E11D48" />
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect width="940" height="570" rx="12" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" />

  <!-- Diagram Header -->
  <g transform="translate(25, 20)">
    <rect x="0" y="0" width="105" height="20" rx="10" fill="#EEF2FF" stroke="#C7D2FE" />
    <text x="52.5" y="13.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="800" fill="#4F46E5">SYSTEM TRACE</text>
    <text x="118" y="14" font-family="'Inter', sans-serif" font-size="12" font-weight="800" fill="#0F172A">END-TO-END TECHNICAL REQUEST LIFECYCLE (15 DISCRETE OPERATIONS)</text>
    <text x="118" y="28" font-family="'Inter', sans-serif" font-size="8.5" fill="#64748B">Synchronous HTTP flow: React Dispatch → FastAPI Gateway → Redis Cache Fork → ChromaDB Vector Retrieval → Gemini 2.5 Flash → UI Render</text>
  </g>

  <!-- ========================================== -->
  <!-- PHASE 1: CLIENT INGRESS & CACHE INSPECTION -->
  <!-- ========================================== -->
  <g transform="translate(20, 58)">
    <rect width="900" height="120" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1" />
    <circle cx="16" cy="16" r="4" fill="#3B82F6" />
    <text x="26" y="19" font-family="'Inter', sans-serif" font-size="8.5" font-weight="800" fill="#1E293B">PHASE 1: CLIENT DISPATCH, GATEWAY INGRESS &amp; CACHE INSPECTION</text>
    <rect x="740" y="8" width="150" height="16" rx="4" fill="#EFF6FF" stroke="#BFDBFE" />
    <text x="815" y="19" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#1D4ED8">Tier: Client + Gateway</text>

    <!-- Step 01: ChatInput.jsx -->
    <g transform="translate(15, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#3B82F6" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#2563EB" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">01</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">ChatInput.jsx</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Submits user question</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Validates length 1-2000</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Triggers useChat hook</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EFF6FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#1D4ED8">Client Dispatch · &lt; 1ms</text>
    </g>

    <!-- Arrow 01 -> 02 -->
    <line x1="172" y1="69" x2="191" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 02: useChat.js -->
    <g transform="translate(193, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#3B82F6" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#2563EB" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">02</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">useChat.js</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Sets isLoading = true</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Optimistic user bubble</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Clears error state</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EFF6FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#1D4ED8">State Transition · React</text>
    </g>

    <!-- Arrow 02 -> 03 -->
    <line x1="350" y1="69" x2="369" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 03: api.js -->
    <g transform="translate(371, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#3B82F6" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#2563EB" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">03</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">services/api.js</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• POST /api/v1/chat</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  AbortController (60s)</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Network error boundary</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EFF6FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#1D4ED8">HTTP Transport · 60s TO</text>
    </g>

    <!-- Arrow 03 -> 04 (Network Boundary) -->
    <line x1="528" y1="69" x2="547" y2="69" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow-indigo)" />
    <text x="538" y="63" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="800" fill="#4F46E5">NET</text>

    <!-- Step 04: routes_chat.py -->
    <g transform="translate(549, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#4F46E5" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">04</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">routes_chat.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Pydantic ChatRequest</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  FastAPI Depends(DI)</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Invokes RAGPipeline</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EEF2FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#4F46E5">FastAPI Router · Ingress</text>
    </g>

    <!-- Arrow 04 -> 05 -->
    <line x1="706" y1="69" x2="725" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 05: redis_cache.py (Cache Lookup) -->
    <g transform="translate(727, 30)">
      <rect width="158" height="78" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="2" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#059669" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">05</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#065F46">redis_cache.py</text>
      <line x1="6" y1="24" x2="152" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• SHA-256 query digest</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  GET nexusrag:query:v1:*</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Fail-open error policy</text>
      <rect x="6" y="62" width="146" height="11" rx="3" fill="#ECFDF5" />
      <text x="79" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="800" fill="#047857">CACHE FORK: HIT vs MISS</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- CONNECTORS: PHASE 1 -> PHASE 2 & CACHE HIT -->
  <!-- ========================================== -->
  <!-- CACHE MISS CONNECTOR (From 05 bottom to 06 top) -->
  <path d="M 806 168 L 806 193 L 112 193 L 112 233" fill="none" stroke="#7C3AED" stroke-width="2" marker-end="url(#arrow-purple)" />
  <g transform="translate(290, 184)">
    <rect width="320" height="18" rx="4" fill="#FAF5FF" stroke="#A855F7" stroke-width="1.2" filter="url(#jShadow)" />
    <text x="160" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#6B21A8">▼ CACHE MISS (~800-1800ms): Dense Semantic Retrieval Pipeline</text>
  </g>

  <!-- ========================================== -->
  <!-- PHASE 2: DENSE RETRIEVAL & LLM GENERATION  -->
  <!-- ========================================== -->
  <g transform="translate(20, 214)">
    <rect width="900" height="120" rx="8" fill="#FAF5FF" stroke="#E9D5FF" stroke-width="1" />
    <circle cx="16" cy="16" r="4" fill="#8B5CF6" />
    <text x="26" y="19" font-family="'Inter', sans-serif" font-size="8.5" font-weight="800" fill="#581C87">PHASE 2: DENSE RETRIEVAL, CONTEXT GUARD &amp; LLM INFERENCE (CACHE MISS)</text>
    <rect x="735" y="8" width="155" height="16" rx="4" fill="#F3E8FF" stroke="#D8B4FE" />
    <text x="812.5" y="19" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#6B21A8">Tier: ChromaDB + Gemini</text>

    <!-- Step 06: embedder.py -->
    <g transform="translate(15, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#7C3AED" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#7C3AED" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">06</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">embedder.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Gemini Embedding 2</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Task: RETRIEVAL_QUERY</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Produces 768d vector</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#F5F3FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#6D28D9">768-dim Vector · ~120ms</text>
    </g>

    <!-- Arrow 06 -> 07 -->
    <line x1="172" y1="69" x2="191" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 07: chroma_store.py -->
    <g transform="translate(193, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#4F46E5" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">07</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">chroma_store.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• HNSW Persistent Index</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Euclidean L2 distance</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Retrieves Top-K=4 chunks</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EEF2FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#4F46E5">Top-4 Chunks · &lt; 15ms</text>
    </g>

    <!-- Arrow 07 -> 08 -->
    <line x1="350" y1="69" x2="369" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 08: Context Guard -->
    <g transform="translate(371, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#E11D48" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#E11D48" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">08</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#9F1239">Context Guard</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Evaluates chunk count</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  If 0 chunks: Refusal</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Guards hallucination</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#FFF1F2" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#BE123C">Anti-Hallucination Gate</text>
    </g>

    <!-- Guardrail Refusal Indicator -->
    <path d="M 448 108 L 448 116 L 490 116" fill="none" stroke="#E11D48" stroke-width="1.2" stroke-dasharray="3,2" marker-end="url(#arrow-red)" />
    <text x="496" y="118.5" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="700" fill="#E11D48">0 chk: Refusal</text>

    <!-- Arrow 08 -> 09 -->
    <line x1="528" y1="69" x2="547" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />
    <text x="538" y="63" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="5.5" font-weight="700" fill="#059669">&gt;0 chk</text>

    <!-- Step 09: Prompt Builder -->
    <g transform="translate(549, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#6366F1" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#4F46E5" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">09</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">templates.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Injects 4 numbered chunks</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Strict grounding rules</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  No prior bias directive</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EEF2FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#4F46E5">Prompt Assembly · QA</text>
    </g>

    <!-- Arrow 09 -> 10 -->
    <line x1="706" y1="69" x2="725" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 10: openrouter.py -->
    <g transform="translate(727, 30)">
      <rect width="158" height="78" rx="6" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#D97706" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">10</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#92400E">openrouter.py</text>
      <line x1="6" y1="24" x2="152" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• google/gemini-2.5-flash</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  temp=0.2, max=4096</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Synthesizes completion</text>
      <rect x="6" y="62" width="146" height="11" rx="3" fill="#FFFBEB" />
      <text x="79" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#B45309">LLM Inference · ~1000ms</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- CONNECTORS: PHASE 2 -> PHASE 3 & CACHE HIT -->
  <!-- ========================================== -->
  <!-- LLM GENERATION COMPLETE CONNECTOR (From 10 bottom to 11 top) -->
  <path d="M 806 324 L 806 348 L 112 348 L 112 398" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow-indigo)" />
  <g transform="translate(130, 339)">
    <rect width="280" height="18" rx="4" fill="#EEF2FF" stroke="#6366F1" stroke-width="1.2" filter="url(#jShadow)" />
    <text x="140" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#3730A3">▼ LLM ANSWER GENERATED: Deduplicate &amp; Cache</text>
  </g>

  <!-- CACHE HIT FAST-TRACK BYPASS (From 05 right to 13 top) -->
  <path d="M 885 125 L 912 125 L 912 360 L 448 360 L 448 398" fill="none" stroke="#10B981" stroke-width="2.5" stroke-dasharray="5,3" marker-end="url(#arrow-green)" />
  <g transform="translate(520, 351)">
    <rect width="320" height="18" rx="4" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5" filter="url(#jShadow)" />
    <text x="160" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#065F46">⚡ CACHE HIT: &lt; 5ms (Skips Steps 06–12) ──► Joins at Step 13</text>
  </g>

  <!-- ========================================== -->
  <!-- PHASE 3: CITATION DEDUPLICATION & PERSIST  -->
  <!-- ========================================== -->
  <g transform="translate(20, 370)">
    <rect width="900" height="120" rx="8" fill="#F0FDF4" stroke="#DCFCE7" stroke-width="1" />
    <circle cx="16" cy="16" r="4" fill="#10B981" />
    <text x="26" y="19" font-family="'Inter', sans-serif" font-size="8.5" font-weight="800" fill="#14532D">PHASE 3: CITATION DEDUPLICATION, CACHE WRITE &amp; CLIENT RENDERING</text>
    <rect x="735" y="8" width="155" height="16" rx="4" fill="#DCFCE7" stroke="#86EFAC" />
    <text x="812.5" y="19" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#166534">Tier: Cache + Response + UI</text>

    <!-- Step 11: Extract Citations -->
    <g transform="translate(15, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#0D9488" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#0D9488" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">11</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">rag/pipeline.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Extract (source, page)</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Deduplicate in context order</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Preserve source accuracy</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#F0FDFA" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#0F766E">Citation Deduplication</text>
    </g>

    <!-- Arrow 11 -> 12 -->
    <line x1="172" y1="69" x2="191" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 12: redis_cache.py (Cache SET) -->
    <g transform="translate(193, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#059669" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">12</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#065F46">redis_cache.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• JSON serialize payload</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  SETEX key TTL 3600s</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Fail-open cache write</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#ECFDF5" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#047857">TTL: 3600s · 1 Hour</text>
    </g>

    <!-- Arrow 12 -> 13 -->
    <line x1="350" y1="69" x2="369" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 13: routes_chat.py (FastAPI Response Packaging) -->
    <g transform="translate(371, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#4F46E5" stroke-width="2" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#4F46E5" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">13</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">routes_chat.py</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Pydantic ChatResponse</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  answer, sources, latency</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" font-weight="700" fill="#059669">  ◄ Cache Hit joins here</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EEF2FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#4F46E5">HTTP 200 JSON Response</text>
    </g>

    <!-- Arrow 13 -> 14 (Network Boundary) -->
    <line x1="528" y1="69" x2="547" y2="69" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow-indigo)" />
    <text x="538" y="63" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6" font-weight="800" fill="#4F46E5">200</text>

    <!-- Step 14: ConversationContext.jsx -->
    <g transform="translate(549, 30)">
      <rect width="155" height="78" rx="6" fill="#FFFFFF" stroke="#3B82F6" stroke-width="1.5" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#2563EB" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">14</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#0F172A">ConversationContext</text>
      <line x1="6" y1="24" x2="149" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Appends assistant message</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Syncs to localStorage</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Thread history persisted</text>
      <rect x="6" y="62" width="143" height="11" rx="3" fill="#EFF6FF" />
      <text x="77" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="700" fill="#1D4ED8">State Persistence · Web</text>
    </g>

    <!-- Arrow 14 -> 15 -->
    <line x1="706" y1="69" x2="725" y2="69" stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow-gray)" />

    <!-- Step 15: ChatMessage.jsx -->
    <g transform="translate(727, 30)">
      <rect width="158" height="78" rx="6" fill="#FFFFFF" stroke="#10B981" stroke-width="2" filter="url(#jShadow)" />
      <rect x="6" y="6" width="22" height="14" rx="3" fill="#059669" />
      <text x="17" y="16.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#FFFFFF">15</text>
      <text x="33" y="17" font-family="'JetBrains Mono', monospace" font-size="8" font-weight="700" fill="#065F46">ChatMessage.jsx</text>
      <line x1="6" y1="24" x2="152" y2="24" stroke="#F1F5F9" stroke-width="1" />
      <text x="8" y="35" font-family="'Inter', sans-serif" font-size="7" font-weight="600" fill="#334155">• Markdown syntax rendering</text>
      <text x="8" y="46" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  Clickable citation pills</text>
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#64748B">  isLoading spinner cleared</text>
      <rect x="6" y="62" width="146" height="11" rx="3" fill="#ECFDF5" />
      <text x="79" y="70" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="6.5" font-weight="800" fill="#047857">UI Completed · Ready</text>
    </g>
  </g>

  <!-- ========================================== -->
  <!-- LEGEND & ARCHITECTURAL CONTRACTS FOOTER    -->
  <!-- ========================================== -->
  <g transform="translate(20, 502)">
    <rect width="900" height="52" rx="8" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1" />
    <g transform="translate(15, 10)">
      <rect width="125" height="18" rx="4" fill="#EFF6FF" stroke="#BFDBFE" />
      <text x="62.5" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7" font-weight="700" fill="#1D4ED8">Client Tier (React 18)</text>
    </g>
    <g transform="translate(150, 10)">
      <rect width="135" height="18" rx="4" fill="#EEF2FF" stroke="#C7D2FE" />
      <text x="67.5" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7" font-weight="700" fill="#4F46E5">Gateway (FastAPI/Pydantic)</text>
    </g>
    <g transform="translate(295, 10)">
      <rect width="145" height="18" rx="4" fill="#ECFDF5" stroke="#A7F3D0" />
      <text x="72.5" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#047857">Redis Cache (&lt;5ms / TTL 3600s)</text>
    </g>
    <g transform="translate(450, 10)">
      <rect width="145" height="18" rx="4" fill="#F3E8FF" stroke="#D8B4FE" />
      <text x="72.5" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#6B21A8">Vector DB (ChromaDB Top-4)</text>
    </g>
    <g transform="translate(605, 10)">
      <rect width="150" height="18" rx="4" fill="#FFFBEB" stroke="#FDE68A" />
      <text x="75" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#B45309">LLM (Gemini 2.5 Flash)</text>
    </g>
    <g transform="translate(765, 10)">
      <rect width="120" height="18" rx="4" fill="#FFF1F2" stroke="#FECDD3" />
      <text x="60" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="700" fill="#BE123C">Anti-Hallucination Gate</text>
    </g>
    <text x="450" y="42" text-anchor="middle" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">
      <tspan font-weight="700" fill="#334155">NexusRAG Execution Guarantees:</tspan> 60s Client Timeout · Asymmetric 768-dim Query Embedding · Strict Distance Guardrail · Deduplicated (source, page) Citations · Fail-Open Caching
    </text>
  </g>
</svg>"""

DIAGRAMS = {
    "diagram_cover_abstract.svg": SVG_COVER_ABSTRACT,
    "diagram_a_master_architecture.svg": SVG_DIAGRAM_A,
    "diagram_b_ingestion_pipeline.svg": SVG_DIAGRAM_B,
    "diagram_c_query_rag_flow.svg": SVG_DIAGRAM_C,
    "diagram_d_redis_cache_decision.svg": SVG_DIAGRAM_D,
    "diagram_e_backend_components.svg": SVG_DIAGRAM_E,
    "diagram_f_document_crud.svg": SVG_DIAGRAM_F,
    "diagram_g_safe_replacement.svg": SVG_DIAGRAM_G,
    "diagram_h_deployment_evolution.svg": SVG_DIAGRAM_H,
    "diagram_i_rag_vs_naive_llm.svg": SVG_DIAGRAM_I,
    "diagram_j_request_lifecycle.svg": SVG_DIAGRAM_J,
}

def write_svgs():
    for base in [DOCS_DIR, NEXUS_DIR]:
        diag_dir = os.path.join(base, "assets", "diagrams")
        os.makedirs(diag_dir, exist_ok=True)
        for name, content in DIAGRAMS.items():
            path = os.path.join(diag_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"Wrote {name} to {path}")

if __name__ == "__main__":
    write_svgs()
