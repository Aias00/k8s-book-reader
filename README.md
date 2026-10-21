# 从零开始学 Kubernetes

14 章正文、3 个附录、7 份配套 YAML，从 Pod、Deployment 和 Service 走向配置、健康检查、回滚、持久卷与排错。以本地无状态网页为主线，明确学习项目与生产系统的差距。

- [在线阅读](https://aias00.github.io/k8s-book-reader/)
- [下载 EPUB](https://aias00.github.io/k8s-book-reader/downloads/k8s-book-reader.epub)
- [版本发布与离线文件](https://github.com/Aias00/k8s-book-reader/releases)
- [公开书稿与实验](https://github.com/Aias00/k8s-book-reader)

阅读页浅色默认，支持共享 `aias-reader-theme` 深色偏好、目录、全文搜索、字号与继续阅读。320/390px 可阅读，禁用 JavaScript 仍有完整正文、目录和翻页。

## 原稿与配套清单

`src/book.md` 为唯一原稿，`examples/` 为 7 份教学清单，`examples/project/` 为中文网页项目。元信息位于 `tools/reader-metadata.json`，网页与共享主题在 `web/`，离线排版在 `epub/`。

按第 3 章安装 Docker、kind、kubectl，在自己的隔离 `k8s-book` 集群中学习；写操作前检查 `kind-k8s-book` 上下文。命令适用于 Bash、zsh 或 WSL，具体版本要求以官方文档为准。

## 真实集群验证

`lab/kind-ci.sh` 专用于 Linux amd64 CI：下载并校验固定 kind v0.33.0 与 kubectl v1.37.0，使用官方 node 镜像摘要创建隔离单节点集群，运行 `lab/run_kind.py`，结束后删除本次集群。它不复用工作环境的 kubeconfig，不会用静态 YAML 解析替代运行。

实验覆盖 Deployment/Service 与真实 DNS/HTTP、端口转发、自愈/扩缩、HTTP 探针隔离、错误镜像发布与回滚、ConfigMap 更新、错误选择器恢复、PVC 跨 Pod 保留，以及 CPU 请求过大和 nodeSelector 不匹配时的调度失败。实际通过状态、工作流与 job ID 以 [DELIVERY.md](DELIVERY.md) 及 `research/runtime-validation.json` 为准。

在已经创建的专用 `kind-k8s-book` 空白集群上，也可在项目根目录运行 `python3 lab/run_kind.py`；它会修改本书命名空间并注入故障。自动化探针测试使用单独生成的测试 Pod，7 份入门 YAML 保持简洁。

## 构建与阅读检查

需要 Python 3.10+、Pandoc 3.12.1、Java 17+。执行：

```sh
sh build.sh
python3 tools/reader_verify.py
python3 tools/verify_book.py
sh tools/epubcheck.sh
```

`site/` 为静态阅读站与下载区，原有中文 EPUB、离线 HTML 和学习包保留在 `dist/`。构建检查 18 个阅读单元的书稿/EPUB/网页/搜索/实验包一致性；EPUBCheck 5.4.0 遇到警告也会失败。

浏览器回归需要 Node.js 22、Playwright 1.64.1 与 Chromium：先运行 `python3 -m http.server 8798 --bind 127.0.0.1 --directory site`，再执行 `BOOK_URL=http://127.0.0.1:8798/ node tools/browser-check.cjs`。

## 维护与发布范围

原 `k8s-book` 维护仓库保持 private。公共 `k8s-book-reader` 使用白名单源码与干净历史，不包含私有历史、官方网页缓存、集群凭证或旧日志。维护仓库 `tools/export_public.py` 导出 `.publication/`；公共仓库 Actions 运行真实 kind、全部阅读检查并部署 Pages。Release 使用对应 CI 的同一产物，不覆盖历史版本。

本书不声称完成生产安全基线、多节点容错、节点丢失后的存储恢复、NetworkPolicy 执行、HPA 或负载压测。PVC 保留不是备份，端口转发不是负载均衡证据，单节点 kind 不能替代生产演练。书稿经 AI 辅助整理，技术结论可通过列出的来源与实验记录核对。
