import asyncio

from web3 import Web3

from utils.data.helper import load_abi, private_keys
from utils.data.contracts import (
    contracts,
    abi_names,
)
from config import *


class ContractInteractor:
    def __init__(self, web3, contract_address, amount_to, gwei_threshold):
        self.web3 = web3
        self.contract_address = web3.to_checksum_address(contract_address)
        self.zksync_contract = web3.eth.contract(address=self.contract_address, abi=load_abi(abi_names['eth']))
        self.amount = web3.to_wei(amount_to, 'ether')
        self.gwei_threshold = gwei_threshold

    def build_transaction(self, wallet_address, private_key):
        contract_address_l2 = wallet_address
        l2_value = self.amount
        calldata = b''
        l2_gas_limit = 733664
        l2_gas_per_pubdata_byte_limit = 800
        factory_deps = []
        refund_recipient = wallet_address

        function_call = self.zksync_contract.functions.requestL2Transaction(
            contract_address_l2,
            l2_value,
            calldata,
            l2_gas_limit,
            l2_gas_per_pubdata_byte_limit,
            factory_deps,
            refund_recipient
        )

        transaction_data = function_call.build_transaction({
            'from': wallet_address,
            'gas': 150096,
            'gasPrice': self.web3.to_wei(GWEI, 'gwei'),
            'nonce': self.web3.eth.get_transaction_count(wallet_address),
        })

        signed_transaction = self.web3.eth.account.sign_transaction(transaction_data, private_key)
        return signed_transaction.rawTransaction

    async def interact_with_contract(self, wallet_address, private_key):
        raw_transaction = self.build_transaction(wallet_address, private_key)
        txn = self.web3.eth.send_raw_transaction(raw_transaction)
        print(f"Success | TX: https://etherscan.io/tx/{txn}")


class MainApp:
    def __init__(self, web3, private_keys, gwei_threshold):
        self.web3 = web3
        self.private_keys = private_keys
        self.gwei_threshold = gwei_threshold
        self.contract_interactor = ContractInteractor(web3, contracts['eth'][0], amount_to, gwei_threshold)

    async def main(self):
        accounts = {}
        for key in self.private_keys:
            account = self.web3.eth.account.from_key(key)
            wallet_address = account.address
            accounts[account] = wallet_address

        while True:
            gas_price = self.web3.eth.gas_price
            gwei_gas_price = self.web3.from_wei(gas_price, 'gwei')

            if gwei_gas_price < self.gwei_threshold:
                tasks = [self.contract_interactor.interact_with_contract(accounts[account], key) for account, key in
                         accounts.items()]
                await asyncio.gather(*tasks)

            await asyncio.sleep(5)


if __name__ == "__main__":
    web3_instance = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
    app = MainApp(web3_instance, private_keys, GWEI)
    asyncio.run(app.main())
