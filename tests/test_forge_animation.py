"""Contrato Forge V1: inspeção isolada de JSON sem converter o editor 2D."""
import hashlib
import json
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.lia import forge_animation, storage


def spec(asset_id="saudacao", loop=False):
    return {
        "schemaVersion": 1, "id": asset_id, "version": "1.0.0", "duration": 1.6,
        "rig": {"profile": "humanoid", "bones": ["head"]},
        "poses": {
            "neutral": {"rotations": {"head": [0, 0, 0, 1]}, "expressions": {"happy": 0}},
            "active": {"rotations": {"head": [0, 0, .165047606, .986285602]}, "expressions": {"happy": .5}},
        },
        "timeline": [{"time": 0, "pose": "neutral", "intensity": 1},
                     {"time": .8, "pose": "active", "intensity": 1},
                     {"time": 1.6, "pose": "neutral", "intensity": 1}],
        "interpolation": "linear",
        "transition": {"inSeconds": .1, "outSeconds": .1},
        "loop": loop, "mask": ["head"],
        "tags": {"emotional": ["happy"], "behavioral": ["greeting"]},
        "provenance": {"author": "Fixture sintética", "source": "Arquivo autoral de teste", "license": "CC0"},
    }


@contextmanager
def serve_forge_inspection(bind="127.0.0.1"):
    from app import server
    with tempfile.TemporaryDirectory() as root:
        st = storage.Storage(Path(root))
        with patch.object(server, "storage", st):
            http = ThreadingHTTPServer((bind, 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            try:
                yield f"http://127.0.0.1:{http.server_port}/api/animation/forge-v1/inspect", st
            finally:
                http.shutdown()
                thread.join(timeout=5)
                http.server_close()


def post(url, source, content_type=forge_animation.SPEC_MEDIA_TYPE, **headers):
    request = Request(url, method="POST", data=source,
                      headers={"Content-Type": content_type, **headers})
    with urlopen(request, timeout=5) as response:
        return json.load(response)


class TestForgeV1Workspace(unittest.TestCase):
    def test_five_synthetic_specs_roundtrip_as_utf8_text(self):
        for asset_id in ("saudacao", "concordancia", "negacao", "curiosidade", "ocioso"):
            with self.subTest(asset_id=asset_id):
                text = json.dumps(spec(asset_id, loop=asset_id == "ocioso"),
                                  ensure_ascii=False, indent=2) + "\n"
                original = text.encode("utf-8")
                inspected = forge_animation.inspect_source(text)
                self.assertEqual(inspected["id"], asset_id)
                self.assertEqual(inspected["version"], "1.0.0")
                self.assertEqual(inspected["sourceSha256"], hashlib.sha256(original).hexdigest())
                self.assertEqual(inspected["boneTracks"], 1)
                self.assertEqual(inspected["expressions"], 1)
                self.assertEqual(inspected["validatedBy"], "studio-structural-check-only")

    def test_five_actual_forge_reference_specs(self):
        """Cross-repository contract gate: original files from the Forge V1 commit."""
        root = Path(__file__).resolve().parents[1]
        fixture_dir = root / "tests/fixtures/forge-v1-official"
        names = ("concordancia", "curiosidade", "negacao", "ocioso", "saudacao")
        for name in names:
            with self.subTest(name=name):
                source = (fixture_dir / (name + ".json")).read_bytes()
                document = source.decode("utf-8")
                parsed = json.loads(document)
                result = forge_animation.inspect_source(document)
                self.assertEqual(result["id"], name)
                self.assertEqual(result["version"], parsed["version"])
                self.assertEqual(result["duration"], parsed["duration"])
                self.assertEqual(result["rigProfile"], parsed["rig"]["profile"])
                self.assertEqual(result["beats"], len(parsed["timeline"]))
                self.assertEqual(result["sourceSha256"], hashlib.sha256(source).hexdigest())
                self.assertEqual(result["interoperability"], "forge-spec-v1-text")

    def test_rejects_modified_unsupported_and_inconsistent_spec(self):
        invalid = []
        s = spec(); s["schemaVersion"] = 2; invalid.append(s)
        s = spec(); s["rig"]["bones"] = ["notARigBone"]; invalid.append(s)
        s = spec(); s["poses"]["active"]["rotations"]["head"] = [0, 0, 0, 0]; invalid.append(s)
        s = spec(); s["timeline"][1]["pose"] = "missing"; invalid.append(s)
        s = spec(); s["timeline"][1]["time"] = 1e-50; invalid.append(s)
        s = spec(); s["mask"] = ["hips"]; invalid.append(s)
        s = spec(); s["tags"]["emotional"].append("invalid tag"); invalid.append(s)
        s = spec(); s["provenance"]["license"] = ""; invalid.append(s)
        s = spec(loop=True); s["timeline"][-1]["pose"] = "active"; invalid.append(s)
        s = spec(); s["unknown"] = True; invalid.append(s)
        for index, item in enumerate(invalid):
            with self.subTest(case=index, item=str(item)[:150]), self.assertRaises(storage.StorageError):
                forge_animation.inspect_source(json.dumps(item))
        with self.assertRaisesRegex(storage.StorageError, "duplicado"):
            forge_animation.inspect_source('{"id":"um","id":"dois"}')
        with self.assertRaises(storage.StorageError):
            forge_animation.inspect_source(json.dumps(spec()) + "x")
        with self.assertRaises(storage.StorageError):
            forge_animation.inspect_source(" " * (forge_animation.MAX_BYTES + 1))
        with self.assertRaises(storage.StorageError):
            forge_animation.inspect_source(json.dumps({**spec(), "duration": float("nan")}))

    def test_http_is_local_and_does_not_change_2d_workspace(self):
        with serve_forge_inspection() as (url, st):
            text = json.dumps(spec(), ensure_ascii=False) + "\n"
            result = post(url, json.dumps({"sourceText": text}).encode(), "application/json")
            self.assertEqual(result["sourceSha256"], hashlib.sha256(text.encode()).hexdigest())
            for body in ({"spec": spec()}, {"sourceText": '{"schemaVersion":7}'}, {"sourceText": "\ud800"}):
                with self.assertRaises(HTTPError) as err:
                    post(url, json.dumps(body).encode(), "application/json")
                self.assertEqual(err.exception.code, 400)
                err.exception.close()
            self.assertFalse((st.projects_dir / "_animation_workspace.json").exists())

    def test_http_hashes_exact_unicode_bytes_with_lf_and_crlf(self):
        motion = spec()
        motion["provenance"]["author"] = "João 🐱"
        lf = json.dumps(motion, ensure_ascii=False, indent=2).encode() + b"\n"
        with serve_forge_inspection() as (url, st):
            for raw in (lf, lf.replace(b"\n", b"\r\n")):
                with self.subTest(line_ending=raw[-2:]):
                    self.assertEqual(post(url, raw)["sourceSha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse((st.projects_dir / "_animation_workspace.json").exists())

    def test_raw_http_limit_applies_to_spec_bytes_without_json_escaping(self):
        text = json.dumps(spec(), ensure_ascii=False).encode()
        limit = forge_animation.MAX_BYTES
        at_limit = text.ljust(limit, b"\n")
        for raw in (text.ljust(2 * 1024 * 1024 + 1, b"\n"), at_limit):
            self.assertEqual(forge_animation.inspect_bytes(raw)["sourceSha256"], hashlib.sha256(raw).hexdigest())
        with self.assertRaisesRegex(storage.StorageError, "4 MiB"):
            forge_animation.inspect_bytes(at_limit + b" ")
        with serve_forge_inspection() as (url, _):
            self.assertEqual(post(url, at_limit)["sourceSha256"], hashlib.sha256(at_limit).hexdigest())
            # O servidor deve recusar o tamanho anunciado antes de ler o corpo.
            with self.assertRaises(HTTPError) as err:
                post(url, b"", **{"Content-Length": str(limit + 1)})
            self.assertEqual(err.exception.code, 413)
            err.exception.close()

    def test_raw_http_rejects_invalid_encoding_json_and_excessive_depth(self):
        text = json.dumps(spec()).encode()
        huge_duration = text.replace(b'"duration": 1.6', b'"duration": ' + b"9" * 500)
        with serve_forge_inspection() as (url, _):
            for raw in (b"", b"\xff", b"\xef\xbb\xbf" + text, text + b"x", b"[" * 2000, huge_duration):
                with self.subTest(prefix=raw[:10]), self.assertRaises(HTTPError) as err:
                    post(url, raw)
                self.assertEqual(err.exception.code, 400)
                err.exception.close()
            with self.assertRaises(HTTPError) as err:
                post(url, b'{"sourceText":' + b"[" * 2000, "application/json")
            self.assertEqual(err.exception.code, 400)
            err.exception.close()

    def test_raw_http_preserves_host_origin_and_loopback_restrictions(self):
        text = json.dumps(spec()).encode()
        with serve_forge_inspection() as (url, _):
            for headers in ({"Host": "external.invalid"}, {"Origin": "https://external.invalid"}):
                with self.assertRaises(HTTPError) as err:
                    post(url, text, **headers)
                self.assertEqual(err.exception.code, 403)
                err.exception.close()
        with serve_forge_inspection(bind="0.0.0.0") as (url, _), self.assertRaises(HTTPError) as err:
            post(url, text)
        self.assertEqual(err.exception.code, 403)
        err.exception.close()

    def test_html_wires_editor_without_claiming_gltf_or_2d_conversion(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "app/static/forge-animation.html").read_text(encoding="utf-8")
        script = (root / "app/static/forge-animation.js").read_text(encoding="utf-8")
        for field in ("forge-file", "forge-source", "forge-check", "forge-export", "forge-status"):
            self.assertIn(f'id="{field}"', html)
        self.assertIn("/api/animation/forge-v1/inspect", script)
        self.assertIn("source.value !== verified.snapshot", script)
        self.assertIn("nem gera clipes ou glTF", html)


if __name__ == "__main__":
    unittest.main()
