# 本地图谱

图谱是知识卡之间已有 Markdown 链接的按需视图。日常建卡、更新和批次入库只维护知识正文、索引与原有 Lint/Query 检查，不要求构图、候选召回、Agent 关系判定或额外的关系缓存。卡片没有相关链接也可正常入库。

## 构建与查看

```bash
python3 <skill-dir>/scripts/knowledge_ingest.py --knowledge-root <repo> build-graph
```

输出为 ignored 的 `artifacts/graphs/graph.json`。克隆仓库后即可构建，无需其他图谱产物；再次执行会根据当前卡片重新生成。

需要本地可搜索的 HTML 视图或显式检查已有产物时：

```bash
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> build
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> viz
python3 <skill-dir>/scripts/knowledge_graph.py --knowledge-root <repo> verify
```

`build` 与 `build-graph` 共用同一实现。`viz` 写入 `artifacts/graphs/graph.html`；`verify` 对照当前卡片链接检查 JSON，如有 HTML 也检查其一致性。图谱陈旧时重新 `build`，HTML 陈旧时重新 `viz`。这些命令都不修改知识卡；本地图谱缺失或陈旧不影响常规入库与 `check.sh`。

## 链接语义

- 节点仅为通过统一 Contract 的知识卡，ID 为 Bundle 相对路径去掉 `.md`。
- 边仅为正文中卡片到卡片的有向 `links_to`，同方向的重复链接合并。API 到算子卡片的关联直接由普通正文链接保留；不要求额外标记或反向链接。
- 复用 Contract 对行内、显式引用式、Bundle 根相对链接和 URL 编码路径的解析。图片、代码中的示例、外部 URL、登记的固定本地源码、自链接和 Index 导航不形成边；Index 不作为节点。
- 不从目录、标题、标签或语义相似性推断关系，不维护专用图谱块。自然的正文链接与其说明一起参与 Query 检索。
- JSON 与 HTML 都是 ignored 派生产物，不是独立知识事实；技术回答仍需打开正文、核对适用范围和来源。

## 按需发现 API 与算子的引用

需要发现新的 API 引用时，在登记源码恢复并校验后运行：

```bash
python3 <skill-dir>/scripts/api_operator_links.py --knowledge-root <repo> suggest
```

该命令保留固定源码的调用提取、平台与 API 归属校验，输出 ignored 的 `artifacts/graphs/api_operator_links.json`，包含完整证据和可采用的普通 Markdown 链接。源码直接调用与仅有正文的调用示例分别标注；语法调用不证明运行时可达性。Registry 的展示上限只控制建议数量，不限制正文链接或图谱边。

建议不会直接成边或回写知识卡，也不作为入库门禁。作者核对并采用后可把链接加入正文；固定归档镜像在完整保留的来源正文后追加普通链接列表，由镜像校验器保留并验证，不需要任何注释标记。
