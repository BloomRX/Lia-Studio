"""Contrato Forge V1: inspeção isolada de JSON sem converter o editor 2D."""
import hashlib
import json
import sys
import tempfile
import threading
import unittest
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
                # O editor é textual: exporta exatamente os bytes que passaram no gate.
                self.assertEqual(text.encode("utf-8"), original)

    def test_rejects_modified_unsupported_and_inconsistent_spec(self):
        invalid = []
        s = spec(); s["schemaVersion"] = 2; invalid.append(s)
        s = spec(); s["rig"]["bones"] = ["notARigBone"]; invalid.append(s)
        s = spec(); s["poses"]["active"]["rotations"]["head"] = [0, 0, 0, 0]; invalid.append(s)
        s = spec(); s["timeline"][1]["pose"] = "missing"; invalid.append(s)
        s = spec(); s["timeline"][1]["time"] = 1e-40; invalid.append(s)
        s = spec(); s["mask"] = ["hips"]; invalid.append(s)
        s = spec(); s["tags"]["emotional"].append("invalid tag"); invalid.append(s)
        s = spec(); s["provenance"]["license"] = ""; invalid.append(s)
        s = spec(loop=True); s["timeline"][-1]["pose"] = "active"; invalid.append(s)
        s = spec(); s["unknown"] = True; invalid.append(s)
        for item in invalid:
            with self.subTest(item=str(item)[:100]), self.assertRaises(storage.StorageError):
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
        from app import server
        with tempfile.TemporaryDirectory() as root:
            st = storage.Storage(Path(root))
            with patch.object(server, "storage", st):
                http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
                thread = threading.Thread(target=http.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{http.server_address[1]}"
                def send(body):
                    request = Request(base + "/api/animation/forge-v1/inspect",
                                      method="POST", data=json.dumps(body).encode("utf-8"),
                                      headers={"Content-Type": "application/json"})
                    with urlopen(request, timeout=5) as response:
                        return json.load(response)
                try:
                    text = json.dumps(spec(), ensure_ascii=False) + "\n"
                    result = send({"sourceText": text})
                    self.assertEqual(result["sourceSha256"], hashlib.sha256(text.encode()).hexdigest())
                    with self.assertRaises(HTTPError) as err:
                        send({"spec": spec()})
                    self.assertEqual(err.exception.code, 400)
                    err.exception.close()
                    with self.assertRaises(HTTPError) as err:
                        send({"sourceText": '{"schemaVersion":7}'})
                    self.assertEqual(err.exception.code, 400)
                    err.exception.close()
                    self.assertFalse((st.projects_dir / "_animation_workspace.json").exists())
                finally:
                    http.shutdown()
                    thread.join(timeout=5)
                    http.server_close()

    def test_html_wires_editor_without_claiming_gltf_or_2d_conversion(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "app/static/forge-animation.html").read_text(encoding="utf-8")
        script = (root / "app/static/forge-animation.js").read_text(encoding="utf-8")
        for field in ("forge-file", "forge-source", "forge-check", "forge-export", "forge-status"):
            self.assertIn(f'id="{field}"', html)
        self.assertIn("/api/animation/forge-v1/inspect", script)
        self.assertIn("source.value !== lastVerifiedText", script)
        self.assertIn("não gera clipes ou glTF", html)


if __name__ == "__main__":
    unittest.main()
