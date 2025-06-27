# chat_cli.py
"""
Interactive CLI for the YAML calendar bot.

Run:  python -m asyncio chat_cli.py
Requires:
    pip install openai openai-agents-python pyyaml python-dotenv
"""

import asyncio, datetime as dt
from dotenv import load_dotenv
from agents import Runner
from calendar_bot import scheduler  # <- your Agent with tools & YAML helpers

# Load environment variables from .env file
load_dotenv()

async def chat() -> None:
    conversation = []                          # full history for this session
    print("Calendar-Bot ready.  Type 'quit' to exit.\n")

    while True:
        user_input = input("You ► ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break

        # append the new user turn
        conversation.append({"role": "user", "content": user_input})

        # run the agent with full history
        result = await Runner.run(scheduler, conversation)

        # append assistant (and any tool calls) back into history
        conversation = result.to_input_list()

        # show assistant's latest reply
        print(f"\nBot ► {result.final_output}\n")

if __name__ == "__main__":
    asyncio.run(chat())
