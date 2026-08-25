# Checks

需要解释错误、选择局部/全库模式或审阅 Lint 覆盖边界时读取本文件。

## 确定性检查

- **Path**：domain-route、Profile、内容型 section、Operator/Runbook 附加层级和小写 snake_case 卡名合法。
- **OKF/Profile**：YAML mapping 无重复 key；JSON Schema、公共字段、Profile 字段白名单和路径到 OKF type 的映射一致。
- **Tags/Platforms**：值受控、无重复、至少一个 task/topic；平台范围合法，`agnostic` 不混用。
- **Lifecycle/Trust/Time**：status、`replaced_by`、verified actor、RFC 3339 时间与先后顺序合法。
- **Sources**：非 draft 有来源；资源为 HTTP(S) 或 Registry 登记根目录中的安全本地路径；识别出的 Git 来源固定到 40 位 commit。全库模式要求每个本地来源获取脚本存在且可执行；来源根已恢复时，归档完成标记必须匹配 Registry，且被引用文件必须存在；根不存在时保持离线可检查。
- **Strict navigation**：启用 `--strict-navigation` 后，宽 `tree/<sha>/` 来源必须同时存在同仓库、同 revision 的精确 blob 来源或正文 Markdown 链接。
- **Body**：正文非空，不含 Git 冲突标记、行内/显式引用式/HTML 嵌入图片、TODO/FIXME 占位或位于行尾/字段中部的疑似截断点；摘要不得截断，也不能只是发布占位、告警标记或表格标题。
- **Navigation**：Bundle 根版本正确；domain 根及 `ops`/`model` 的注册 route 存在；每层 index 完整列出直接子项。这些协作骨架可只有 index，其他空目录仍报错。
- **Links/Logs**：行内和显式引用式 Markdown 本地目标必须是 `knowledge/` 内的现有文件；日志文件名、H1、entry 时间格式、`Summary`/`Details` 和倒序正确。

## 运行模式

- 无 card/sample：扫描全部知识 Markdown，执行结构、导航和日志检查。
- 一个或多个 `--card`：只检查指定卡和相对链接，不检查完整树。
- `--sample N`：按稳定路径散列选择 N 张卡，只用于快速抽样；不能与 `--card` 同用。
- `--strict-navigation`：加强代码来源导航准入，可与局部、抽样或全库模式组合。
- `--json`：输出 root、checked 和结构化 errors。

退出码 `0` 表示无错误，`1` 表示发现治理错误，`2` 表示参数、知识根或输入不可用。

Lint 使用本 Skill 所属仓的 Contract 校验目标根；两边 Contract 文件不一致时以退出码 `2` 失败，不导入或执行目标根的 Python。

## 人工审阅边界

机器检查不能证明 URL 可访问、source 足以支持正文、平台实验真实发生或结论正确。来源 claim mapping、同名 API 边界、因果证据和版本冲突仍需独立审阅。
