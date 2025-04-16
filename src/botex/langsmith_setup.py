import os
from langsmith.run_helpers import traceable
import litellm

# Get LangSmith config from environment
os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGSMITH_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGSMITH_API_KEY"] = os.environ.get("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "pr-frosty-analogue-50")

# Create a traceable completion function
@traceable(run_type="llm")
def traced_completion(**kwargs):
    return litellm.completion(**kwargs)
