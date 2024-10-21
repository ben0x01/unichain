import json
import asyncio
import random

from pathlib import Path
from web3 import Web3
from web3.exceptions import TransactionNotFound

abi_path = Path(__file__).parent.parent / 'Abi' / 'swap_abi.json'

class Unichain:
    def __init__(self, private_key, rpc, explorer):
        self.private_key = private_key
        self.rpc = rpc
        self.explorer = explorer
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.wallet = self.w3.eth.account.from_key(private_key)
        self.contract_address = Web3.to_checksum_address("0xea58fcA6849d79EAd1f26608855c2D6407d54Ce2")
        with open(abi_path) as abi_file:
            self.abi = json.load(abi_file)
        self.contract = self.w3.eth.contract(abi=self.abi, address=self.contract_address)

    def get_random_value_withdraw(self):
        balance = self.w3.eth.get_balance(self.wallet.address)
        balance_in_ether = float(self.w3.from_wei(balance, 'ether'))
        print("Баланс на кошельке -", balance_in_ether)
        random_value = random.uniform(0, balance_in_ether / 8)
        return self.w3.to_wei(random_value, 'ether')

    async def is_transaction_successful(self, tx_hash: hex, max_attempts: int = 10, delay: int = 30) -> bool:
        attempts = 0
        while attempts < max_attempts:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)

                if receipt:
                    if receipt['status'] == 1:
                        print(f'Transaction {tx_hash} was successful.')
                        return True
                    else:
                        print(f'Transaction {tx_hash} failed.')
                        return False

            except TransactionNotFound:
                print(f"Transaction with hash {tx_hash} not found. Attempt {attempts + 1} of {max_attempts}...")

            await asyncio.sleep(delay)
            attempts += 1

        print(f"Transaction {tx_hash} still pending after {max_attempts * delay} seconds.")
        return False

    async def swap(self):
        nonce = self.w3.eth.get_transaction_count(self.wallet.address)

        base_fee = self.w3.eth.gas_price
        max_priority_fee_per_gas = self.w3.eth.max_priority_fee
        max_fee_per_gas = base_fee + max_priority_fee_per_gas
        max_fee_per_gas_increased = int(max_fee_per_gas * 2)

        amount_to_send = self.get_random_value_withdraw()

        chain_id = self.w3.eth.chain_id

        tx = self.contract.functions.bridgeETHTo(self.wallet.address, 200000, "0x6272696467670a").build_transaction({
            "from": self.wallet.address,
            "value": amount_to_send,
            "nonce": nonce,
            "maxFeePerGas": max_fee_per_gas_increased,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "chainId": chain_id
        })

        estimated_gas = self.w3.eth.estimate_gas(tx)
        tx['gas'] = estimated_gas

        signed_approve_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if await self.is_transaction_successful(tx_hash):
            print(f'Transaction hash: {self.explorer}0x{tx_hash.hex()}')
