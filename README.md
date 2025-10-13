# Mem0 Cathedral MCP Server (Python Edition)

**Intelligent memory management for Claude Desktop** - Quality filtering, smart deduplication, and better search triggering.

## Why Python v2.0?

The original Node.js version created too many low-quality memories with poor context. This Python rewrite adds:

- **Quality Filtering**: Rejects trivial acknowledgments and low-value content
- **Smart Deduplication**: Prevents saving similar/duplicate memories
- **Context Enrichment**: Automatically adds timestamps and clarifying context
- **Memory Consolidation**: Tool to find and merge redundant memories
- **Better Prompting**: Clearer tool descriptions that trigger more reliably in Claude

## Features

### Core Operations
- ✅ **add-memory** - Store memories with quality checks and deduplication
- ✅ **search-memories** - Semantic search with better Claude triggering
- ✅ **get-all-memories** - Retrieve all memories for context loading
- ✅ **update-memory** - Modify existing memories
- ✅ **delete-memory** - Remove specific memories
- ✅ **consolidate-memories** - Find and merge similar memories (NEW!)

### Intelligence Features
- **Quality Gating**: Minimum length, word count, and content validation
- **Duplicate Detection**: Semantic similarity checking before save
- **Context Enrichment**: Auto-adds timestamps and clarifying prefixes
- **Consolidation**: Identifies redundant memories for cleanup

## Installation

### Requirements
- Python 3.10+
- Mem0 API key from https://app.mem0.ai/

### Setup

1. **Clone to your MCP tools location:**
   ```bash
   git clone <repo-url> C:\mcptools\mem0-cathedral-mcp
   cd C:\mcptools\mem0-cathedral-mcp
   ```

2. **Install Python dependencies:**
   ```bash
   # Using pip
   pip install -r requirements.txt

   # Or using uv (recommended)
   uv pip install -r requirements.txt
   ```

3. **Update Claude Desktop config** (`%APPDATA%\Claude\claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "mem0": {
         "command": "python",
         "args": ["C:\\mcptools\\mem0-cathedral-mcp\\server.py"],
         "env": {
           "MEM0_API_KEY": "your_mem0_api_key_here"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop**

## Configuration

### Environment Variables

- **MEM0_API_KEY** (required): Your Mem0 API key
- Default user ID: `el-jefe-principal`

### Quality Thresholds (in server.py)

Customize these constants to adjust filtering:

```python
MIN_MEMORY_LENGTH = 20      # Minimum characters
MIN_WORD_COUNT = 4          # Minimum words
SIMILARITY_THRESHOLD = 0.85 # Deduplication threshold (0.0-1.0)
```

## Usage Examples

### Adding Memories (with Quality Filtering)

**Good memory (will save):**
```
User: I prefer TypeScript over JavaScript for type safety
Claude: [Calls add-memory]
✅ Saved with quality score: 120
```

**Low-quality memory (will reject):**
```
User: ok
Claude: [Calls add-memory]
❌ Rejected: "Too short, low-value acknowledgment"
```

**Force save bypass:**
```python
# In rare cases, force save low-quality content
{"content": "ok", "force": true}
```

### Searching Memories

The search tool now has clearer triggers. Claude will search when:
- User mentions past conversations
- User asks questions about themselves
- Discussing familiar topics
- Requesting recommendations

```
User: What programming languages do I prefer?
Claude: [Calls search-memories with query: "programming languages preferences"]
```

### Consolidating Memories

```
User: Clean up my memories
Claude: [Calls consolidate-memories with dryRun: true]

Response: Found 5 similar memory pairs:
  1. "User prefers Python" ↔ "User likes Python for data science" (similarity: 0.82)
  2. "Working on MCP project" ↔ "Building Mem0 MCP server" (similarity: 0.76)
  ...
```

## Architecture

- **Language**: Python 3.10+
- **MCP SDK**: `mcp` (official Python SDK)
- **Mem0 Client**: `mem0ai` (official Python SDK)
- **Protocol**: stdio (standard input/output)
- **Async**: Full async/await support

## Comparison: Node.js vs Python

| Feature | Node.js (v1.0) | Python (v2.0) |
|---------|---------------|---------------|
| Quality Filtering | ❌ | ✅ |
| Deduplication | ❌ | ✅ |
| Context Enrichment | ❌ | ✅ |
| Memory Consolidation | ❌ | ✅ |
| Smart Search Prompts | ⚠️ Verbose | ✅ Concise |
| Async Support | ✅ | ✅ |
| Native Mem0 SDK | ❌ | ✅ |

## API Quality Features

### Memory Quality Assessment

Before saving, each memory is scored:
- ✅ **Good**: Length ≥20 chars, ≥4 words, has context indicators
- ⚠️ **Warning**: Very long (>500 chars) - may need summarization
- ❌ **Reject**: Too short, acknowledgments only, no context

### Context Indicators

Memories containing these terms get bonus points:
- Preferences: "prefer", "like", "love", "hate", "always", "never"
- Technical: "project", "tool", "language", "technology"
- Personal: "name is", "location", "timezone", "schedule"
- Goals: "goal", "objective", "plan", "want to", "need to"

## Troubleshooting

### Server not starting
- Check Python version: `python --version` (need 3.10+)
- Verify MEM0_API_KEY is set in config
- Check logs: `%APPDATA%\Claude\logs\mcp-server-mem0.log`

### Dependencies not found
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Too many memories rejected
Lower quality thresholds in [server.py:23-25](server.py#L23-L25):
```python
MIN_MEMORY_LENGTH = 10   # Was 20
MIN_WORD_COUNT = 2       # Was 4
```

### Search not triggering
Tool description has been optimized, but you can further customize at [server.py:170-178](server.py#L170-L178)

## Development Workflow

### Dev/Prod Split
- **Dev**: `C:\Users\jonat\OneDrive\Coding Projects\mem0-cathedral-mcp\`
- **Prod**: `C:\mcptools\mem0-cathedral-mcp\`

### Testing Locally

```bash
# Set API key
set MEM0_API_KEY=your_key_here

# Run server directly
python server.py

# Test with MCP inspector
mcp dev server.py
```

### Deploying to Production

```bash
cd C:\mcptools\mem0-cathedral-mcp
git pull
# Restart Claude Desktop
```

## Version History

- **2.0.0** (Python) - Complete rewrite with intelligent filtering
- **1.0.0** (Node.js) - Original cathedral implementation

## Migration from Node.js

1. **Backup existing config** (optional)
2. **Install Python dependencies**
3. **Update Claude Desktop config** to use Python
4. **Test with a few memories** to verify quality filtering
5. **Run consolidate-memories** to clean up old duplicates

No data migration needed - same Mem0 API backend!

## Credits

Originally based on [mem0-cathedral-api](https://github.com/1818TusculumSt/mem0-cathedral-api) for Open WebUI.

Python rewrite by El Jefe Principal with intelligent quality management. 🧠
