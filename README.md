# mihomo-rules

适用于 Clash Party 的 Mihomo 自定义覆写。在原版 ACL4SSR_Online_Full.yaml 上保留原有分组和分流规则，仅定制节点分组。

## 配置文件

`yaml/ACL4SSR_Online_Full.yaml`

这是 **YAML 覆写文件**，不是完整订阅。它不包含服务器、密码、订阅链接或 API 密钥；节点继续由你在 Clash Party 中的订阅提供。

## 本版改动

1. 新增 **🌐 其他节点**：按当前六个地区筛选条件取反并过滤提示条目，保留未匹配六个地区的节点，使用 url-test 自动测速选择（300 秒，容差 50）。在原来可选全部六个地区的分组中也加入此选项。
2. **♻️ 自动选择**：使用 exclude-filter 按名称排除香港和提示条目，兼顾 港、独立的 HK/HKG 代码、Hong Kong、HongKong、Hong-Kong、Hong_Kong、🇭🇰 等命名。
3. 原版已有 **🇰🇷 韩国节点**，本版保留，没有并入“其他”。除 OpenAi 规则改为路由到 **🚀 节点选择** 外，既有分组中显式 proxies 的候选顺序和 rules / rule-providers 不变。
4. **OpenAi**：使用 OpenAi 规则集匹配后直接路由到 **🚀 节点选择**，不再维护独立的 OpenAi 代理分组。
5. **分组排序**：前三项保持“节点选择 → 手动切换 → 自动选择”，随后是“香港 → 日本 → 美国 → 台湾 → 狮城 → 韩国 → 其他”地区分组，再显示应用等其余分组。只调整 proxy-groups 的排列，不改变组内候选顺序或分流规则优先级。
6. **名称匹配修正**：给国家代码增加非英文字母边界，识别六个地区的旗帜；全部 12 个 include-all 分组统一排除明确的提示标题。

### 地区匹配和提示条目过滤

- 国家代码支持 HK/HKG、JP/JPN、US/USA、TW/TWN、SG/SGP、KR/KOR，并允许代码直接接数字，例如 US01、HK02。代码不能嵌在其他英文单词或字母标识符里，避免 Justhost 中的 us、Kerkrade 中的 kr、随机后缀中的 hk 造成误匹配。
- 识别 🇭🇰、🇯🇵、🇺🇸、🇹🇼、🇸🇬、🇰🇷；兼容原版使用的 🇺🇲 美国图标。香港组和“自动选择”使用一致的香港识别条件；“其他”排除全部六个地区的匹配项。
- 统一过滤以“剩余流量”“流量剩余”“套餐到期”“到期时间”“距离下次重置”“配额模式”“新域名”“防/放丢失官网”“订阅共享”“建议”等开头并带冒号的提示标题，兼容前置图标和共享前缀。
- 不笼统过滤“余”“GB”或“直连”。例如 [余10 GB] [CF-随机-001] …、日本专线直连仍可作为节点；节点名称中的“直连”与代理类型 direct 不同。
- 地区未知节点仍保留在“其他”和“自动选择”，不新增地区白名单或未知地区排除策略。
- 共享提示表达式定义在“手动切换”的 YAML 锚点 exclude-notices；“自动选择”使用 exclude-hk-and-notices。修改地区或提示表达式时，应同步“其他”的并集，测试会检查一致性。

### OpenAI 分流

OpenAi 规则集匹配到的流量直接路由到 **🚀 节点选择**，不再单独维护 OpenAi 代理分组。因此 OpenAI 及其 Cloudflare 验证请求会使用“节点选择”当前选中的节点。

此修改不新增其他 AI 服务的规则。使用规则模式时生效；全局模式或其他覆写可能绕过本规则。

## 导入 Clash Party

### 本地导入

在“覆写”页面通过本地文件导入本仓库的 YAML（不同版本入口名称可能不同）；如果没有文件导入入口，使用下面的远程链接导入。

在“订阅管理”中编辑目标订阅，关联此覆写并保存，重新应用该订阅。不要把覆写链接当作节点订阅链接。

### 远程导入（推荐）

仓库：[lyn-hart/mihomo-rules](https://github.com/lyn-hart/mihomo-rules)

YAML 覆写地址：

```text
https://raw.githubusercontent.com/lyn-hart/mihomo-rules/main/yaml/ACL4SSR_Online_Full.yaml
```

1. 在 Clash Party 的“覆写”页面粘贴上述链接并导入。
2. 到“订阅管理”编辑目标订阅，关联这个覆写、保存并重新应用。
3. 以后仓库更新 YAML 后，更新 Clash Party 中对应的远程覆写并重新应用。

如需维护自己的副本，可以 Fork 此仓库，并将链接中的 lyn-hart 替换为自己的用户名；仓库名或分支名改变时也要同步修改链接。

私有仓库不能直接用普通匿名 Raw 链接访问。不要在 URL 中嵌入 GitHub Token，也不要将订阅链接、真实节点或密码上传至公开仓库。

## 更新方式和限制

- 原有 ACL4SSR 远程规则集保留，通过客户端按 interval: 86400（每天）定期拉取；下载是否成功取决于网络和上游。配置文件本身无需每天重新生成。
- GitHub Actions 仅在推送、PR 或手动触发时校验本配置，不自动覆盖你的自定义内容，也不自动同步上游。
- 地区筛选根据**节点名称**，不是出口 IP 检测。已修正国家代码子串误匹配，但保留原有中文和英文地区关键词；多地区名称或不规范命名仍可能歧义，未标注地区的节点无法可靠分类。
- 已过滤已知格式的到期/流量等提示标题；其他格式需要按实际命名补充，不保证识别所有提示条目。
- 测速不代表某个网站一定可用；没有可匹配节点的组不能提供预期地区的代理，请检查实际候选项。
- 本地和 CI 静态测试不检查第三方远程规则下载情况，也不能替代你当前 Clash Party 版本与真实订阅的合并验证。

## 本地校验

需要 Python 3 和 PyYAML：

	python3 -m pip install PyYAML==6.0.2
	python3 -m unittest discover -s tests -v

默认运行静态测试，跳过需要内核的集成测试。如需复现离线内核校验，指定支持上述配置项的 Mihomo 可执行文件：

	MIHOMO_BIN=/path/to/mihomo python3 -m unittest discover -s tests -v

集成测试覆盖普通节点、仅 proxy-providers、两种来源混合、全香港、仅香港 provider、全直连、仅提示条目、仅提示 provider、地区未知及空节点列表，验证全部 12 个 include-all 分组；测试探测地址均为本机回环地址。

校验 YAML 可解析、分组名唯一、分组顺序、引用存在且无分组循环、代码边界及旗帜匹配、提示条目过滤、真实节点标签和地区未知节点保留、共享过滤条件一致性、OpenAi 规则路由和规则集更新间隔。

本版还使用 Mihomo v1.19.32 做了离线内核校验：合并模拟节点，将远程规则替换为测试用内联规则并略去 GEOIP 规则后，配置检查通过，并从运行中的内核 API 验证了全部 include-all 分组的候选列表。此测试不验证真实节点连通性、远程规则集或 Clash Party 的实际合并结果。

## 来源

- 上游：[mihomo-party-org/override-hub](https://github.com/mihomo-party-org/override-hub)
- 基础文件：[ACL4SSR_Online_Full.yaml](https://github.com/mihomo-party-org/override-hub/blob/1c7c45c3512a22b5b3425eb2e6c101d4d45691ce/yaml/ACL4SSR_Online_Full.yaml)
- 该文件最近修改提交：[163ace2](https://github.com/mihomo-party-org/override-hub/commit/163ace2f46cd4ecbdac27883fb64f97a422c1625)
- 上游 2026-01-28 的 AI 排除香港提交修改的是 **ACL4SSR_Online_Full_WithIcon.yaml**，不是这里使用的基础文件。
