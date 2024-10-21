import asyncio
import random
import time

from src.unichain import Unichain
from src.constants import EXPLORER_URL, RPC


def load_private_keys(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


async def execute_transactions():
    private_keys = load_private_keys('private_keys.txt')

    for private_key in private_keys:
        print(f"Starting transaction with private key: {private_key}")

        unichain = Unichain(private_key, RPC, EXPLORER_URL)

        await unichain.swap()

        pause_duration = random.uniform(15, 35)
        print(f"Pausing for {pause_duration:.2f} seconds before the next transaction.")
        time.sleep(pause_duration)


async def main():
    await execute_transactions()


if __name__ == "__main__":
    asyncio.run(main())
