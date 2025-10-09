# Mem0 Cathedral MCP Server

Full-featured Mem0 MCP server for Claude Desktop, providing complete memory management capabilities based on the cathedral-api implementation.

## Features

This MCP server provides **all 6 Mem0 operations**, compared to the basic @mem0/mcp-server which only provides 2:

- ✅ **add-memory** - Store new memories with user context
- ✅ **search-memories** - Query memories with configurable limits (up to 100 results)
- ✅ **get-memory** - Retrieve specific memory by ID
- ✅ **update-memory** - Modify existing memory content
- ✅ **delete-memory** - Remove memories permanently
- ✅ **get-memory-history** - View memory modification history

## Installation

1. **Clone or copy this directory** to your MCP tools location:
   ```
   C:\mcptools\mem0-cathedral-mcp\
   ```

2. **Install dependencies:**
   ```bash
   cd C:\mcptools\mem0-cathedral-mcp
   npm install
   ```

3. **Update Claude Desktop config** (`%APPDATA%\Claude\claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "mem0": {
         "command": "node",
         "args": ["C:\\mcptools\\mem0-cathedral-mcp\\index.js"],
         "env": {
           "MEM0_API_KEY": "your_mem0_api_key_here"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop**

## Configuration

### Required Environment Variables

- `MEM0_API_KEY` - Your Mem0 API key (required)
  - Get yours at: https://app.mem0.ai/

### Optional Settings

- Default user ID: `el-jefe-principal` (automatically used if not specified)
- Default search limit: 100 memories

## Usage in Claude Desktop

Once configured, Claude Desktop will automatically have access to all 6 memory tools:

### Adding Memories
```
User: Remember that I prefer dark mode
Claude: [Calls add-memory with content: "User prefers dark mode"]
```

### Searching Memories
```
User: What do you know about my preferences?
Claude: [Calls search-memories with query: "preferences"]
```

### Getting Specific Memory
```
Claude: [Calls get-memory with memoryId: "abc123"]
```

### Updating Memory
```
User: Actually, I prefer light mode now
Claude: [Calls update-memory with memoryId and new text]
```

### Deleting Memory
```
User: Forget about my color preferences
Claude: [Calls delete-memory with memoryId]
```

### Viewing History
```
Claude: [Calls get-memory-history with memoryId to see changes]
```

## Architecture

- **Protocol**: MCP (Model Context Protocol)
- **Runtime**: Node.js 18+
- **SDK**: @modelcontextprotocol/sdk v1.0.4
- **HTTP Client**: node-fetch v3.3.2
- **Transport**: stdio (standard input/output)

## Comparison with @mem0/mcp-server

| Feature | @mem0/mcp-server | mem0-cathedral-mcp |
|---------|-----------------|-------------------|
| Add Memory | ✅ | ✅ |
| Search Memories | ✅ | ✅ |
| Get Memory | ❌ | ✅ |
| Update Memory | ❌ | ✅ |
| Delete Memory | ❌ | ✅ |
| Get History | ❌ | ✅ |
| Custom User IDs | ✅ | ✅ |
| Configurable Limits | ❌ | ✅ |

## API Reference

The server communicates with Mem0's v1 API at `https://api.mem0.ai/v1`.

All operations use Token-based authentication via the `MEM0_API_KEY`.

## Troubleshooting

### Server not starting
- Check that Node.js 18+ is installed: `node --version`
- Verify the path in claude_desktop_config.json is correct
- Check Claude Desktop logs at: `%APPDATA%\Claude\logs\mcp-server-mem0.log`

### API errors
- Verify your MEM0_API_KEY is valid
- Check your internet connection
- Review the error message in the tool response

### Tools not appearing
- Restart Claude Desktop after config changes
- Check that the config JSON is valid (use a JSON validator)
- Look for errors in the Claude Desktop logs

## Development Workflow

This project uses a **dev/prod split**:

- **Dev**: `C:\Users\jonat\OneDrive\Coding Projects\mem0-cathedral-mcp\` - Make changes here, commit to GitHub
- **Prod**: `C:\mcptools\mem0-cathedral-mcp\` - Running container serving live traffic to Claude Desktop

### Workflow Steps

1. **Development**: Clone repo, make changes in dev folder, test locally
2. **Commit**: Push changes to GitHub from dev folder
3. **Deploy**: Pull on production folder, restart Claude Desktop

### Testing the Server Manually

```bash
set MEM0_API_KEY=your_key_here
echo {"jsonrpc":"2.0","method":"tools/list","params":{},"id":1} | node index.js
```

### Deploying to Production

```bash
# In production folder
cd C:\mcptools\mem0-cathedral-mcp
git pull
# Restart Claude Desktop
```

## Version

**1.0.0** - Full-featured cathedral implementation

## Credits

Based on the [mem0-cathedral-api](https://github.com/1818TusculumSt/mem0-cathedral-api) FastAPI implementation for Open WebUI.

Adapted for Claude Desktop MCP by El Jefe Principal. 🏗️
