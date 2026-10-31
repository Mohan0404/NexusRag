"""
Test script to generate and validate the new SVG_DIAGRAM_J.
"""
import os

SVG_DIAGRAM_J_NEW = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 570" width="100%" height="570">
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
    <text x="118" y="28" font-family="'Inter', sans-serif" font-size="8.5" fill="#64748B">Comprehensive execution trace from React input submission, through FastAPI routing, Redis caching, ChromaDB retrieval, Gemini LLM, to UI rendering</text>
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
  <path d="M 806 324 L 806 348 L 112 348 L 112 388" fill="none" stroke="#4F46E5" stroke-width="2" marker-end="url(#arrow-indigo)" />
  <g transform="translate(180, 339)">
    <rect width="320" height="18" rx="4" fill="#EEF2FF" stroke="#6366F1" stroke-width="1.2" filter="url(#jShadow)" />
    <text x="160" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#3730A3">▼ LLM ANSWER GENERATED: Deduplicate Citations &amp; Write Cache</text>
  </g>

  <!-- CACHE HIT FAST-TRACK BYPASS (From 05 right to 13 top) -->
  <path d="M 885 125 L 912 125 L 912 360 L 452 360 L 452 388" fill="none" stroke="#10B981" stroke-width="2.5" stroke-dasharray="5,3" marker-end="url(#arrow-green)" />
  <g transform="translate(560, 351)">
    <rect width="310" height="18" rx="4" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5" filter="url(#jShadow)" />
    <text x="155" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7.5" font-weight="800" fill="#065F46">⚡ CACHE HIT: &lt; 5ms (Skips Steps 06–12) ──► Joins at Step 13</text>
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
      <text x="8" y="57" font-family="'Inter', sans-serif" font-size="6.8" fill="#059669">  ◄ Cache Hit joins here</text>
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
      <text x="72.5" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7" font-weight="700" fill="#6B21A8">Vector DB (ChromaDB Top-4)</text>
    </g>
    <g transform="translate(605, 10)">
      <rect width="150" height="18" rx="4" fill="#FFFBEB" stroke="#FDE68A" />
      <text x="75" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7" font-weight="700" fill="#B45309">LLM (Gemini 2.5 Flash)</text>
    </g>
    <g transform="translate(765, 10)">
      <rect width="120" height="18" rx="4" fill="#FFF1F2" stroke="#FECDD3" />
      <text x="60" y="12.5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="7" font-weight="700" fill="#BE123C">Anti-Hallucination Gate</text>
    </g>
    <text x="450" y="42" text-anchor="middle" font-family="'Inter', sans-serif" font-size="7.5" fill="#64748B">
      <tspan font-weight="700" fill="#334155">NexusRAG Execution Guarantees:</tspan> 60s Client Timeout · Asymmetric 768-dim Query Embedding · Strict Distance Guardrail · Deduplicated (source, page) Citations · Fail-Open Caching
    </text>
  </g>
</svg>"""

with open(r"D:\Academic-Projects\RAG\scratch\test_diagram_j.svg", "w", encoding="utf-8") as f:
    f.write(SVG_DIAGRAM_J_NEW)
print("Wrote test_diagram_j.svg successfully.")
