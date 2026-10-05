"""Static checks for the Clash Party override (no subscription credentials needed)."""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "yaml" / "ACL4SSR_Online_Full.yaml"
REGIONS = (
    "🇭🇰 香港节点", "🇹🇼 台湾节点", "🇯🇵 日本节点",
    "🇸🇬 狮城节点", "🇺🇲 美国节点", "🇰🇷 韩国节点",
)
HONG_KONG = (
    "香港 01", "沪港 IPLC", "HK 01", "hk02", "HKG-03",
    "Hong Kong 01", "HongKong 02", "Hong-Kong 03", "Hong_Kong 04", "🇭🇰 01",
    "香港→日本 JP 01", "美国 US-HK 中转",
)
REGION_SAMPLES = (
    "香港 HK 01", "台湾 TW 01", "日本 JP 01", "新加坡 SG 01",
    "美国 US 01", "韩国 KR 01", "首尔 02",
)
OTHER_SAMPLES = ("德国 DE 01", "英国 UK 01", "加拿大 CA 01", "澳大利亚 AU 01")

# Synthetic/anonymized names only; never copy private subscription credentials here.
REGION_IDENTIFIERS = {
    "🇭🇰 香港节点": ("HK01", "hk-02", "HKG03", "🇭🇰 01", "Hong_Kong 01"),
    "🇯🇵 日本节点": ("JP01", "JPN-02", "🇯🇵 01", "[anytls]JP Tokyo"),
    "🇺🇲 美国节点": ("US01", "USA-02", "🇺🇸 01", "🇺🇲 02", "[anytls]US NYC"),
    "🇹🇼 台湾节点": ("TW01", "TWN-02", "🇹🇼 01", "[anytls]TW Hinet"),
    "🇸🇬 狮城节点": ("SG01", "SGP-02", "🇸🇬 01", "Singapore 01"),
    "🇰🇷 韩国节点": ("KR01", "KOR-02", "🇰🇷 01", "Seoul Korea 01"),
}
MISCLASSIFIED_SAMPLES = (
    "RU Example Justhost", "RU Example Justhost IPv6",
    "NL Kerkrade Demo", "NL Kerkrade Demo IPv6",
    "NL-Amsterdam-001-demohk", "SE-Stockholm-001-demohk",
    "FR-Soisy-sous-Montmorency-001-demohk", "Australia 01", "UA-Ukraine-01",
)
NOTICE_SAMPLES = (
    "剩余流量：10 GB", "流量剩余：1T / 2T", "套餐到期：2099-01-01",
    "到期时间：充足", "距离下次重置剩余：5 天", "距离下次重置: 1 天",
    "建议：卡顿请切换节点", "建议：Netflix Music 线路维护",
    "放丢失官网:https://example.invalid", "防丢失官网2:https://example.invalid",
    "新域名：https://example.invalid/us", "DEMO订阅共享：example.invalid",
    "📌 剩余流量: 1 GB (总 10 GB | 已用 9 GB)",
    "📅 配额模式: 每月1号自动重置配额", "🇺🇸 剩余流量：1 GB",
)
UNKNOWN_SAMPLES = (
    "GLOBAL-001 · VLESS", "001-未知-https-100ms", "unclassified-keep",
    "[余10 GB] [CF-随机-001] CF 电信优选 (demo)",
)


def accepts(group, name, proxy_type="http"):
    excluded_types = group.get("exclude-type", "").lower().split("|")
    if proxy_type.lower() in excluded_types:
        return False
    include = group.get("filter")
    exclude = group.get("exclude-filter")
    return (not include or bool(re.search(include, name))) and not (
        exclude and re.search(exclude, name)
    )


class OverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        cls.groups = {group["name"]: group for group in cls.config["proxy-groups"]}

    def test_override_only_and_unique_groups(self):
        self.assertEqual(set(self.config), {"proxy-groups", "rule-providers", "rules"})
        self.assertEqual(len(self.groups), len(self.config["proxy-groups"]))

    def test_group_display_order(self):
        self.assertEqual(list(self.groups), [
            "🚀 节点选择", "🚀 手动切换", "♻️ 自动选择",
            "🇭🇰 香港节点", "🇯🇵 日本节点", "🇺🇲 美国节点",
            "🇹🇼 台湾节点", "🇸🇬 狮城节点", "🇰🇷 韩国节点", "🌐 其他节点",
            "📲 电报消息", "💬 OpenAi", "📹 油管视频", "🎥 奈飞视频",
            "📺 巴哈姆特", "📺 哔哩哔哩", "🌍 国外媒体", "🌏 国内媒体",
            "📢 谷歌FCM", "Ⓜ️ 微软Bing", "Ⓜ️ 微软云盘", "Ⓜ️ 微软服务",
            "🍎 苹果服务", "🎮 游戏平台", "🎶 网易音乐", "🎯 全球直连",
            "🛑 广告拦截", "🍃 应用净化", "🐟 漏网之鱼", "🎥 奈飞节点",
        ])

    def test_references_and_no_cycles(self):
        allowed = set(self.groups) | {"DIRECT", "REJECT"}
        visited, active = set(), set()

        def visit(name):
            self.assertNotIn(name, active, f"Group cycle involving {name}")
            if name in visited:
                return
            active.add(name)
            for target in self.groups[name].get("proxies", []):
                self.assertIn(target, allowed)
                if target in self.groups:
                    visit(target)
            active.remove(name)
            visited.add(name)

        for name in self.groups:
            visit(name)
        for rule in self.config["rules"]:
            parts = rule.split(",")
            self.assertIn(parts[-1], allowed)
            if parts[0] == "RULE-SET":
                self.assertIn(parts[1], self.config["rule-providers"])

    def test_automatic_excludes_hong_kong(self):
        group = self.groups["♻️ 自动选择"]
        self.assertEqual(group["type"], "url-test")
        self.assertTrue(group["include-all"])
        self.assertNotIn("proxies", group)  # No indirect paths through other groups.
        for name in HONG_KONG:
            with self.subTest(name=name):
                self.assertFalse(accepts(group, name))
        for name in REGION_SAMPLES[1:] + OTHER_SAMPLES:
            with self.subTest(name=name):
                self.assertTrue(accepts(group, name))

    def test_other_excludes_existing_regions(self):
        group = self.groups["🌐 其他节点"]
        self.assertEqual(group["type"], "url-test")
        self.assertTrue(group["include-all"])
        for name in REGION_SAMPLES + HONG_KONG:
            with self.subTest(name=name):
                self.assertFalse(accepts(group, name))
        for name in OTHER_SAMPLES:
            with self.subTest(name=name):
                self.assertTrue(accepts(group, name))
        for region in REGIONS:
            self.assertIn(region, self.groups)
        for candidate in self.groups.values():
            if "🇰🇷 韩国节点" in candidate.get("proxies", []):
                self.assertIn("🌐 其他节点", candidate["proxies"])

    def test_ai_excludes_hong_kong(self):
        group = self.groups["💬 OpenAi"]
        self.assertEqual(group["type"], "select")
        self.assertTrue(group["include-all"])
        for name in HONG_KONG:
            with self.subTest(name=name):
                self.assertFalse(accepts(group, name))
        for name in REGION_SAMPLES[1:] + OTHER_SAMPLES:
            with self.subTest(name=name):
                self.assertTrue(accepts(group, name))
        self.assertIn("RULE-SET,OpenAi,💬 OpenAi", self.config["rules"])

    def test_ai_has_no_indirect_routes_and_rejects_empty_pool(self):
        group = self.groups["💬 OpenAi"]
        # Include-all adds subscription nodes/providers, not other proxy groups.
        self.assertNotIn("proxies", group)
        self.assertNotIn("use", group)
        self.assertEqual(group["empty-fallback"], "REJECT")

    def test_ai_excludes_direct_aliases(self):
        group = self.groups["💬 OpenAi"]
        self.assertFalse(accepts(group, "自定义直连", "direct"))
        self.assertFalse(accepts(group, "日本直连别名", "Direct"))
        self.assertTrue(accepts(group, "日本 JP 01", "ss"))

    def test_region_codes_and_flags(self):
        for expected, names in REGION_IDENTIFIERS.items():
            for name in names:
                with self.subTest(region=expected, name=name):
                    hits = [g for g in REGIONS if accepts(self.groups[g], name)]
                    self.assertEqual(hits, [expected])
                    self.assertFalse(accepts(self.groups["🌐 其他节点"], name))
                    for group in ("♻️ 自动选择", "💬 OpenAi"):
                        self.assertEqual(accepts(self.groups[group], name), expected != "🇭🇰 香港节点")

    def test_codes_do_not_match_inside_words_or_identifiers(self):
        for name in MISCLASSIFIED_SAMPLES:
            with self.subTest(name=name):
                self.assertFalse(any(accepts(self.groups[g], name) for g in REGIONS))
                for group in ("🌐 其他节点", "♻️ 自动选择", "💬 OpenAi"):
                    self.assertTrue(accepts(self.groups[group], name))

    def test_notices_excluded_from_all_dynamic_groups(self):
        for group in self.groups.values():
            if not group.get("include-all"):
                continue
            for name in NOTICE_SAMPLES:
                with self.subTest(group=group["name"], name=name):
                    self.assertFalse(accepts(group, name))

    def test_real_node_labels_not_treated_as_notices(self):
        cases = {
            "🇸🇬 新加坡直连": "🇸🇬 狮城节点",
            "[余10 GB] 日本专线": "🇯🇵 日本节点",
            "US01 剩余流量: 10 GB": "🇺🇲 美国节点",
        }
        for name, region in cases.items():
            with self.subTest(name=name):
                for group in (region, "🚀 手动切换", "♻️ 自动选择", "💬 OpenAi"):
                    self.assertTrue(accepts(self.groups[group], name))
        self.assertTrue(accepts(self.groups["🚀 手动切换"], "香港 直连"))

    def test_unknown_regions_still_allowed_for_ai(self):
        for name in UNKNOWN_SAMPLES:
            with self.subTest(name=name):
                self.assertFalse(any(accepts(self.groups[g], name) for g in REGIONS))
                for group in ("🌐 其他节点", "♻️ 自动选择", "💬 OpenAi", "🚀 手动切换"):
                    self.assertTrue(accepts(self.groups[group], name))

    def test_filter_definitions_stay_synchronized(self):
        notice = self.groups["🚀 手动切换"]["exclude-filter"]
        region_filters = []
        for name, group in self.groups.items():
            if name in REGIONS:
                self.assertEqual(group["exclude-filter"], notice)
                region_filters.append(group["filter"])
        for name in ("🎶 网易音乐", "🎥 奈飞节点"):
            self.assertEqual(self.groups[name]["exclude-filter"], notice)

        def union(patterns):
            for pattern in patterns:
                self.assertTrue(pattern.startswith("(?i)"))
            return "(?i)" + "|".join("(?:" + p[4:] + ")" for p in patterns)

        no_hk = union([self.groups["🇭🇰 香港节点"]["filter"], notice])
        self.assertEqual(self.groups["♻️ 自动选择"]["exclude-filter"], no_hk)
        self.assertEqual(self.groups["💬 OpenAi"]["exclude-filter"], no_hk)
        self.assertEqual(self.groups["🌐 其他节点"]["exclude-filter"], union(region_filters + [notice]))

    def test_rule_providers_update_daily(self):
        for provider in self.config["rule-providers"].values():
            self.assertEqual(provider["interval"], 86400)
            self.assertEqual(provider["type"], "http")
            self.assertTrue(provider["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
