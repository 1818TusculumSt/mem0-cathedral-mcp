# Upgrade Guide: v2.0.0 → v12.1.0 (The Silent Oracle)

## Overview

This is a **MAJOR upgrade** that brings the MCP version to full feature parity with the API version (mem0-cathedral-api). Version numbering has been synchronized across both implementations.

## What's New in v12.1.0

### 🤖 AI Extraction Mode
- **Before:** Only manual content extraction via `content` parameter
- **After:** Pass `messages` array and Mem0's AI extracts memories automatically
- **Benefit:** Multiple high-quality memories extracted from single conversation

### 🧠 Intelligent Auto-Recall
- **New Tool:** `get-context` - Proactively retrieves relevant memories
- **Hybrid Search:** Semantic (Mem0) + Lexical (keyword matching)
- **Keyword Reranking:** 15% score boost per matching keyword
- **Benefit:** Better context relevance for conversations

### 🤫 Silent Operations
- **Before:** Verbose JSON responses with quality scores, rejection reasons, etc.
- **After:** Minimal `{success: true/false}` responses
- **Benefit:** No chat clutter - memory operations happen invisibly

### 📂 Custom Categories
- **12 Default Categories:** personal_information, preferences, work, food_preferences, technical, goals, health, hobbies, relationships, location, schedule, communication
- **Custom Override:** Pass `customCategories` to define your own
- **Benefit:** Organized, searchable memories by topic

### 🕸️ Graph Memory
- **Feature:** Entity relationship tracking via `enableGraph` parameter
- **Benefit:** Better contextual retrieval through entity connections

### 🤝 Multi-Agent & Session Tracking
- **New Parameters:** `agentId`, `runId`
- **Benefit:** Track memories by AI agent and conversation session

### ⚡ Enhanced Search
- **Category Filtering:** Search within specific categories
- **Graph Support:** Include entity relationships in results
- **Agent/Session Filters:** Filter by agentId or runId

## Breaking Changes

### Tool Response Format

**add-memory responses:**

```diff
# BEFORE (v2.0.0)
{
  "ok": true,
  "memory_id": "mem_123",
  "quality_score": 120,
  "message": "Memory saved successfully"
}

# AFTER (v12.1.0)
{
  "success": true
}
```

**Rejections are now silent** (logged server-side only):

```diff
# BEFORE (v2.0.0)
{
  "ok": false,
  "rejected": true,
  "reason": "Quality threshold not met",
  "issues": ["Too short (min 20 chars)"],
  "suggestion": "Provide more context"
}

# AFTER (v12.1.0)
{
  "success": false
}
```

## Migration Steps

### 1. Pull Latest Code

```bash
cd C:\mcptools\mem0-cathedral-mcp
git pull
```

### 2. No Dependency Changes

The `mem0ai` SDK version remains the same. No need to reinstall dependencies.

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new server.

### 4. Test New Features

Try the new `get-context` tool:
```
You: What do you know about my food preferences?
Claude: [Calls get-context, gets formatted context]
```

Try AI extraction mode:
```
You: I love Python but I'm learning Rust for systems programming
Claude: [Calls add-memory with messages array]
```

## New Tool: get-context

### Purpose
Intelligent auto-recall for injecting relevant memories into conversation context.

### Usage
```json
{
  "currentMessage": "What should I eat for dinner?",
  "recentMessages": [
    {"role": "user", "content": "I'm hungry"},
    {"role": "assistant", "content": "What sounds good?"}
  ],
  "maxMemories": 10,
  "enableGraph": true
}
```

### Response
```json
{
  "context": "## User Context\n\n### Food Preferences\n- User loves pizza\n- User dislikes pineapple on pizza\n\n",
  "memories": [...],
  "count": 2,
  "total_searched": 6
}
```

### When to Use
- **Proactively** at conversation start
- When user asks questions you might have context for
- Before making recommendations
- When discussing familiar topics

## Enhanced add-memory Tool

### Mode 1: AI Extraction (RECOMMENDED)

**New `messages` parameter:**
```json
{
  "messages": [
    {"role": "user", "content": "I love pizza but hate pineapple on it"},
    {"role": "assistant", "content": "I'll remember that!"}
  ],
  "enableGraph": true,
  "metadata": {
    "location": "Chicago",
    "tags": ["food", "preferences"]
  }
}
```

**Mem0 extracts:**
- "User loves pizza"
- "User dislikes pineapple on pizza"

### Mode 2: Legacy Content (Backward Compatible)

**Old `content` parameter still works:**
```json
{
  "content": "User prefers TypeScript over JavaScript for type safety"
}
```

### New Optional Parameters

- `agentId` (string) - AI agent identifier
- `runId` (string) - Conversation session ID
- `customCategories` (object) - Override default categories
- `customInstructions` (string) - Guide AI extraction
- `metadata` (object) - Structured metadata
- `enableGraph` (boolean) - Build entity relationships
- `includes` (string) - Focus extraction on topics
- `excludes` (string) - Exclude patterns

## Enhanced search-memories Tool

### New Parameters

```json
{
  "query": "programming preferences",
  "categories": ["technical", "preferences"],
  "agentId": "coding-assistant",
  "runId": "session_123",
  "enableGraph": true,
  "limit": 20
}
```

### Response Format

```json
{
  "results": [
    {
      "id": "mem_123",
      "content": "User prefers Python",
      "categories": ["technical", "preferences"],
      "score": 0.92,
      "created_at": "2025-01-20T10:00:00Z"
    }
  ],
  "count": 1,
  "filters_applied": {
    "categories": ["technical", "preferences"],
    "graph_enabled": true
  }
}
```

## Default Categories

When using AI extraction, memories are automatically categorized:

| Category | Description |
|----------|-------------|
| `personal_information` | Name, location, age, family, background |
| `preferences` | Likes, dislikes, favorites, personal tastes |
| `work` | Career, projects, professional information |
| `food_preferences` | Food likes, dislikes, dietary restrictions |
| `technical` | Tech stack, tools, programming languages |
| `goals` | Objectives, plans, aspirations, future intentions |
| `health` | Health conditions, fitness routines, wellness |
| `hobbies` | Interests, activities, pastimes |
| `relationships` | Friends, family, colleagues, connections |
| `location` | Places lived, traveled, or frequently visited |
| `schedule` | Routines, availability, time preferences |
| `communication` | Preferred communication styles and channels |

## Backward Compatibility

✅ **All v2.0.0 functionality is preserved:**
- Old `add-memory` with `content` works
- Quality filtering still applies in legacy mode
- Deduplication still works
- All other tools unchanged (get-all-memories, update-memory, delete-memory, consolidate-memories)

⚠️ **Response format is different:**
- Tools now return minimal responses
- This may affect any automation that parses responses
- Check Claude Desktop logs for detailed info: `%APPDATA%\Claude\logs\mcp-server-mem0.log`

## Troubleshooting

### "Tool not found" errors

**Solution:** Restart Claude Desktop completely (not just reload).

### Silent rejections - memory not saving

**Check logs:**
```powershell
Get-Content $env:APPDATA\Claude\logs\mcp-server-mem0.log -Tail 50
```

**Common reasons:**
- Quality threshold not met (too short, low value)
- Duplicate detected (similarity > 0.85)
- Mem0 API error

**Override quality checks:**
```json
{
  "content": "short text",
  "force": true
}
```

### get-context returns empty

**Possible causes:**
- No relevant memories found
- Query too specific
- Memories haven't been created yet

**Try broader queries:**
```json
{
  "currentMessage": "preferences",  // Broad query
  "maxMemories": 20  // Increase limit
}
```

### AI extraction not working

**Check:**
1. Using `messages` parameter (not `content`)
2. Messages are properly formatted with `role` and `content`
3. MEM0_API_KEY is valid
4. Check server logs for API errors

## Best Practices

### When to Use AI Extraction vs Manual

**Use AI Extraction (`messages`) when:**
- You have conversation context available
- You want multiple memories from one interaction
- You want automatic categorization
- You're okay with Mem0's extraction quality

**Use Manual (`content`) when:**
- You need precise control over what's saved
- You've already extracted the exact memory text
- Backward compatibility with existing code
- Testing or debugging

### When to Use get-context vs search-memories

**Use `get-context` when:**
- You want proactive context injection
- You have the user's current message
- You want keyword reranking for better relevance
- You want formatted context ready for LLM

**Use `search-memories` when:**
- You need specific category filtering
- You want to search by agent_id or run_id
- You need raw memory data for processing
- You're building custom context formatting

## Performance Notes

### Keyword Reranking Strategy

`get-context` retrieves 3x the requested memories, then reranks:

```
maxMemories: 10
↓
Retrieve 30 from Mem0 (semantic search)
↓
Rerank by keyword matching (+15% per match)
↓
Return top 10
```

**Benefit:** Better relevance without sacrificing semantic search quality.

### Silent Operations Impact

**Before:** Large JSON responses consumed tokens and cluttered chat.

**After:** Minimal responses save tokens and provide cleaner UX.

**Trade-off:** Less visibility into what happened. Check logs for details.

## Version Numbering

**Why the jump from 2.0.0 to 12.1.0?**

To synchronize with the API version (mem0-cathedral-api), which is at v12.1.0. Both implementations now have feature parity and share the same version number.

## Support

If you encounter issues:

1. **Check logs:** `%APPDATA%\Claude\logs\mcp-server-mem0.log`
2. **Test server directly:** `python server.py` (will show startup errors)
3. **Report issues:** [GitHub Issues](https://github.com/1818TusculumSt/mem0-cathedral-mcp/issues)

## Rollback

If you need to revert to v2.0.0:

```bash
cd C:\mcptools\mem0-cathedral-mcp
git checkout v2.0.0
# Restart Claude Desktop
```

Note: Memories created with v12.1.0 categories will still work in v2.0.0.
