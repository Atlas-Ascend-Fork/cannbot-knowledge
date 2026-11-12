# OpsTune 算子调优知识

从 [asc-tools tool-ops-tune](https://gitcode.com/cann/asc-tools/tree/14714fdab5b495b048e13151b418f058cc66c9ce/skills/tool-ops-tune) 迁入的算子性能调优知识：分层瓶颈判定规则的语义卡（判定条件/反证/阈值溯源，#220 已合入）、优化机制卡（八要素，本批）与案例证据卡（A-E 分级，后续批次）。规则 YAML 本体、代码模板、opstune.* 数据契约与 evals 回归留在工具仓，本 section 只承载可复用的知识半边。

- [判定规则语义](rules/index.md)：L0-L3 四层 24 条规则的判定条件、反证与阈值四级溯源（[msprof-doc] / [tuning-practice] / [mc2-practice] / 首期标定值 🟡）。
- [优化机制卡](mechanisms/index.md)：按判定结果路由的机制实施知识（流水/搬运/API/存储层次/Tiling/MC²/RegBase VF），含 rule→机制路由表与已知覆盖缺口。
