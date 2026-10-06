"""Optional offline integration test: MIHOMO_BIN=/path/to/mihomo python -m unittest discover -s tests -v."""
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request

import yaml

from test_override import (
    CONFIG, HONG_KONG, MISCLASSIFIED_SAMPLES, NOTICE_SAMPLES, OTHER_SAMPLES,
    REGION_IDENTIFIERS, REGION_SAMPLES, UNKNOWN_SAMPLES, accepts,
)


def nodes(names):
    return [dict(name=name, type="http", server="127.0.0.1", port=9) for name in names]


@unittest.skipUnless(os.environ.get("MIHOMO_BIN"), "Set MIHOMO_BIN for offline core checks")
class MihomoRuntimeTests(unittest.TestCase):
    def test_candidates_and_empty_fallback(self):
        config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        groups = {g["name"]: g for g in config["proxy-groups"]}
        identifiers = tuple(n for names in REGION_IDENTIFIERS.values() for n in names)
        names = list(dict.fromkeys(
            HONG_KONG + REGION_SAMPLES + OTHER_SAMPLES + identifiers
            + MISCLASSIFIED_SAMPLES + NOTICE_SAMPLES + UNKNOWN_SAMPLES
        ))
        direct = {"name": "自定义直连", "type": "direct"}
        scenarios = (
            ("mixed", nodes(names) + [direct], []),
            ("provider_only", [], nodes(names) + [direct]),
            ("mixed_sources", nodes(HONG_KONG), nodes(OTHER_SAMPLES) + [direct]),
            ("hk_only", nodes(HONG_KONG), []),
            ("hk_provider_only", [], nodes(HONG_KONG)),
            ("direct_only", [direct], []),
            ("notices_only", nodes(NOTICE_SAMPLES), []),
            ("notices_provider_only", [], nodes(NOTICE_SAMPLES)),
            ("unknown_only", nodes(UNKNOWN_SAMPLES), []),
            ("empty", [], []),
        )
        for label, static_nodes, provider_nodes in scenarios:
            with self.subTest(scenario=label):
                proxies = self.run_core(config, static_nodes, provider_nodes)
                for name, group in groups.items():
                    if not group.get("include-all"):
                        continue
                    expected = {
                        n["name"] for n in static_nodes + provider_nodes
                        if accepts(group, n["name"], n["type"])
                    } | set(group.get("proxies", []))
                    if not expected:
                        expected = {groups[name].get("empty-fallback", "COMPATIBLE")}
                    self.assertEqual(set(proxies[name]["all"]), expected, name)
                    self.assertTrue(set(NOTICE_SAMPLES).isdisjoint(expected))

    def run_core(self, template, static_nodes, provider_nodes):
        config = copy.deepcopy(template)
        config["proxies"] = static_nodes
        if provider_nodes:
            config["proxy-providers"] = {
                "test-inline": {"type": "inline", "payload": provider_nodes}
            }
        # No subscription credentials, external rule downloads, GeoIP, or remote probes.
        for provider in config["rule-providers"].values():
            behavior = provider["behavior"]
            payload = {
                "classical": "DOMAIN,example.invalid",
                "domain": "example.invalid",
                "ipcidr": "192.0.2.0/24",
            }[behavior]
            provider.clear()
            provider.update(type="inline", behavior=behavior, payload=[payload])
        config["rules"] = [r for r in config["rules"] if not r.startswith("GEOIP,")]
        for group in config["proxy-groups"]:
            group["url"] = "http://127.0.0.1:9/health"
        config.update({
            "mixed-port": 0,
            "allow-lan": False,
            "log-level": "warning",
            "dns": {"enable": False},
            "tun": {"enable": False},
        })
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        config["external-controller"] = f"127.0.0.1:{port}"
        core = str(Path(os.environ["MIHOMO_BIN"]).resolve())
        with tempfile.TemporaryDirectory(prefix="override-test-") as tmp:
            path = Path(tmp) / "config.yaml"
            path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
            command = [core, "-d", tmp, "-f", str(path)]
            check = subprocess.run(command + ["-t"], capture_output=True, text=True, timeout=10)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            with (Path(tmp) / "core.log").open("w+") as log:
                process = subprocess.Popen(command, stdout=log, stderr=log)
                try:
                    client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            break
                        try:
                            with client.open(f"http://127.0.0.1:{port}/proxies", timeout=1) as response:
                                proxies = json.load(response)["proxies"]
                            # The controller can respond before the configuration is applied.
                            if {"♻️ 自动选择", "🌐 其他节点", "💬 OpenAi"} <= proxies.keys():
                                return proxies
                        except OSError:
                            pass
                        time.sleep(0.1)
                    log.seek(0)
                    self.fail("Core API did not become ready: " + log.read())
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
