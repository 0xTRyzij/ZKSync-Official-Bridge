import json


def load_abi(name: str) -> str:
    with open(f'./assets/abi/{name}.json') as f:
        abi: str = json.load(f)
    return abi


with open('wallets.txt', 'r', encoding='utf-8-sig') as file:
    private_keys = [line.strip() for line in file]
