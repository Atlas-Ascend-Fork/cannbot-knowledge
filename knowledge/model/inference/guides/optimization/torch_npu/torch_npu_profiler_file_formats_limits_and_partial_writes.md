---
type: Guide
title: TorchNPU Profiler的文件格式、大小边界与部分写入
description: 记录读写格式、大小限制、二进制尾部和归档委托边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_path_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_path_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-11T07:06:23Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的文件格式、大小边界与部分写入

## 范围

完整核对PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的FileManager。本文只读源码，未读取/创建真实trace、CSV、JSON、DB或归档；PathManager完整行为仍另计，本文仅核直接读写检查和create_file_safety。

## 空返回之前可能先抛错误

file_read_all与read_csv_file先调用check_directory_path_readable，再检查是否常规文件和size；非文件/空文件分别返回空字符串/空列表，但不存在路径可在前置检查先抛错，不能写成“所有文件不存在都返回空”。read_json_file没有这条前置helper，缺文件或空文件返回{}；有效JSON不强制为dict，Optional[Dict]注解不能替代schema校验。

发布给file_read_all/read_json_file加超过10×1024³字节警告并返回空值，CSV阈值为5×1024³；等于阈值不在该超限分支。主线这些方法没有相同本地大小门槛，不推导整个软件栈无限制或大文件一定能完成。JSON解码/CSV转Bean和open/read内部异常包为RuntimeError；前置stat/权限helper异常不一定经同一包装。

read_csv_file使用csv.DictReader并对每行调用class_bean，不自行解释单位或验证所有列。read_json_file按UTF-8读；file_read_all/open和CSV没有统一显式encoding。check_file_owner是root或当前有效UID，writable/readable只返回os.access结果。读取helper主线对symlink和access不足警告、缺路径仍抛；发布相应helper对symlink/access不足抛错，owner不一致本身警告，不能把所有方法名中的check理解成同样拒绝策略。

## 写入不是一组原子提交

CSV/JSON/JSON-GZ/文本/二进制与prepare-trace写方法大多if not data直接返回，因此空容器/空串通常不创建、不截断，也不清旧产物；不能因本轮输入为空就把旧文件当本轮成功输出。create_json_file只拼路径委托create_json_file_by_path；CSV仅headers为真才写表头。

| 方法族 | 本地动作和边界 |
|---|---|
| CSV | 'w'打开，csv.writer写可选headers再writerows，迭代/单元转换失败可留部分文件 |
| JSON | 先以'w'打开（可截断旧文件），再json.dumps(indent可选, ensure_ascii=False)并写；序列化失败仍可能留下空文件，没有临时文件/rename提交 |
| JSON-GZ | gzip.open('wt')再json.dump，序列化设置不与普通JSON强制一致 |
| 文本 | 'w'直接写字符串，内部异常转RuntimeError |
| 二进制 | create_file_safety后os.open(O_WRONLY)交fdopen('wb')写，未显式O_TRUNC；已有更长文件可能保留尾部字节 |
| 空标记 | create_empty_file不按data真值跳过，以'w'打开空内容，目录/权限/创建在内部open的try之前 |

二进制尾部边界有直接helper依据：create_file_safety发现文件存在就return，并不截断；新文件则O_WRONLY|O_CREAT创建。各方法前置目录/权限/文件检查与写入不构成同一事务，失败没有统一删除已写内容或恢复旧文件。它们没有在本地证明跨进程并发写安全。

prepare-trace将JSON列表去最后一个字符，append-trace以'a'追加逗号加序列化列表去首字符后的串，随后按需rename；不是任意已闭合JSON文件的通用合并。rename发生在写try之后，异常包装边界也不同；完整trace拼装限制见[Trace追加与栈](torch_npu_profiler_trace_append_and_collapsed_stack.md)。

## DB文件检查没有认证SQLite内容

check_db_file_vaild先检查输入文件路径，再getsize；主线仅拒绝size<0，发布再拒绝超过10GiB。size分支不拒绝0字节，不验证SQLite header、schema、表或完整性；成功通过这个helper不代表连接/查询可用，连接句柄、逐批提交与查询空结果的边界见[数据库装配与部分失败](torch_npu_profiler_database_assembly_and_failure_boundaries.md)。

## 主线新增tar.gz的窄范围

发布模块没有compress_to_tar_gz；主线先检查输入目录和归档路径，将source规范路径basename作归档顶层，archive.add(root, recursive=False)，随后遍历直接子项，不在exclude_names集合中的项按子路径archive.add。排除匹配的是直接子项名字，不是对任意深度/正则的全局过滤；下层归档语义仍委托tarfile。

归档以'w:gz'直接打开，没有本地临时文件/原子替换/失败回滚；只捕OSError和TarError包RuntimeError，前置检查和exclude_names集合构造在这个try之外。源码docstring保留顶层目录的约定，不据此宣称归档已完成、内容快照一致或支持全部特殊文件。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（1–235行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_path_manager.py)（34–49,51–89,131–141行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（1–220行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_path_manager.py)（34–49,51–102,144–154行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（27–30行；有界辅助）
