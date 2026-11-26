"""Inspeção e edição textual do contrato de animação Forge V1.

Não substitui composeMotion (Node/Zod), não exporta glTF e não aprova direitos.
Não abre arquivos do servidor nem altera o editor 2D privado do Studio.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from typing import Any

from .storage import StorageError

MAX_BYTES = 2 * 1024 * 1024
BONES = set(("hips spine chest upperChest neck head leftEye rightEye jaw "
             "leftShoulder rightShoulder leftUpperArm rightUpperArm leftLowerArm rightLowerArm leftHand rightHand "
             "leftUpperLeg rightUpperLeg leftLowerLeg rightLowerLeg leftFoot rightFoot leftToes rightToes").split())
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
IDENTITY = (0.0, 0.0, 0.0, 1.0)


def _fail(message: str) -> None:
    raise StorageError("Especificação Forge V1 inválida: " + message)


def _keys(value: Any, fields: set[str], context: str, optional: set[str] = frozenset()) -> None:
    if type(value) is not dict or set(value) - fields or fields - optional - set(value):
        _fail(context + ": estrutura ou campos incompatíveis")


def _name(value: Any) -> bool:
    return type(value) is str and bool(NAME.fullmatch(value))


def _number(value: Any, lo: float, hi: float, positive: bool = False) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and lo <= value <= hi and (not positive or value > 0)


def _rotation(value: Any) -> bool:
    return (type(value) is list and len(value) == 4 and
            all(_number(x, -1, 1) for x in value) and
            abs(math.hypot(*value) - 1) <= 1e-5)


def _float32(value: float) -> float:
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, ValueError):
        _fail("tempo não representável em float32")


def _slerp_from_identity(quaternion: list, intensity: float) -> list:
    # Mesmo SLERP a partir da identidade que o compositor do Forge usa.
    dot = max(-1.0, min(1.0, quaternion[3]))
    target = [-v for v in quaternion] if dot < 0 else quaternion
    angle = math.acos(abs(dot))
    if angle < 1e-6:
        values = [(1 - intensity) * a + intensity * b
                  for a, b in zip(IDENTITY, target)]
    else:
        weight_a = math.sin((1 - intensity) * angle) / math.sin(angle)
        weight_b = math.sin(intensity * angle) / math.sin(angle)
        values = [weight_a * a + weight_b * b
                  for a, b in zip(IDENTITY, target)]
    length = math.hypot(*values)
    return [x / length for x in values]


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("campo JSON duplicado: " + key)
        result[key] = value
    return result


def inspect_source(source_text: Any) -> dict:
    """Valida o recorte de contrato V1 e retorna o hash dos bytes originais."""
    if type(source_text) is not str or not source_text:
        _fail("texto JSON obrigatório")
    raw = source_text.encode("utf-8")
    if len(raw) > MAX_BYTES:
        _fail("arquivo supera 2 MB")
    try:
        spec = json.loads(source_text, object_pairs_hook=_unique_pairs,
                          parse_constant=lambda x: _fail("constante JSON proibida: " + x))
    except (ValueError, UnicodeError) as exc:
        _fail("JSON ilegível: " + str(exc))
    _keys(spec, {"schemaVersion", "id", "version", "duration", "rig", "poses", "timeline",
                 "interpolation", "transition", "loop", "tags", "provenance", "mask"},
          "raiz", {"mask"})
    if type(spec["schemaVersion"]) is not int or spec["schemaVersion"] != 1:
        _fail("schemaVersion deve ser 1")
    if not _name(spec["id"]) or type(spec["version"]) is not str or not VERSION.fullmatch(spec["version"]):
        _fail("id ou version inválidos")
    duration = spec["duration"]
    if not _number(duration, 0, 3600, positive=True):
        _fail("duration fora de 0-3600 segundos")
    _keys(spec["rig"], {"profile", "bones"}, "rig")
    rig = spec["rig"]
    if not _name(rig["profile"]) or type(rig["bones"]) is not list or not rig["bones"] or (
        any(type(b) is not str or b not in BONES for b in rig["bones"]) or
        len(set(rig["bones"])) != len(rig["bones"])
    ):
        _fail("ossos do rig inválidos")
    bones = set(rig["bones"])
    mask = spec.get("mask", rig["bones"])
    if type(mask) is not list or len(set(map(str, mask))) != len(mask) or any(
        type(b) is not str or b not in bones for b in mask
    ):
        _fail("mask incompatível")
    poses = spec["poses"]
    if type(poses) is not dict:
        _fail("poses devem ser um objeto")
    for name, pose in poses.items():
        if not _name(name):
            _fail("nome de pose inválido")
        _keys(pose, {"rotations", "expressions"}, "pose")
        if type(pose["rotations"]) is not dict or type(pose["expressions"]) is not dict:
            _fail("canais da pose inválidos")
        if any(b not in bones or not _rotation(q) for b, q in pose["rotations"].items()):
            _fail("rotação ou osso inválido")
        if any(not _name(e) or not _number(w, 0, 1) for e, w in pose["expressions"].items()):
            _fail("expressão inválida")
    beats = spec["timeline"]
    if type(beats) is not list or not 2 <= len(beats) <= 10000:
        _fail("timeline deve ter entre 2 e 10000 beats")
    previous = -1.0
    for idx, beat in enumerate(beats):
        _keys(beat, {"time", "pose", "intensity"}, "beat")
        time = beat["time"]
        if not _number(time, 0, 3600) or not _number(beat["intensity"], 0, 1) or (
            type(beat["pose"]) is not str or beat["pose"] not in poses
        ):
            _fail("beat inválido")
        rounded = _float32(time)
        if rounded <= previous:
            _fail("tempos da timeline não são crescentes em float32")
        previous = rounded
    if beats[0]["time"] != 0 or beats[-1]["time"] != duration:
        _fail("timeline deve começar em 0 e terminar em duration")
    if spec["interpolation"] not in ("linear", "step") or type(spec["loop"]) is not bool:
        _fail("interpolação ou loop inválido")
    _keys(spec["transition"], {"inSeconds", "outSeconds"}, "transition")
    if any(not _number(value, 0, 3600) for value in spec["transition"].values()) or (
        sum(spec["transition"].values()) > duration
    ):
        _fail("transições excedem a duração")
    _keys(spec["tags"], {"emotional", "behavioral"}, "tags")
    for values in spec["tags"].values():
        if type(values) is not list or any(not _name(value) for value in values):
            _fail("tags inválidas")
    _keys(spec["provenance"], {"author", "source", "license"}, "provenance")
    for value in spec["provenance"].values():
        if type(value) is not str or not 1 <= len(value.strip()) <= 300:
            _fail("proveniência obrigatória e limitada")
    used = [poses[beat["pose"]] for beat in beats]
    tracks = [b for b in mask if any(b in p["rotations"] for p in used)]
    expressions = {e for pose in used for e in pose["expressions"]}
    if not tracks and not expressions:
        _fail("clipe sem canais")
    if spec["loop"]:
        first, last = beats[0], beats[-1]
        a, b = poses[first["pose"]], poses[last["pose"]]
        for bone in tracks:
            q1 = _slerp_from_identity(a["rotations"].get(bone, list(IDENTITY)), first["intensity"])
            q2 = _slerp_from_identity(b["rotations"].get(bone, list(IDENTITY)), last["intensity"])
            if abs(sum(x*y for x, y in zip(q1, q2))) < 1 - 1e-6:
                _fail("loop não fecha a pose")
        for expression in expressions:
            v1 = a["expressions"].get(expression, 0) * first["intensity"]
            v2 = b["expressions"].get(expression, 0) * last["intensity"]
            if abs(v1 - v2) > 1e-6:
                _fail("loop não fecha a expressão")
    return {
        "schemaVersion": 1, "id": spec["id"], "version": spec["version"],
        "duration": duration, "rigProfile": rig["profile"], "boneTracks": len(tracks),
        "expressions": len(expressions), "beats": len(beats),
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "interoperability": "forge-spec-v1-text",
        "validatedBy": "studio-structural-check-only",
        "notice": ("Revisão estrutural local. Reexecute o compositor e o empacotador oficiais "
                   "do Forge após editar; nenhum glTF, direitos ou rig real foi validado."),
    }
