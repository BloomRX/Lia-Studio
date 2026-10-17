"""Lia Studio — núcleo da aplicação (engine-agnostic, local-first, stdlib only).

Este pacote implementa a lógica de domínio da Lia Studio sem nenhuma dependência
de terceiros e sem acoplar a nenhuma engine ou provedor de IA. Toda persistência é
local (arquivos no computador do Dev). Provedores de IA e engines são tratados por
adaptadores claramente marcados; nada é conectado nem pago por padrão.
"""

from . import storage
from . import templates_loader
from . import bootstrap
from . import planning
from . import providers
from . import execution
from . import qa
from . import release
from . import conflicts
from . import decisions
from . import stages
from . import skills
from . import handoff
from . import evidence
from . import sessions
from . import attempt_history
from . import vertical_slice
from . import validation_sessions
from . import code_drafts
from . import runtime_policy
from . import engine_probe

__all__ = [
    "storage",
    "templates_loader",
    "bootstrap",
    "planning",
    "providers",
    "execution",
    "qa",
    "release",
    "conflicts",
    "decisions",
    "stages",
    "skills",
    "handoff",
    "evidence",
    "sessions",
    "attempt_history",
    "vertical_slice",
    "validation_sessions",
    "code_drafts",
    "runtime_policy",
    "engine_probe",
]
