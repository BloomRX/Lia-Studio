"""IDs de versões anteriores aceitos sem transportar nomes de fornecedores à UI.

Hashes SHA-256 dos IDs antigos são marcadores de compatibilidade, não segredos.
A conversão em memória não concede permissões adicionais nem chama serviços.
"""
import hashlib

_IDS = {
    "a080aa301b3399439331d5cd3d9b623ba6e23bf3fea75066593d6f9d2c850f87": "local-model",
    "2fc71628b5a1cc33119d0ba9bf7d944b54bc846148a19df98c39721324f368c6": "cloud-route",
    "14b29c7fea0b8408a49af5bd6b0d4dbde6e746017c7d3b609c1160a76415bf29": "cloud-route",
    "9ac33a376a29fb0ab9d14b1f84bcee1fc36392996db961d19ab071f67aede99c": "model.local.infer",
    "b5ae680443039621336d4ecbb5886c7d61c2afa990ac15d9f9084a9db3bc5ef0": "lia.local.infer",
    "8e992d67c11d6bfa5c087aaa47f730e774e5328aec00b908c1dccb3b2637509f": "local-model-draft",
    "c0a1a1d384d47c03d412039911cf365e088a4a92587423bbfd26f0d3366b4571": "local-model-draft-job",
}

def canonical(value: str) -> str:
    if type(value) is not str: return value
    return _IDS.get(hashlib.sha256(value.encode()).hexdigest(), value)
