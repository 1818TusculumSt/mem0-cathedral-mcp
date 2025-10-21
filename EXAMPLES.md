# Mem0 Cathedral MCP v12.1.0 - Usage Examples

## Table of Contents

1. [Basic AI Extraction](#1-basic-ai-extraction)
2. [Multi-Category Extraction](#2-multi-category-extraction)
3. [Category Filtering Search](#3-category-filtering-search)
4. [Multi-Agent Session Tracking](#4-multi-agent-session-tracking)
5. [Custom Extraction Instructions](#5-custom-extraction-instructions)
6. [Custom Categories](#6-custom-categories)
7. [Legacy Manual Mode](#7-legacy-manual-mode)
8. [Graph Memory Relationships](#8-graph-memory-relationships)
9. [Intelligent Auto-Recall](#9-intelligent-auto-recall)
10. [Metadata Filtering](#10-metadata-filtering)
11. [Memory Consolidation](#11-memory-consolidation)
12. [Silent Operations in Practice](#12-silent-operations-in-practice)

---

## 1. Basic AI Extraction

**Scenario:** User shares food preferences in conversation.

**Input:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {"role": "user", "content": "I love pizza but I absolutely hate pineapple on it"},
      {"role": "assistant", "content": "Got it! I'll remember your pizza preferences."}
    ]
  }
}
```

**What Mem0 Extracts:**
- "User loves pizza" → category: `food_preferences`
- "User dislikes pineapple on pizza" → category: `food_preferences`

**Response:**
```json
{
  "success": true
}
```

---

## 2. Multi-Category Extraction

**Scenario:** User shares work and technical preferences.

**Input:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {
        "role": "user",
        "content": "I'm a Python developer working on a machine learning project at Google. I prefer VSCode over PyCharm."
      },
      {
        "role": "assistant",
        "content": "Interesting! I'll remember your work details and tool preferences."
      }
    ],
    "enableGraph": true
  }
}
```

**What Mem0 Extracts:**
- "User is a Python developer" → category: `work`, `technical`
- "User works on machine learning project" → category: `work`, `technical`
- "User works at Google" → category: `work`
- "User prefers VSCode over PyCharm" → category: `technical`, `preferences`

**Graph Entities Created:**
- User → works_with → Python
- User → works_at → Google
- User → prefers → VSCode

**Response:**
```json
{
  "success": true
}
```

---

## 3. Category Filtering Search

**Scenario:** Search only technical memories.

**Input:**
```json
{
  "tool": "search-memories",
  "arguments": {
    "query": "programming tools",
    "categories": ["technical", "preferences"],
    "limit": 10
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "mem_abc123",
      "content": "User prefers VSCode over PyCharm",
      "categories": ["technical", "preferences"],
      "score": 0.92,
      "created_at": "2025-01-20T10:00:00Z"
    },
    {
      "id": "mem_def456",
      "content": "User is a Python developer",
      "categories": ["technical", "work"],
      "score": 0.87,
      "created_at": "2025-01-20T09:30:00Z"
    }
  ],
  "count": 2,
  "filters_applied": {
    "categories": ["technical", "preferences"]
  }
}
```

---

## 4. Multi-Agent Session Tracking

**Scenario:** Different AI agents saving memories for the same user.

**Coding Assistant Agent:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {"role": "user", "content": "I prefer functional programming over OOP"},
      {"role": "assistant", "content": "Noted!"}
    ],
    "agentId": "coding-assistant",
    "runId": "session_20250120_001"
  }
}
```

**Recipe Assistant Agent:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {"role": "user", "content": "I'm allergic to peanuts"},
      {"role": "assistant", "content": "I'll remember that for recipe suggestions!"}
    ],
    "agentId": "recipe-assistant",
    "runId": "session_20250120_002"
  }
}
```

**Search by Agent:**
```json
{
  "tool": "search-memories",
  "arguments": {
    "query": "preferences",
    "agentId": "coding-assistant"
  }
}
```

**Returns:** Only memories from coding-assistant agent.

---

## 5. Custom Extraction Instructions

**Scenario:** Guide Mem0 to focus on specific aspects.

**Input:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {
        "role": "user",
        "content": "I usually wake up at 6am, work out for an hour, then have breakfast. I prefer to work in the mornings when I'm most productive."
      }
    ],
    "customInstructions": "Focus on extracting daily routines, time preferences, and productivity patterns. Include specific times mentioned."
  }
}
```

**What Mem0 Extracts (with guidance):**
- "User wakes up at 6am" → category: `schedule`
- "User works out for one hour after waking" → category: `health`, `schedule`
- "User prefers morning work for productivity" → category: `schedule`, `work`
- "User is most productive in mornings" → category: `work`, `preferences`

---

## 6. Custom Categories

**Scenario:** Define your own categories for specialized use case.

**Input:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {"role": "user", "content": "I play guitar and I'm learning jazz improvisation"},
      {"role": "assistant", "content": "Cool! What style of jazz?"}
    ],
    "customCategories": {
      "music_skills": "Musical instruments and abilities",
      "learning_goals": "Things the user is actively learning",
      "creative_pursuits": "Artistic and creative activities"
    }
  }
}
```

**What Mem0 Extracts (with custom categories):**
- "User plays guitar" → category: `music_skills`, `creative_pursuits`
- "User is learning jazz improvisation" → category: `learning_goals`, `music_skills`

---

## 7. Legacy Manual Mode

**Scenario:** Precise control over memory content (backward compatible with v2.0.0).

**Input:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "content": "User strongly prefers dark mode in all applications and finds light mode eye-straining"
  }
}
```

**What Happens:**
1. Quality assessment (length, word count, context indicators)
2. Duplicate detection (similarity check against existing)
3. Context enrichment (timestamp added)
4. Save to Mem0

**Response:**
```json
{
  "success": true
}
```

**Force Save (bypass quality checks):**
```json
{
  "tool": "add-memory",
  "arguments": {
    "content": "likes cats",
    "force": true
  }
}
```

---

## 8. Graph Memory Relationships

**Scenario:** Build entity relationship graph.

**Input:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {
        "role": "user",
        "content": "My friend Sarah recommended that Italian restaurant downtown. She knows I love pasta."
      }
    ],
    "enableGraph": true
  }
}
```

**Graph Entities Created:**
- User → friend_with → Sarah
- Sarah → recommended → Italian restaurant downtown
- User → loves → pasta
- Italian restaurant → serves → pasta

**Search with Graph:**
```json
{
  "tool": "search-memories",
  "arguments": {
    "query": "restaurant recommendations",
    "enableGraph": true
  }
}
```

**Returns:** Memories about the Italian restaurant, including relationship context (Sarah recommended it, user loves pasta).

---

## 9. Intelligent Auto-Recall

**Scenario:** Proactively inject relevant context into conversation.

**User's Current Message:** "What should I eat for dinner tonight?"

**Get Context:**
```json
{
  "tool": "get-context",
  "arguments": {
    "currentMessage": "What should I eat for dinner tonight?",
    "recentMessages": [
      {"role": "user", "content": "I'm really hungry"},
      {"role": "assistant", "content": "What are you in the mood for?"}
    ],
    "maxMemories": 10,
    "enableGraph": true
  }
}
```

**Response:**
```json
{
  "context": "## User Context\n\n### Food Preferences\n- User loves pizza\n- User dislikes pineapple on pizza\n- User is allergic to peanuts\n\n### Health\n- User is trying to eat healthier\n\n### Location\n- User lives in Chicago\n\n",
  "memories": [
    {"id": "mem_1", "memory": "User loves pizza", "score": 0.95},
    {"id": "mem_2", "memory": "User is allergic to peanuts", "score": 0.89},
    {"id": "mem_3", "memory": "User dislikes pineapple on pizza", "score": 0.87},
    {"id": "mem_4", "memory": "User is trying to eat healthier", "score": 0.82},
    {"id": "mem_5", "memory": "User lives in Chicago", "score": 0.78}
  ],
  "count": 5,
  "total_searched": 15
}
```

**How Keyword Reranking Works:**
1. Search query: "What should I eat for dinner tonight? I'm really hungry What are you in the mood for?"
2. Extract keywords: `["eat", "dinner", "tonight", "hungry", "mood"]`
3. Retrieve 30 candidate memories (3x the requested 10)
4. Rerank by keyword matching:
   - "User loves pizza" - matches "eat" → +15% boost
   - "User is allergic to peanuts" - matches "eat" → +15% boost
5. Return top 10 after reranking

**Claude then uses this context invisibly in the response.**

---

## 10. Metadata Filtering

**Scenario:** Add structured metadata for advanced filtering.

**Save with Metadata:**
```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {"role": "user", "content": "I had an amazing sushi experience at Miku in Vancouver"}
    ],
    "metadata": {
      "location": "Vancouver, BC",
      "restaurant_name": "Miku",
      "cuisine_type": "Japanese",
      "experience_rating": 5,
      "date": "2025-01-20",
      "tags": ["food", "travel", "recommendation"]
    }
  }
}
```

**Later Retrieval:**
All metadata is stored and returned with search results, enabling custom filtering in your application.

---

## 11. Memory Consolidation

**Scenario:** Find and merge duplicate/similar memories.

**Input:**
```json
{
  "tool": "consolidate-memories",
  "arguments": {
    "dryRun": true
  }
}
```

**Response:**
```json
{
  "ok": true,
  "dry_run": true,
  "candidates": [
    {
      "memory1_id": "mem_abc",
      "memory1_content": "User prefers Python for data science",
      "memory2_id": "mem_def",
      "memory2_content": "User likes Python for ML work",
      "similarity": 0.82
    },
    {
      "memory1_id": "mem_ghi",
      "memory1_content": "User works at Google",
      "memory2_id": "mem_jkl",
      "memory2_content": "User is employed by Google",
      "similarity": 0.91
    }
  ],
  "count": 2,
  "message": "Review these candidates. Use update-memory and delete-memory to consolidate manually."
}
```

**Manual Consolidation:**
1. Review candidates
2. Update one memory with merged content
3. Delete the duplicate

---

## 12. Silent Operations in Practice

**Before v12.1.0 (Verbose):**

```
User: I love TypeScript
Claude: Let me save that to memory...
[Calls add-memory]
✅ Memory saved successfully with quality score 120. Memory ID: mem_abc123.
Great! I've saved your preference for TypeScript.
```

**After v12.1.0 (Silent):**

```
User: I love TypeScript
Claude: [Calls add-memory silently]
Got it! TypeScript is a great choice for type-safe development.
```

**User sees:** Natural conversation, no technical details about memory operations.

**What Actually Happened (server logs):**
```
[2025-01-20 10:30:15] add-memory called with messages array
[2025-01-20 10:30:16] Mem0 AI extraction: 2 memories extracted
[2025-01-20 10:30:16] Categories: ['technical', 'preferences']
[2025-01-20 10:30:16] Response: {success: true}
```

**If Rejected (server logs):**
```
[2025-01-20 10:30:15] add-memory called with content: "ok"
[2025-01-20 10:30:15] Memory rejected: ['Too short (min 20 chars)', 'Too few words (min 4 words)', 'Low-value acknowledgment']
[2025-01-20 10:30:15] Response: {success: false}
```

**User sees:** Nothing (silent rejection).

---

## Tips for Best Results

### AI Extraction
- ✅ Include both user and assistant messages for context
- ✅ Let conversations be natural - Mem0 handles extraction
- ✅ Enable graph memory for relationship tracking
- ❌ Don't pre-filter or summarize - let AI extract

### Auto-Recall
- ✅ Call `get-context` proactively at conversation start
- ✅ Include recent messages for better query understanding
- ✅ Use keyword reranking (default) for better relevance
- ❌ Don't mention the function call to users (silent operation)

### Search
- ✅ Use category filters to narrow results
- ✅ Enable graph memory for relationship context
- ✅ Use `get-context` instead of `search-memories` for auto-recall
- ❌ Don't search for exact text matches (use semantic queries)

### Legacy Mode
- ✅ Use for backward compatibility
- ✅ Use when you need precise control
- ✅ Force save only when absolutely necessary
- ❌ Don't use when AI extraction would work better

---

## Advanced: Combining Features

**Multi-Agent + Graph + Categories + Metadata:**

```json
{
  "tool": "add-memory",
  "arguments": {
    "messages": [
      {
        "role": "user",
        "content": "My coworker Alex suggested I try the new React hooks pattern for state management in our project"
      }
    ],
    "agentId": "coding-assistant",
    "runId": "session_project_alpha",
    "enableGraph": true,
    "metadata": {
      "project": "alpha",
      "context": "work",
      "team_member": "Alex",
      "technology": "React",
      "timestamp": "2025-01-20T10:30:00Z"
    }
  }
}
```

**What Happens:**
1. **AI Extraction:** Mem0 extracts memories about React hooks, Alex's suggestion
2. **Categorization:** Assigns to `work`, `technical` categories
3. **Graph:** Creates relationships: User → works_with → Alex, User → uses → React, Alex → suggested → React hooks
4. **Multi-Agent:** Associates with "coding-assistant" agent
5. **Session:** Links to "session_project_alpha" run
6. **Metadata:** Stores structured data for advanced filtering

**Later Retrieval (Highly Targeted):**

```json
{
  "tool": "search-memories",
  "arguments": {
    "query": "React recommendations",
    "agentId": "coding-assistant",
    "categories": ["technical", "work"],
    "enableGraph": true
  }
}
```

**Returns:** Exactly this memory with full context including Alex's relationship and project metadata.

---

That's it! You now have full feature parity with the API version. 🎉
