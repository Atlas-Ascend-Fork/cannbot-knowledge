# KfcWorkspace

- [构造函数与析构函数](constructor_and_destructor.md)：用于创建KfcWorkspace对象，Kfc全称为kernel function call，表示核间通信调用。
- [GetKfcWorkspace](get_kfc_workspace.md)：获取用于CubeResGroupHandle消息通信区的内存地址。用户使用CubeResGroupHandle接口时，需要用此接口自主管理空间地址。
- [KfcWorkspace](kfc_workspace.md)：KfcWorkspace 接口集，用于管理 Kfc 工作区内存，含构造与析构函数、UpdateKfcWorkspace、GetKfcWorkspace 等。
- [UpdateKfcWorkspace](update_kfc_workspace.md)：更新用于CubeResGroupHandle消息通信区的内存地址。用户使用CubeResGroupHandle接口时，需要用此接口自主管理空间地址。
