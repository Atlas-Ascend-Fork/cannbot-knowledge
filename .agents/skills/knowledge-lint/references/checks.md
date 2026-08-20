# Checks

需要解释错误、选择局部/全库模式或审阅 Lint 覆盖边界时读取本文件。

## 确定性检查

- **Path**：domain-route、Profile、Operator/Runbook 附加层级和小写 snake_case 卡名合法。
- **OKF/Profile**：JSON Schema、公共字段、Profile 字段白名单和路径到 OKF type 的映射一致。
- **Tags/Platforms**：值受控、无重复、至少一个 task/topic；平台范围合法，`agnostic` 不混用。
- **Lifecycle/Trust/Time**：status、`replaced_by`、verified actor、RFC 3339 时间与先后顺序合法。
- **Sources**：非 draft 有来源；HTTP(S) 形状正确；已知 Git 来源固定到 40 位 commit。
- **Strict navigation**：启用 `--strict-navigation` 后，宽 `tree/<sha>/` 来源必须同时存在同 revision 的精确 blob 来源或正文链接。
- **Body**：正文非空，不含 Git 冲突标记、嵌入图片、TODO 或 FIXME 占位。
- **Navigation**：Bundle 根版本正确；domain 根及 `ops`/`model` 的注册 route 存在；每层 index 完整列出直接子项。这些协作骨架可只有 index，其他空目录仍报错。
- **Links/Logs**：Markdown 本地目标存在；日志文件名、H1、entry 时间格式及倒序正确。
- **Mirror**：指定发布镜像时，规范源与镜像的文件集合和内容完全一致。

## 运行模式

- 无 card/sample：扫描全部知识 Markdown，执行结构、导航和日志检查。
- 一个或多个 `--card`：只检查指定卡和相对链接，不检查完整树。
- `--sample N`：按稳定路径散列选择 N 张卡，只用于快速抽样；不能与 `--card` 同用。
- `--strict-navigation`：加强代码来源导航准入，可与局部、抽样或全库模式组合。
- `--json`：输出 root、checked 和结构化 errors。
- `--skill-mirror`：额外比较完整 Skill 目录。

退出码 `0` 表示无错误，`1` 表示发现治理错误，`2` 表示参数、知识根或输入不可用。

## 人工审阅边界

机器检查不能证明 URL 可访问、source 足以支持正文、平台实验真实发生或结论正确。来源 claim mapping、同名 API 边界、因果证据和版本冲突仍需独立审阅。
