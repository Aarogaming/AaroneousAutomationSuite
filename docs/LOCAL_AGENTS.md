# Local Agent Framework Integration

## Overview

This guide covers the integration of privacy-focused, offline-capable AI agent frameworks within the Aaroneous Automation Suite. These frameworks enable autonomous task execution, knowledge management, and workflow automation without requiring cloud dependencies.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AAS Orchestration Hub                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   ARGO      │  │    Clara     │  │   Observer   │      │
│  │  (Native    │  │  (Modular    │  │     AI       │      │
│  │   Agent)    │  │  Workspace)  │  │  (Coding)    │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Workflow & Knowledge Layer                 │   │
│  │  ┌───────────┐  ┌──────────────┐  ┌─────────────┐ │   │
│  │  │    n8n    │  │  AnythingLLM │  │   Flowise   │ │   │
│  │  │(Workflows)│  │ (Knowledge)  │  │   (Visual)  │ │   │
│  │  └───────────┘  └──────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Model Inference Layer                   │   │
│  │  ┌───────────┐  ┌──────────────┐  ┌─────────────┐ │   │
│  │  │  Ollama   │  │   LocalAI    │  │  llamafile  │ │   │
│  │  │(Primary)  │  │  (OpenAI     │  │  (Single    │ │   │
│  │  │           │  │   API compat)│  │   Binary)   │ │   │
│  │  └───────────┘  └──────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Supported Frameworks

### 1. ARGO (Agent Runtime & Goal Orchestrator)

**Purpose:** Native Python agent runtime for task decomposition and autonomous execution.

**Repository:** [ARGO GitHub](https://github.com/yourusername/argo) *(example link)*

**Features:**
- Goal-oriented task planning
- Dynamic tool discovery
- Memory persistence across sessions
- Built-in error recovery

**Installation:**
```bash
pip install argo-agent
```

**Integration:**
```python
from core.handoff.agents.argo_client import ARGOClient

# Initialize ARGO agent
argo = ARGOClient(
    model_endpoint="http://localhost:11434",  # Ollama
    memory_path="artifacts/argo/memory",
    tool_registry=hub.get_tool_registry()
)

# Execute goal
result = await argo.execute_goal(
    goal="Refactor combat logic for improved modularity",
    context={"project_root": "core/deimos"}
)
```

**Configuration:**
```python
# core/config/manager.py
class ARGOConfig(BaseSettings):
    argo_enabled: bool = Field(default=False, alias="ARGO_ENABLED")
    argo_memory_path: str = Field(default="artifacts/argo/memory")
    argo_max_iterations: int = Field(default=10)
```

---

### 2. Clara (Modular AI Workspace)

**Purpose:** Provides a modular, plugin-based workspace for collaborative AI tasks.

**Repository:** [Clara GitHub](https://github.com/clara-labs/clara)

**Features:**
- Plugin ecosystem for specialized tasks
- Web-based UI for monitoring
- Multi-agent collaboration
- Project scaffolding

**Installation:**
```bash
npm install -g clara-cli
clara init --workspace aas-workspace
```

**Integration:**
```python
from core.handoff.agents.clara_client import ClaraClient

clara = ClaraClient(workspace_path="artifacts/clara/workspace")

# Create a project for a specific plugin
clara.create_project(
    name="home_assistant_integration",
    plugin="plugins/home_assistant",
    agents=["research", "coding", "testing"]
)
```

**Workspace Structure:**
```
artifacts/clara/workspace/
├── projects/
│   ├── home_assistant_integration/
│   │   ├── context.json
│   │   ├── plan.md
│   │   └── artifacts/
├── agents/
│   ├── research/
│   ├── coding/
│   └── testing/
└── config.yaml
```

---

### 3. LocalAI / LocalAGI

**Purpose:** OpenAI-compatible API for local model inference.

**Repository:** [LocalAI GitHub](https://github.com/mudler/LocalAI)

**Features:**
- Drop-in replacement for OpenAI API
- Multi-model support (LLaMA, Mistral, GPT-J)
- GPU acceleration with CUDA/ROCm
- Function calling support

**Installation (Docker):**
```bash
docker run -p 8080:8080 -v $PWD/models:/models localai/localai:latest
```

**Integration:**
```python
from openai import OpenAI

# Use LocalAI as OpenAI drop-in
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="mistral-7b-instruct",
    messages=[{"role": "user", "content": "Analyze this combat log..."}]
)
```

---

### 4. n8n (Workflow Automation)

**Purpose:** Visual workflow builder for automating task pipelines.

**Repository:** [n8n GitHub](https://github.com/n8n-io/n8n)

**Features:**
- 300+ pre-built integrations
- Custom code execution (Python/JavaScript)
- Webhook triggers
- Scheduled executions

**Installation:**
```bash
npm install -g n8n
n8n start
```

**Workflow Example: Combat Log Analysis**
```json
{
  "nodes": [
    {
      "name": "Watch Combat Logs",
      "type": "n8n-nodes-base.fileSystemTrigger",
      "parameters": {
        "path": "artifacts/combat_logs/",
        "event": "add"
      }
    },
    {
      "name": "Parse Log",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "language": "python",
        "code": "import json\nreturn json.loads(items[0].json.fileContent)"
      }
    },
    {
      "name": "Send to Ollama",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:11434/api/generate",
        "method": "POST",
        "body": {
          "model": "mistral",
          "prompt": "Analyze: {{$json.log}}"
        }
      }
    },
    {
      "name": "Create Linear Issue",
      "type": "n8n-nodes-base.linear",
      "parameters": {
        "operation": "create",
        "title": "Combat inefficiency detected",
        "description": "{{$json.analysis}}"
      }
    }
  ]
}
```

**Integration:**
```python
from core.handoff.workflows.n8n_client import N8NClient

n8n = N8NClient(base_url="http://localhost:5678")

# Trigger workflow via webhook
n8n.trigger_workflow(
    webhook_id="combat-analysis",
    payload={"log_path": "artifacts/combat_logs/session_12345.json"}
)
```

---

### 5. AnythingLLM (Knowledge Base)

**Purpose:** Private, document-based knowledge base with chat interface.

**Repository:** [AnythingLLM GitHub](https://github.com/Mintplex-Labs/anything-llm)

**Features:**
- Multi-document embeddings
- Vector database (ChromaDB, Pinecone)
- Chat with documents
- Multi-workspace support

**Installation (Docker):**
```bash
docker run -d -p 3001:3001 \
  -v $(pwd)/anythingllm:/app/server/storage \
  mintplexlabs/anythingllm
```

**Integration:**
```python
from core.handoff.knowledge.anything_llm import AnythingLLMClient

knowledge = AnythingLLMClient(base_url="http://localhost:3001")

# Create workspace for project
workspace = knowledge.create_workspace(
    name="Wizard101 Combat Research",
    documents=[
        "docs/COMBAT_MECHANICS.md",
        "artifacts/research/spell_analysis.pdf"
    ]
)

# Query knowledge base
answer = knowledge.query(
    workspace_id=workspace.id,
    question="What is the optimal spell rotation for Fire wizards?"
)
```

**Workspace Configuration:**
```yaml
# artifacts/anythingllm/workspaces/wizard101_combat.yaml
name: Wizard101 Combat Research
vectorDB: chroma
embeddingModel: nomic-embed-text
llmModel: mistral-7b-instruct
documents:
  - path: docs/COMBAT_MECHANICS.md
    type: markdown
  - path: artifacts/research/spell_analysis.pdf
    type: pdf
settings:
  chunkSize: 1000
  chunkOverlap: 200
  topK: 5
```

---

### 6. Flowise (Visual LLM Chains)

**Purpose:** No-code LangChain builder with drag-and-drop interface.

**Repository:** [Flowise GitHub](https://github.com/FlowiseAI/Flowise)

**Features:**
- Visual chain builder
- 100+ LangChain integrations
- API generation for chains
- Embeddings & vector stores

**Installation:**
```bash
npm install -g flowise
flowise start
```

**Use Case: Multi-Step Research Agent**
```
[Document Loader] → [Text Splitter] → [Embeddings] → [Vector Store]
                                                            ↓
[User Query] → [Retriever] → [LLM Chain] → [Output Parser]
```

**Integration:**
```python
from core.handoff.workflows.flowise_client import FlowiseClient

flowise = FlowiseClient(base_url="http://localhost:3000")

# Execute pre-built chain
response = flowise.execute_chain(
    chain_id="research-agent-v1",
    inputs={"query": "Analyze recent combat performance trends"}
)
```

---

### 7. Observer AI (Code Analysis)

**Purpose:** AI-powered code understanding and refactoring tool.

**Repository:** [Observer AI](https://github.com/observerai/observer)

**Features:**
- Codebase semantic search
- Dependency mapping
- Automated refactoring suggestions
- Security vulnerability detection

**Installation:**
```bash
pip install observer-ai
observer init --path ./core
```

**Integration:**
```python
from observer import CodeAnalyzer

analyzer = CodeAnalyzer(project_root="core/deimos")

# Analyze code quality
report = analyzer.analyze(
    files=["src/combat_new.py", "src/combat_math.py"],
    checks=["complexity", "duplication", "security"]
)

# Generate refactoring plan
plan = analyzer.suggest_refactoring(
    target="src/combat_new.py",
    goal="reduce_complexity"
)
```

---

### 8. Cline / Aider (Terminal Coding Assistants)

**Purpose:** AI pair programming tools for terminal-based development.

**Cline Repository:** [Cline GitHub](https://github.com/cline/cline)  
**Aider Repository:** [Aider GitHub](https://github.com/paul-gauthier/aider)

**Features:**
- Git-aware code editing
- Multi-file context
- Test generation
- Commit message generation

**Cline Installation:**
```bash
npm install -g @cline/cli
cline --model ollama/mistral
```

**Aider Installation:**
```bash
pip install aider-chat
aider --model ollama/mistral --no-git
```

**Integration Example:**
```bash
# Use aider for targeted refactoring
aider core/deimos/src/combat_new.py \
  --message "Extract spell casting logic into separate class" \
  --model ollama/codellama
```

---

## Model Selection Guide

### Recommended Models by Task

| Task | Model | Size | Hardware | Notes |
|------|-------|------|----------|-------|
| Code Generation | CodeLlama 13B | 7.4 GB | 16GB RAM | Best for Python/C# |
| General Chat | Mistral 7B Instruct | 4.1 GB | 8GB RAM | Fast, accurate |
| Code Review | DeepSeek Coder 33B | 19 GB | 32GB RAM | Excellent for refactoring |
| Research/Writing | Mixtral 8x7B | 26 GB | 48GB RAM | High quality output |
| Embeddings | nomic-embed-text | 274 MB | 4GB RAM | For vector search |

### Hardware Tiers

**Tier 1: Entry (16GB RAM, GTX 1660)**
- Models: Mistral 7B, CodeLlama 7B
- Use Cases: Code completion, simple queries
- Expected Performance: 5-10 tokens/sec

**Tier 2: Enthusiast (32GB RAM, RTX 3060)**
- Models: CodeLlama 13B, Mistral 7B, Mixtral 8x7B (quantized)
- Use Cases: Full development workflow, research
- Expected Performance: 15-25 tokens/sec

**Tier 3: Professional (64GB RAM, RTX 4090)**
- Models: DeepSeek Coder 33B, Mixtral 8x7B, Llama 2 70B (quantized)
- Use Cases: Multi-agent orchestration, real-time analysis
- Expected Performance: 30-50 tokens/sec

---

## Configuration

### Environment Variables

```bash
# .env additions

# ARGO Configuration
ARGO_ENABLED=true
ARGO_MEMORY_PATH=artifacts/argo/memory
ARGO_MAX_ITERATIONS=10

# Clara Configuration
CLARA_ENABLED=true
CLARA_WORKSPACE=artifacts/clara/workspace

# n8n Configuration
N8N_ENABLED=true
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your-n8n-api-key

# AnythingLLM Configuration
ANYTHINGLLM_ENABLED=true
ANYTHINGLLM_BASE_URL=http://localhost:3001
ANYTHINGLLM_WORKSPACE=wizard101-research

# Flowise Configuration
FLOWISE_ENABLED=true
FLOWISE_BASE_URL=http://localhost:3000

# LocalAI Configuration
LOCALAI_ENABLED=false  # Optional if using Ollama
LOCALAI_BASE_URL=http://localhost:8080

# Observer AI Configuration
OBSERVER_ENABLED=true
OBSERVER_PROJECT_ROOT=core/deimos
```

### Pydantic Config Integration

```python
# core/config/manager.py

class LocalAgentsConfig(BaseSettings):
    """Configuration for local agent frameworks."""
    
    # ARGO
    argo_enabled: bool = Field(default=False, alias="ARGO_ENABLED")
    argo_memory_path: str = Field(default="artifacts/argo/memory")
    argo_max_iterations: int = Field(default=10)
    
    # Clara
    clara_enabled: bool = Field(default=False, alias="CLARA_ENABLED")
    clara_workspace: str = Field(default="artifacts/clara/workspace")
    
    # n8n
    n8n_enabled: bool = Field(default=False, alias="N8N_ENABLED")
    n8n_base_url: str = Field(default="http://localhost:5678")
    n8n_api_key: SecretStr = Field(default=SecretStr(""))
    
    # AnythingLLM
    anythingllm_enabled: bool = Field(default=False, alias="ANYTHINGLLM_ENABLED")
    anythingllm_base_url: str = Field(default="http://localhost:3001")
    anythingllm_workspace: str = Field(default="aas-research")
    
    # Flowise
    flowise_enabled: bool = Field(default=False, alias="FLOWISE_ENABLED")
    flowise_base_url: str = Field(default="http://localhost:3000")
    
    # LocalAI (optional alternative to Ollama)
    localai_enabled: bool = Field(default=False, alias="LOCALAI_ENABLED")
    localai_base_url: str = Field(default="http://localhost:8080")
    
    # Observer AI
    observer_enabled: bool = Field(default=False, alias="OBSERVER_ENABLED")
    observer_project_root: str = Field(default="core/deimos")

class AASConfig(BaseSettings):
    # ... existing config ...
    local_agents: LocalAgentsConfig = LocalAgentsConfig()
```

---

## Integration Patterns

### Pattern 1: Task Decomposition with ARGO

```python
from core.handoff.agents.argo_client import ARGOClient
from loguru import logger

async def decompose_and_execute_task(task_id: str, task_description: str):
    """Use ARGO to decompose a complex task into subtasks."""
    
    argo = ARGOClient(
        model_endpoint=config.ollama_endpoint,
        memory_path=config.local_agents.argo_memory_path
    )
    
    # Decompose task
    logger.info(f"Decomposing task {task_id}: {task_description}")
    subtasks = await argo.decompose_task(
        task=task_description,
        constraints={"max_subtasks": 5, "time_limit": "2 hours"}
    )
    
    # Execute each subtask
    results = []
    for subtask in subtasks:
        result = await argo.execute_subtask(subtask)
        results.append(result)
        logger.info(f"Completed subtask: {subtask.title}")
    
    # Synthesize results
    final_result = await argo.synthesize_results(results)
    return final_result
```

### Pattern 2: Document-Augmented Responses (AnythingLLM)

```python
from core.handoff.knowledge.anything_llm import AnythingLLMClient

async def query_with_context(question: str, workspace: str = "wizard101-research"):
    """Query AnythingLLM with project documentation as context."""
    
    knowledge = AnythingLLMClient(
        base_url=config.local_agents.anythingllm_base_url
    )
    
    # Query with retrieval
    response = await knowledge.query(
        workspace_id=workspace,
        question=question,
        mode="query",  # "chat" for conversational, "query" for direct answer
        include_sources=True
    )
    
    return {
        "answer": response.text,
        "sources": response.sources,
        "confidence": response.confidence
    }
```

### Pattern 3: Automated Workflow Triggers (n8n)

```python
from core.handoff.workflows.n8n_client import N8NClient

async def trigger_combat_analysis(log_path: str):
    """Trigger n8n workflow for combat log analysis."""
    
    n8n = N8NClient(
        base_url=config.local_agents.n8n_base_url,
        api_key=config.local_agents.n8n_api_key.get_secret_value()
    )
    
    # Trigger workflow
    result = await n8n.trigger_workflow(
        webhook_id="combat-analysis-v2",
        payload={
            "log_path": log_path,
            "analysis_type": "performance",
            "notify_linear": True
        }
    )
    
    logger.info(f"Triggered workflow: {result.execution_id}")
    return result
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_local_agents.py

import pytest
from core.handoff.agents.argo_client import ARGOClient
from core.handoff.knowledge.anything_llm import AnythingLLMClient

@pytest.mark.asyncio
async def test_argo_task_decomposition():
    """Test ARGO task decomposition."""
    argo = ARGOClient(
        model_endpoint="http://localhost:11434",
        memory_path="artifacts/test/argo"
    )
    
    subtasks = await argo.decompose_task(
        task="Refactor combat system for modularity",
        constraints={"max_subtasks": 3}
    )
    
    assert len(subtasks) <= 3
    assert all(subtask.has_clear_goal for subtask in subtasks)

@pytest.mark.asyncio
async def test_anythingllm_query():
    """Test AnythingLLM knowledge retrieval."""
    knowledge = AnythingLLMClient(base_url="http://localhost:3001")
    
    response = await knowledge.query(
        workspace_id="test-workspace",
        question="What is the project architecture?"
    )
    
    assert response.text is not None
    assert len(response.sources) > 0
```

### Integration Tests

```python
# tests/integration/test_agent_pipeline.py

@pytest.mark.integration
async def test_full_agent_pipeline():
    """Test end-to-end agent pipeline: Task → ARGO → n8n → Linear."""
    
    # 1. ARGO decomposes task
    argo = ARGOClient(...)
    subtasks = await argo.decompose_task("Implement new spell system")
    
    # 2. Execute each subtask
    for subtask in subtasks:
        result = await argo.execute_subtask(subtask)
        
        # 3. Trigger n8n workflow for analysis
        n8n = N8NClient(...)
        analysis = await n8n.trigger_workflow(
            webhook_id="code-quality-check",
            payload={"code": result.code}
        )
        
        # 4. Create Linear issue if issues found
        if analysis.issues_found:
            linear = LinearSync(...)
            await linear.create_issue(
                title=f"Code quality issues in {subtask.title}",
                description=analysis.report
            )
```

---

## Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.local-agents.yml

version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - ./artifacts/n8n:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}

  anythingllm:
    image: mintplexlabs/anythingllm
    ports:
      - "3001:3001"
    volumes:
      - ./artifacts/anythingllm:/app/server/storage
    environment:
      - STORAGE_DIR=/app/server/storage
      - SERVER_PORT=3001

  flowise:
    image: flowiseai/flowise
    ports:
      - "3000:3000"
    volumes:
      - ./artifacts/flowise:/root/.flowise
    environment:
      - PORT=3000
      - FLOWISE_USERNAME=admin
      - FLOWISE_PASSWORD=${FLOWISE_PASSWORD}

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ./artifacts/ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Start Services:**
```bash
docker-compose -f docker-compose.local-agents.yml up -d
```

---

## Security Considerations

### Network Isolation
All local agent services should run on `localhost` only. Use firewall rules to prevent external access:

```bash
# Windows Firewall (PowerShell as Admin)
New-NetFirewallRule -DisplayName "Block n8n External" `
  -Direction Inbound -LocalPort 5678 -Protocol TCP `
  -Action Block -RemoteAddress Internet
```

### Data Privacy
- **No Cloud Transmission:** All data stays on local machine
- **Encrypted Storage:** Use BitLocker/LUKS for artifact directories
- **Model Security:** Download models from official sources only

### API Key Management
```python
# Never log API keys
logger.info(f"N8N configured: {config.local_agents.n8n_enabled}")
# DON'T: logger.info(f"API Key: {config.local_agents.n8n_api_key}")

# Use SecretStr in config
n8n_api_key: SecretStr = Field(default=SecretStr(""))
```

---

## Troubleshooting

### Common Issues

**1. Ollama Model Not Found**
```bash
# List available models
ollama list

# Pull missing model
ollama pull mistral
```

**2. n8n Workflow Fails**
- Check webhook URL is correct: `http://localhost:5678/webhook/<webhook-id>`
- Verify API key in `.env` matches n8n settings
- Check logs: `docker logs n8n`

**3. AnythingLLM Empty Responses**
- Ensure documents are uploaded to workspace
- Check embedding model is downloaded
- Verify vector database (ChromaDB) is initialized

**4. ARGO Memory Persistence**
```python
# Clear corrupted memory
import shutil
shutil.rmtree("artifacts/argo/memory")
os.makedirs("artifacts/argo/memory")
```

---

## Roadmap

### Phase 1: Foundation (Current)
- ✅ Ollama integration (AAS-008)
- 🔄 ARGO client implementation
- 🔄 n8n workflow library
- 🔄 AnythingLLM workspace setup

### Phase 2: Automation
- Clara project templates
- Flowise pre-built chains
- Observer AI code audits
- Aider/Cline integration in dev workflow

### Phase 3: Advanced
- Multi-agent orchestration (ARGO + Clara)
- Real-time workflow triggers
- Knowledge graph (AnythingLLM + Neo4j)
- Hardware optimization (model quantization)

---

## References

- [Ollama Documentation](https://ollama.ai/docs)
- [n8n Workflow Examples](https://n8n.io/workflows)
- [AnythingLLM Setup Guide](https://docs.anythingllm.com/)
- [LangChain Documentation](https://langchain.readthedocs.io/)
- [Local-First AI Principles](https://www.inkandswitch.com/local-first/)

---

**Last Updated:** 2026-01-02  
**Maintainer:** Copilot (AAS-103)
