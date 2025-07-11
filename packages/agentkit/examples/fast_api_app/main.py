# -*- coding: utf-8 -*-
import os
import logging
import uvicorn
from tortoise import Tortoise

from .app import app, container
from .api import chat, conversations
from yai_nexus_agentkit.llm import LLMConfig, LLMProvider, OpenAIModel
from yai_nexus_agentkit.persistence import TORTOISE_ORM_CONFIG_TEMPLATE

# Load configuration
container.config.from_yaml("config.yml", required=False)
container.config.db.url.from_env(
    "DATABASE_URL", "postgres://postgres:mysecretpassword@localhost:5432/agent_db"
)

# Initialize LLM Factory
llm_factory_instance = container.llm_factory()
default_llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model=OpenAIModel.GPT_3_5_TURBO.value,
    api_key=os.getenv("OPENAI_API_KEY"),
)
llm_factory_instance.register_config("default_openai", default_llm_config)


@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)
    db_config_instance = container.db_config()
    tortoise_config = TORTOISE_ORM_CONFIG_TEMPLATE.copy()
    tortoise_config["connections"]["default"] = db_config_instance.db_url
    try:
        await Tortoise.init(config=tortoise_config)
        if db_config_instance.generate_schemas:
            await Tortoise.generate_schemas()
        logging.info("Database connection established and schemas generated.")
    except Exception as e:
        logging.error(f"Could not connect to database: {e}")
        logging.warning("Database features will be unavailable.")

    checkpoint_repo_instance = container.checkpoint_repository()
    await checkpoint_repo_instance.setup()


@app.on_event("shutdown")
async def shutdown_event():
    checkpoint_repo_instance = container.checkpoint_repository()
    await checkpoint_repo_instance.cleanup()
    await Tortoise.close_connections()


# Include API routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(
    conversations.router, prefix="/conversations", tags=["Conversations"]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
