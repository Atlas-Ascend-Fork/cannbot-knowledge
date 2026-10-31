# Group Management

- [aclrtCreateGroupInfo](aclrt_create_group_info.md)：申请保存 Group 信息的结构体，供 GetAllGroupInfo 填写；不支持 Group 或没有 Group 时返回空指针，使用后需 DestroyGroupInfo。
- [aclrtDestroyGroupInfo](aclrt_destroy_group_info.md)：销毁 aclrtGroupInfo 类型的数据。
- [aclrtGetAllGroupInfo](aclrt_get_all_group_info.md)：查询当前 Context 下全部 Group 的信息，写入 CreateGroupInfo 申请的结构体，再用 GetGroupInfoDetail 提取属性。
- [aclrtGetGroupCount](aclrt_get_group_count.md)：查询当前 Context 下可用的 Group 个数。
- [aclrtGetGroupInfoDetail](aclrt_get_group_info_detail.md)：从已查询的 Group 信息中按 groupIndex 与属性类型提取具体值；调用方提供输出缓冲区，接口返回实际属性长度。
- [aclrtSetGroup](aclrt_set_group.md)：为当前运算选择已创建的 Group；先经 DCMI 创建分组，再从 GroupInfo 取得 groupId，仅适用于 Atlas 推理产品 Control CPU 开放场景。
