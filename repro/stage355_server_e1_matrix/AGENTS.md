# 远程服务器

- 通过 `ssh autovoice-delld` 连接，不直接写用户名或 IP。
- 不读取、复制或输出 SSH 私钥。
- 远端写入仅限本基准目录 `/home/spz/Fast-Amortized-Bootstrapping-stage355-e1-server/`（由操作者经 sudo 创建并 chown 给 delld，2026-08-20 迁移完成；旧位置 `~/spz/...` 已清理）。
- 未经确认不使用 sudo（sudo 需要密码，Agent 的 BatchMode SSH 无法且不应交互输入）。
- 服务器规格：104 核 / 251 GB / Xeon Gold 6230R（AVX-512/VAES）；磁盘较满（/ 已用 97%），避免大文件。
- 运行中的基准支持断点续跑：整行完成则跳过，perf 循环从第一个未通过样本继续。
