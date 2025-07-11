# YAI Nexus AgentKit

A Python toolkit for building AI applications with multi-LLM support and extensible architecture.

## Installation

```bash
pip install -e ".[all]"
```

## Usage

```python
from yai_nexus_agentkit import create_llm, OpenAIModel

config = {
    "provider": "openai",
    "model": OpenAIModel.GPT_4O.value,
    "api_key": "sk-..."
}
llm = create_llm(config)
response = llm.invoke("Hello, world!")
```

For more details, see the main project documentation.