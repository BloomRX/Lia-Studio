"""Descoberta de modelos em endereço escolhido; não autoriza inferência/Agent.

Chave no cofre do sistema; endereço em JSON local. Sem proxy/redirect; resposta
bruta, segredo e erros do serviço nunca são devolvidos ao browser ou a logs.
"""
from __future__ import annotations
import hashlib
import json
import re
from http.client import HTTPException
from typing import Optional
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler,ProxyHandler,Request,build_opener
from . import combo_canary,combo_policy,credential_store
from .storage import Storage,StorageError

NAME="gateway_connection.json"
MAX_RESPONSE=256*1024
TIMEOUT=3

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl): return None

def _address(address: str) -> str:
    if type(address) is not str or not 1 <= len(address) <= 1024 or address.strip()!=address:
        raise StorageError("endereço inválido")
    try:
        u=urlsplit(address);port=u.port
    except ValueError as exc: raise StorageError("endereço inválido") from exc
    if (u.scheme not in ("http","https") or not u.hostname or u.username or u.password
        or u.path not in ("","/") or u.query or u.fragment
        or (port is not None and not 1<=port<=65535)
        or (u.scheme=="http" and u.hostname not in ("127.0.0.1","::1"))
        or not re.fullmatch(r"https?://[A-Za-z0-9.\-\[\]:]+/?",address)):
        raise StorageError("use HTTPS ou HTTP no loopback, sem caminho/usuário")
    return address.rstrip("/")

def _target(storage:Storage)->str:
    return "Lia Studio/Gateway/"+hashlib.sha256(str(storage.projects_dir.resolve()).encode()).hexdigest()

def _saved(storage:Storage)->str:
    data=storage.read_structured_global(NAME)
    if data=={} and not (storage.projects_dir/NAME).exists(): return ""
    if type(data) is not dict or set(data)!={"address"}: raise StorageError("conexão inválida")
    if data["address"] == "": return ""
    return _address(data["address"])

def _key(storage:Storage,address:str)->Optional[str]:
    raw=credential_store.get(_target(storage))
    if raw is None: return None
    try:
        value=json.loads(raw)
        if type(value) is dict and set(value)=={"address","key"} and value["address"]==address and type(value["key"]) is str:
            return value["key"] or None
    except (ValueError,TypeError): pass
    return None

def public_config(storage:Storage)->dict:
    address=_saved(storage)
    try:
        available=True;has_key=bool(address and _key(storage,address))
    except StorageError:
        available=has_key=False
    return {"address":address,"has_key":has_key,"vault_available":available,"runtime_enabled":False}

def configure(storage:Storage,address:str,key:str,confirmed:bool)->dict:
    if confirmed is not True: raise StorageError("confirme endereço e chave")
    address=_address(address)
    if (type(key) is not str or not 1<=len(key)<=1000
        or any(ord(c)<33 or ord(c)>126 for c in key)):
        raise StorageError("chave inválida")
    with storage.stage_lock:
        # Vínculo no cofre impede enviar chave nova ao endereço antigo se JSON falhar.
        secret=json.dumps({"address":address,"key":key},separators=(",",":"))
        credential_store.put(_target(storage),secret)
        storage.write_structured_global(NAME,{"address":address})
    return public_config(storage)

def revoke(storage:Storage,confirmed:bool)->dict:
    if confirmed is not True: raise StorageError("confirme a revogação da conexão")
    with storage.stage_lock:
        # Revogar segredo antes da configuração: se escrita falhar, nenhuma chave é enviada.
        credential_store.delete(_target(storage))
        storage.write_structured_global(NAME,{"address":""})
    return public_config(storage)

def _fetch(storage:Storage,confirmed:bool)->dict:
    if confirmed is not True: raise StorageError("confirme a consulta opt-in")
    address=_saved(storage)
    if not address: raise StorageError("configure endereço e chave")
    key=_key(storage,address)
    if not key: raise StorageError("chave indisponível ou vinculada a outro endereço")
    request=Request(address+"/v1/models",headers={"Accept":"application/json",
                    "Authorization":"Bearer "+key},method="GET")
    opener=build_opener(ProxyHandler({}),_NoRedirect())
    try:
        with opener.open(request,timeout=TIMEOUT) as reply: raw=reply.read(MAX_RESPONSE+1)
        if len(raw)>MAX_RESPONSE: raise ValueError()
        payload=json.loads(raw.decode("utf-8"))
        if type(payload) is not dict or type(payload.get("data")) is not list or len(payload["data"])>500: raise ValueError()
        return payload
    except (HTTPError,URLError,HTTPException,TimeoutError,OSError,ValueError,UnicodeError,TypeError) as exc:
        raise StorageError("metadados indisponíveis; nenhum modelo aprovado") from exc

def list_models(storage:Storage,confirmed:bool)->dict:
    entries={};ambiguous=set()
    for item in _fetch(storage,confirmed)["data"]:
        if type(item) is not dict or type(item.get("id")) is not str or not combo_policy.ALIAS.fullmatch(item["id"]): continue
        model_id=item["id"]
        if model_id in entries: ambiguous.add(model_id)
        entries[model_id]=item
    result=[]
    for model_id,item in entries.items():
        if model_id in ambiguous: continue
        owner=item.get("owned_by")
        kind="fallback_chain" if owner=="combo" else ("single_model" if type(owner) is str and owner else "unknown")
        result.append({"id":model_id,"kind":kind,"approved":False,"tool_round_trip":"not_tested"})
    return {"models":result,"warning":"Lista declarada: membros, custo e Tools não verificados."}

def inspect(storage:Storage,tier_id:str,confirmed:bool)->Optional[dict]:
    if type(tier_id) is not str or not combo_policy.ALIAS.fullmatch(tier_id):
        raise StorageError("ID inválido")
    # A falta de configuração/consentimento é erro, não equivalência no canário.
    if not confirmed or not _saved(storage): raise StorageError("configure e confirme a consulta")
    try: return combo_canary.normalize(tier_id,_fetch(storage,True))
    except StorageError: return None
