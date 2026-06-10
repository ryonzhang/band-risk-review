"""
band_connect_test.py — fail-fast: prove ONE agent connects to Band before
wiring all four. Run after creating at least the 'data' agent in Band.

    uv run python band_connect_test.py

Success prints "Connected as: <name>". If this works, the API + credentials
are good and band_agents.py will work the same way.
"""
import asyncio, logging, os
from dotenv import load_dotenv
from thenvoi import Agent
from thenvoi.adapters import AnthropicAdapter      # confirm name in docs
from thenvoi.config import load_agent_config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def main():
    load_dotenv()
    agent_id, api_key = load_agent_config("data")   # uses the 'data' block in agent_config.yaml
    adapter = AnthropicAdapter(model="claude-sonnet-4-6",
                               system_prompt="You are a connection test agent.")
    agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key)
    await agent.start()                              # validates the connection
    log.info(f"Connected as: {getattr(agent, 'agent_name', agent_id)}")
    log.info("Band connection verified.")
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
# end of band_connect_test.py
