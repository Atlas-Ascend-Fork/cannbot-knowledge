# 本地图谱

需要浏览知识关系时，运行：

```bash
python3 <skill-dir>/scripts/knowledge_ingest.py --knowledge-root <repo> build-graph
```

`<skill-dir>` 是 `knowledge-ingest/SKILL.md` 所在目录，应先解析为实际路径；命令不依赖调用者的当前工作目录。

脚本扫描 `knowledge/` 下的 Concept，从显式 Markdown 相对或 bundle-absolute 链接确定性生成 `artifacts/graphs/graph.json`。节点保留 bundle 相对 Concept ID、OKF type、路径 profile、标题、状态和 tags，边统一标记为 `links_to`。

运行前会用统一 Contract 校验每张卡；非法卡片会让构建失败。重复执行会重建同一输出文件，因此该命令不承担人工关系编辑、增量同步或发布职责。

`artifacts/graphs/` 必须保持 gitignore。相似度、LLM 判定或可视化可以在本地产物上继续计算，但不得把推断边当作签入真值；需要长期保留的关系应直接体现在知识卡正文和可审核链接中。

图谱构建成功只说明卡片和显式链接可解析，不证明链接关系在语义上充分；语义审阅仍由贡献者和 reviewer 完成。
