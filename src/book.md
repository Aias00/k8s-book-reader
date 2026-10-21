---
title: "从零开始学 Kubernetes"
subtitle: "从容器概念到可验证的本地应用部署"
author: "Aias00"
date: "2026-10-21"
lang: zh-CN
toc-title: "目录"
rights: "原创教学内容；外部资料版权归原作者。"
description: "从容器、Pod 到 Deployment、Service、配置、存储和排错，循序渐进完成一个本地 Kubernetes 项目。"
---

# 写在开始之前

如果你第一次看到 Kubernetes，读作“库伯内特斯”，觉得它像一堵由英文缩写组成的墙，这本书就是为你准备的。Kubernetes 常简称 K8s，因为首字母 K 与末字母 s 之间有八个字母。它管理运行在一组机器上的容器，让应用按照你声明的要求运行。

本书目标是让你理解核心概念，在自己的电脑上部署一个网页，能找到常见故障的原因，并知道下一步该学什么。完成本书不等于能够独立维护生产集群；生产运维还涉及网络、备份、升级、审计和团队流程。

全书以 Kubernetes 官方文档为主要依据，并用自己的教学语言重新组织。末尾提供可点击的来源与延伸阅读。网络资料持续变化，安装时应以对应工具的官方页面为准。书中的 API 使用稳定版本，不把某个“最新版本号”写死。

## 怎样阅读

第一次学习请按顺序阅读第 1 至 9 章。每读完一章，先用自己的话回答章末问题，再执行实验。第 10 至 14 章用于补全能力。附录提供练习答案、命令速查和两周安排。

建议准备一台可以安装软件、连接互联网的电脑，至少约 4 GB 可供实验使用的内存和几 GB 空闲磁盘；实际需求取决于操作系统、容器运行时和虚拟化方式，8 GB 及以上整机内存更从容。镜像下载可能很慢，先区分网络问题与 Kubernetes 配置问题。

本书默认选择 **Docker + kind + kubectl**：Docker 提供容器运行环境，kind 在容器里创建练习集群，kubectl 向集群发命令。macOS、Windows 和 Linux 都能使用这条路线。命令示例以 Bash、zsh 或 WSL 的 shell 为准；Windows 原生 PowerShell 在多行输入和引号上存在差异，初学者可在 WSL 中统一操作。

发布前的自动化实验在新的 GitHub Actions Linux runner 中运行真实 kind 集群，固定 kind v0.33.0、Kubernetes v1.37.0 的官方 node 镜像摘要和同版本 kubectl。它验证网页服务、探针故障、回滚、存储与调度边界；实际证据和未测试项见公开仓库的交付记录。这个固定组合用于复现本次结果，不代替各平台安装文档，也不意味着所有 Kubernetes 版本行为完全相同。

实验仅针对你创建的本地 `k8s-book` 集群。执行任何写操作前，确认当前上下文，避免误操作工作环境。若你没有权限安装软件，可以先阅读概念，但动手结果必须在真正的集群中验证。

# 第 1 章　先弄懂：为什么需要 Kubernetes

## 从一个网站讲起

假设你写了一个小网站。最初只需在电脑上启动程序，就能从浏览器访问。后来要让别人访问，你把它放到服务器上。服务器重启怎么办？程序退出怎么办？访问量增加后要开三份程序怎么办？更新版本时如何尽量减少中断？这时你开始需要一套管理运行过程的方法。

容器先解决“把程序连同运行环境打包”的问题。镜像是一份可分发的模板，容器是用这份模板启动的进程实例。镜像像菜谱加备好的食材，容器像实际做出来的一份菜。这个比喻只帮助记忆：容器本质上仍然是进程，不是完整虚拟机。

Kubernetes 再解决“很多容器怎么持续运行”的问题。你告诉它希望有三份应用，它观察实际状态，如果只剩两份，就尝试补回一份。这个不断缩小实际状态与期望状态差距的过程，叫作**协调**。

## 它能做什么，不能替你做什么

Kubernetes 可以调度应用到节点，维持副本数，提供服务发现，组织滚动更新，并按配置执行健康检查。它不会自动修好程序逻辑错误，也不会自动替你设计数据库备份。配置了三个副本，也不代表应用天然高可用：如果三个副本都依赖同一处故障点，仍可能一起不可用。

如果你只是运行一个个人脚本，直接启动进程或者使用 Docker Compose 可能更合适。学习 Kubernetes 的价值，是理解应用规模扩大后，系统如何声明、调度和恢复。

## 你需要先掌握的终端知识

终端是用文字控制电脑的入口。`cd` 切换目录，`ls` 列出文件，`mkdir` 建目录。命令执行完没有输出，可能代表成功；遇到错误要读完整信息，尤其是最后几行。

```sh
mkdir k8s-practice
cd k8s-practice
pwd
```

`pwd` 显示当前目录。后续 YAML 文件都放在这里，避免不知道文件保存到了哪里。代码块内的命令不带提示符 `$`，可以直接复制。出现 `<名称>` 这样的占位符时，需要替换为实际值；不要原样执行。

**本章自测**：镜像与容器有什么区别？Kubernetes 可以保证程序永远没有 bug 吗？如果期望三个副本而实际只有两个，控制器会尝试做什么？

# 第 2 章　用一张地图认识集群

## 集群、节点、Pod

**集群（Cluster）**是一组受 Kubernetes 管理的计算资源。**节点（Node）**通常是一台虚拟机或物理机，在 kind 中则由容器模拟。节点提供 CPU、内存和网络等资源。

**Pod** 是 Kubernetes 调度和管理应用的基本单位。最常见的 Pod 只运行一个业务容器；某些紧密协作的容器也可以放在同一个 Pod 内，共享网络和指定的卷。你扩容的是多个 Pod 副本，而不是把同一应用的十个副本塞进一个 Pod。

```text
集群
├── 控制平面：接收请求，记录状态，做出调度与协调决策
└── 工作节点
    ├── Pod A → 网页容器
    └── Pod B → 网页容器
```

图表示逻辑职责。本书的单节点 kind 集群会在同一个节点中承担控制平面和工作负载，适合练习；生产常会把这些职责分开，并配置冗余。

## 控制平面各组件在忙什么

`kube-apiserver` 是 API 入口。kubectl 提交资源描述，首先与它交互。`etcd` 保存集群的关键状态；它并不是供你随意存放业务数据的数据库。`kube-scheduler` 为还没有绑定节点的 Pod 选择合适节点。控制器持续观察状态，例如副本数不足时触发补建。

每个节点上的 `kubelet` 负责让分配给这个节点的 Pod 按要求运行，并上报状态。容器运行时负责实际拉取镜像、启动容器。网络组件让 Pod 互通；Service 转发常由 kube-proxy 或其他替代实现提供。

不要把 Docker 和 Kubernetes 的关系理解成“集群必须装 Docker”。现代 Kubernetes 通过 CRI 接口使用容器运行时，例如 containerd。本书用 Docker 是为了运行 kind 的节点容器。

## 声明式管理

命令式表达是“现在帮我启动三个实例”。声明式表达是“这个应用的副本数应该是三个”。后者允许系统持续纠偏。

YAML 是描述期望状态的常见文本格式，kubectl 是提交与查询这些描述的工具。它们不是 Kubernetes 本身。你可以把 YAML 理解为订单，API 是接单窗口，控制器是不断检查订单是否落实的工作人员。

**本章自测**：kubectl 在你的电脑上还是集群里运行？谁负责选择节点？Pod 被删除后，为什么有时会自动出现一个新的？

# 第 3 章　搭建你的练习环境

## 安装顺序与平台选择

首先安装并启动 Docker。macOS 与 Windows 常使用 Docker Desktop；Windows 需按其官方要求启用 WSL 2 等组件。Linux 可以安装 Docker Engine。Docker Desktop 的许可与平台要求请自行查看其官方说明。之后从官方安装页安装 kubectl 和 kind。

- Docker：[Get Docker](https://docs.docker.com/get-started/get-docker/)
- kubectl：[安装工具](https://kubernetes.io/docs/tasks/tools/)
- kind：[快速开始](https://kind.sigs.k8s.io/docs/user/quick-start/)

在 macOS 中，已经安装 Homebrew 的读者可以执行以下命令安装后两个工具；Docker 需先按官网完成安装并启动。

```sh
brew install kubectl kind
```

其他平台请使用上述官方页面中与你的操作系统、CPU 架构匹配的步骤。不要混用 Intel 与 ARM 下载包。请尽量让 kubectl 与集群版本一致；官方支持的 kubectl 偏差范围通常是相对 kube-apiserver 前后一个次版本，具体限制见文末版本偏差政策。

安装完成后检查：

```sh
docker version
kubectl version --client
kind version
```

`docker version` 应同时显示客户端和服务端信息。若只有客户端信息并提示连接不到 daemon，先启动 Docker，或检查 Linux 上的服务与用户权限。不要通过对所有用户开放 Docker socket 来绕过权限问题。

## 创建本地集群

```sh
kind create cluster --name k8s-book --wait 120s
kubectl config current-context
kubectl --context kind-k8s-book get nodes
```

创建完成后的上下文名应为 `kind-k8s-book`，节点最终应显示 `Ready`。首次创建要下载节点镜像，需要等待。若超过 120 秒，先看错误，不要连续创建多个同名集群。可以用 `kind get clusters` 查看已存在的集群，再运行 `kind export logs --name k8s-book` 导出日志辅助排查。

上下文（context）是 kubectl 使用的集群、用户及默认命名空间组合。它相当于你当前操作的目的地。之后每次练习前检查：

```sh
kubectl config use-context kind-k8s-book
kubectl config current-context
```

## 创建独立命名空间

命名空间（Namespace）是同一集群里对资源进行逻辑分组的方式。先创建本书专用区域：

```sh
kubectl create namespace k8s-book
kubectl get namespaces
```

若提示 `AlreadyExists`，说明已经创建，不必重复。全书在应用命令中显式写 `-n k8s-book`，帮助你看清资源所在的位置。命名空间本身不能代替完整的安全隔离机制。

**完成标志**：你能列出一个 Ready 节点，并能在命名空间列表中看到 `k8s-book`。如果这一步尚未完成，先解决环境问题再继续，后续所有实验都依赖它。

# 第 4 章　读懂第一份 YAML

## 四个核心字段

Kubernetes 对象常见的四个部分如下：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-pod
spec:
  containers:
    - name: web
      image: nginx:1.28
      ports:
        - containerPort: 80
```

`apiVersion` 表示资源所属 API 版本，不是你电脑上的 Kubernetes 版本。`kind` 表示资源类型。`metadata` 放名字、标签等标识信息。`spec` 描述你期望它怎样运行。查询时看到的 `status` 是系统报告的实际状态，通常不应复制进你维护的清单。

YAML 用缩进表示层级，使用空格，不用 Tab。同一层级保持对齐。`containers` 前的短横线表示列表，意味着一个 Pod 可以描述多个容器。书中使用的 `nginx:1.28` 固定到次版本系列，方便复现；标签可能继续指向该系列的新补丁。严格复现应固定镜像摘要，并在更新时验证安全性。

## 创建、观察与删除

把上述内容保存为 `pod.yaml`。文件必须是纯文本，扩展名是 `.yaml`，避免编辑器悄悄保存成 `.yaml.txt`。

```sh
kubectl apply -n k8s-book -f pod.yaml
kubectl get pods -n k8s-book
kubectl describe pod hello-pod -n k8s-book
kubectl logs hello-pod -n k8s-book
```

`apply` 创建或更新资源；`get` 看概况；`describe` 看细节和事件；`logs` 看容器输出。首次拉取镜像期间，Pod 可能显示 `ContainerCreating`，随后进入 `Running`。

想看网页，可以运行：

```sh
kubectl port-forward -n k8s-book pod/hello-pod 8080:80
```

保持这个终端开启，用浏览器访问 `http://localhost:8080`，应看到 NGINX 欢迎页。`8080:80` 表示本机 8080 端口转发到 Pod 的 80 端口。按 Ctrl+C 停止转发，Pod 本身仍在运行。

`containerPort: 80` 是端口声明，不会自动把网页暴露到你的电脑或公网；真正访问还需要端口转发或后面的 Service 等机制。

```sh
kubectl delete pod hello-pod -n k8s-book
kubectl get pods -n k8s-book
```

这个手工创建的独立 Pod 删除后不会自动回来，因为没有 Deployment 等上层控制器替它维持副本。这就是下一章的切入点。

**本章自测**：`metadata.name` 与容器 `name` 是同一个概念吗？为什么声明 `containerPort` 后还需要转发？

# 第 5 章　用 Deployment 管理应用

## 从“启动一次”变成“持续保持”

Deployment 管理无状态应用的副本和更新。它通过 ReplicaSet 维持 Pod 数量。一般情况下，你维护 Deployment 清单，不直接编辑它生成的 Pod，也不手工修改它管理的 ReplicaSet。

把以下内容保存为 `deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello-web
  template:
    metadata:
      labels:
        app: hello-web
    spec:
      containers:
        - name: web
          image: nginx:1.28
          ports:
            - containerPort: 80
```

`template` 是 Pod 模板。`selector.matchLabels` 告诉 Deployment 哪些 Pod 属于自己，必须与模板的标签匹配。标签（Label）是键值标记，如 `app: hello-web`；名字标识单个对象，标签则帮助筛选一组对象。Deployment 的选择器创建后通常不能直接修改，修改时要规划重建。

```sh
kubectl apply -n k8s-book -f deployment.yaml
kubectl rollout status deployment/hello-web -n k8s-book --timeout=120s
kubectl get deployments,replicasets,pods -n k8s-book
```

Deployment 中 READY 最终应为 `2/2`。Pod 名称带自动生成的后缀，这是正常现象。

## 亲手观察自愈

```sh
kubectl get pods -n k8s-book -l app=hello-web
```

从输出复制一个 Pod 名，将下面的占位符替换后执行：

```sh
kubectl delete pod <实际的Pod名称> -n k8s-book
kubectl get pods -n k8s-book -w
```

你会看到一个新名字的 Pod 被创建。`-w` 持续观察，Ctrl+C 结束。这不是旧 Pod 起死回生，而是控制器创建了替代品。Pod 的 IP 和名字都可能变化，因此应用之间不应该依赖某一个 Pod 的地址。

## 扩容和声明文件的一致性

```sh
kubectl scale deployment hello-web -n k8s-book --replicas=3
kubectl get pods -n k8s-book
```

这是一次命令式修改。如果 `deployment.yaml` 里仍是 `replicas: 2`，下次 `apply` 可能把它改回两个。长期管理要把你真正希望的副本数写回清单。练习完成后，将副本数恢复为两个，并重新应用文件。

**本章自测**：删除 Deployment 管理的一个 Pod 后发生什么？为什么它的替代品通常不沿用旧名字？

# 第 6 章　Service：给会变化的 Pod 一个稳定入口

## 名字稳定，后端可以变化

Deployment 创建的 Pod 会更换，而调用者希望访问一个固定名字。Service 提供一个稳定的服务抽象，通过标签选择对应的 Pod，并维护转发所需的后端信息。现代集群使用 EndpointSlice 记录后端地址。

把以下内容保存为 `service.yaml`：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-web
spec:
  selector:
    app: hello-web
  ports:
    - name: http
      port: 80
      targetPort: 80
  type: ClusterIP
```

`port` 是 Service 的入口端口，`targetPort` 是后端 Pod 的目标端口，两者可以不同。选择器必须对应 Pod 的标签。Service 和 Deployment 可以同名，因为它们是不同类型的对象。

```sh
kubectl apply -n k8s-book -f service.yaml
kubectl get services -n k8s-book
kubectl get endpointslices -n k8s-book -l kubernetes.io/service-name=hello-web
kubectl port-forward -n k8s-book service/hello-web 8080:80
```

再次访问 `http://localhost:8080`。这里的端口转发会选择一个后端 Pod，适合开发调试；它并不等价于完整测试 Service 负载均衡路径。后端 Pod 被替换时，可能需要重新运行转发命令。

## 从集群内部验证 DNS 和访问

在另一个终端运行以下一次性检查。它会创建一个临时客户端 Pod，执行请求后删除。

```sh
kubectl run netcheck -n k8s-book --rm -i --restart=Never \
  --image=busybox:1.37 -- wget -qO- http://hello-web
```

应该输出 NGINX 页面的 HTML。如果本次运行异常中断，临时 Pod 可能残留，可用 `kubectl delete pod netcheck -n k8s-book` 清理后重试。BusyBox 是用于此练习的小型工具镜像，不属于应用本身。

状态显示就绪与一次真实请求成功是两项证据。刚滚动更新时，服务后端与节点转发规则可能还在传播；可在有限时间内重复只读 HTTP 检查，确认页面实际恢复。持续失败就继续排查后端、DNS 与网络，不应只看 Ready 就宣布整条路径成功。

同一命名空间里的 Pod 通常可用 `hello-web` 访问该 Service。跨命名空间可用 `hello-web.k8s-book`。完整名称通常为 `hello-web.k8s-book.svc.cluster.local`，其中集群域名可由管理员配置，并非永远是 `cluster.local`。你的电脑一般不能直接解析这种集群内部名称。

## 常见访问方式

| 方式 | 主要用途 | 本地练习的注意点 |
|---|---|---|
| ClusterIP | 集群内访问 | 本书默认使用 |
| NodePort | 通过节点端口访问 | kind 节点在容器里，还涉及宿主机映射 |
| LoadBalancer | 由外部负载均衡实现提供入口 | 裸机或 kind 通常需要额外实现，可能一直 Pending |
| Ingress | 按 HTTP 域名、路径路由 | 必须安装相应控制器 |
| port-forward | 本地调试 | 依赖持续运行的 kubectl 会话 |

创建 Ingress YAML 不会自动获得可工作的入口。Ingress API 仍可使用，但其功能已冻结；学习新入口能力时可以进一步了解 Gateway API，同样需要相应控制器与配置。本书不要求把应用开放到公网。

**本章自测**：Service 通过什么找到 Pod？Service 没有后端时，应首先检查什么？

# 第 7 章　ConfigMap 与 Secret：把配置移出镜像

## 为什么配置不应全部写进镜像

同一份程序在开发和生产可能使用不同的欢迎语、日志级别或数据库地址。如果每改一行配置就重新打包镜像，维护会变得笨重。ConfigMap 存放非敏感配置，Secret 用来承载需要谨慎处理的数据，例如令牌或密码。

本章把网页内容放进 ConfigMap。保存为 `configmap.yaml`：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hello-page
data:
  index.html: |
    <!doctype html>
    <html lang="zh-CN">
      <meta charset="utf-8">
      <title>我的 Kubernetes 小站</title>
      <h1>你好，Kubernetes！</h1>
      <p>这是我通过 ConfigMap 提供的第一个网页。</p>
    </html>
```

竖线 `|` 表示保留换行的多行文本。先创建 ConfigMap，下一章的完整 Deployment 会把它挂载到 NGINX 默认网页目录。

```sh
kubectl apply -n k8s-book -f configmap.yaml
kubectl get configmap hello-page -n k8s-book
```

## 两种常见注入方式

配置可以作为环境变量，也可以以卷挂载成文件。环境变量在容器启动时读取，修改 ConfigMap 后，已有容器的环境变量不会自动刷新，通常需要重新创建 Pod。普通 ConfigMap 卷的文件更新通常会经过一定延迟传播，应用是否重新读取还取决于自身行为；使用 `subPath` 挂载时，不会收到这类自动更新。

本书整目录挂载网页，不使用 `subPath`。初学阶段，为了明确结果，修改 ConfigMap 后可以执行滚动重启，让所有副本重新读取配置。

## Secret 的边界

```sh
kubectl create secret generic demo-secret -n k8s-book \
  --from-literal=DEMO_TOKEN=only-for-practice
```

这里刻意使用无价值的练习字符串。真实机密不要直接留在命令历史、聊天记录或公开 Git 仓库中。Secret 的 `data` 常以 Base64 表示，Base64 是编码，不是加密。是否启用存储加密、谁有权限读取 Secret，都需要单独配置。

环境变量引用片段如下，阅读理解即可，不必加入本书网页项目：

```yaml
env:
  - name: DEMO_TOKEN
    valueFrom:
      secretKeyRef:
        name: demo-secret
        key: DEMO_TOKEN
```

这段片段应放在某个容器定义下。它不是可以独立 `apply` 的完整资源。实验后可删除示例 Secret：

```sh
kubectl delete secret demo-secret -n k8s-book
```

**本章自测**：把密码做 Base64 后放进公开仓库安全吗？修改 ConfigMap 后，已有容器的环境变量会立即改变吗？

# 第 8 章　健康检查与资源：让系统知道应用的状态

## Running 不等于能服务

容器进程存在，只能说明它在运行；它可能还在加载数据，也可能已经卡死。Kubernetes 提供三种探针。

**readinessProbe（就绪探针）**回答“现在能接流量吗”。失败时，Pod 会变为未就绪，通常不再作为 Service 的就绪后端；它本身不会因此被重启。

**livenessProbe（存活探针）**回答“是否需要重启这个容器”。连续失败达到阈值后，kubelet 会按重启策略处理。错误地把外部数据库偶发故障作为存活失败原因，可能造成大量无效重启。

**startupProbe（启动探针）**给慢启动应用留时间。配置了启动探针后，在它成功之前，就绪和存活探针不会开始工作。简单 NGINX 静态网页启动很快，本书完整示例只使用就绪和存活探针。

若两种探针都检查同一个路径，删除页面可能同时触发两种失败，不能据此推断“就绪失败导致重启”。分开验证时，应让就绪路径失败、存活路径仍成功，观察 Service 就绪后端移除而 restartCount 不变；再单独破坏存活路径，检查容器重启与恢复。随书自动化实验用另建的故障 Pod 完成这项隔离检查，主线网页清单仍保持易读。

## requests 与 limits

`requests` 是调度时用于计算资源需求的重要依据。`limits` 约束运行时资源使用。CPU 的 `100m` 是 0.1 核，内存 `64Mi` 是 64 × 1024 × 1024 字节。

CPU 超出限制通常会被限流；内存达到限制后，进程可能被内核终止，出现 `OOMKilled`。节点内存压力也可能导致 Pod 被驱逐。资源不足时应结合事件和实际负载分析，不能见到重启就无限增大上限。

## 把前面知识合成完整应用

将之前的 `deployment.yaml` 替换为下面内容。这是完整文件，不是片段。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-web
spec:
  replicas: 2
  revisionHistoryLimit: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: hello-web
  template:
    metadata:
      labels:
        app: hello-web
    spec:
      containers:
        - name: web
          image: nginx:1.28
          ports:
            - name: http
              containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 64Mi
            limits:
              cpu: 500m
              memory: 128Mi
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 2
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          volumeMounts:
            - name: page
              mountPath: /usr/share/nginx/html
              readOnly: true
      volumes:
        - name: page
          configMap:
            name: hello-page
```

这个清单挂载整个网页目录，所以该目录中原镜像自带的文件会被挂载内容遮住。`readOnly` 表示容器不能通过这个挂载点改写配置。普通 NGINX 镜像的权限模型适合本地教学，不要据此假定已满足生产环境的非 root 与安全加固要求。

```sh
kubectl apply -n k8s-book -f configmap.yaml
kubectl apply -n k8s-book -f deployment.yaml
kubectl apply -n k8s-book -f service.yaml
kubectl rollout status deployment/hello-web -n k8s-book --timeout=120s
kubectl get pods -n k8s-book
```

保持 `port-forward` 运行，刷新浏览器。如果转发因 Pod 替换退出，重新执行第 6 章的转发命令。你应该看到中文欢迎页。

**本章自测**：就绪失败是否必然重启容器？`100m` 是一百核吗？为什么 ConfigMap 缺失可能导致 Pod 一直无法启动？

# 第 9 章　升级、回滚与配置更新

## 先区分三种改变

修改 Deployment 的 Pod 模板，例如镜像或探针，会触发新的滚动发布。只修改副本数是扩缩容，不会生成同样意义上的新模板版本。只修改外部 ConfigMap 内容，也不会自动产生 Deployment 的新模板修订。

本章不依赖另一个真实镜像版本，而是故意填错镜像标签，观察一次失败更新，然后恢复。务必先确认当前两个 Pod 均就绪。

```sh
kubectl rollout history deployment/hello-web -n k8s-book
kubectl set image deployment/hello-web -n k8s-book \
  web=nginx:this-tag-does-not-exist-k8s-book
kubectl rollout status deployment/hello-web -n k8s-book --timeout=45s
kubectl get pods -n k8s-book
```

预期更新超时，新 Pod 可能显示 `ErrImagePull` 或 `ImagePullBackOff`。因为设置了 `maxUnavailable: 0` 与 `maxSurge: 1`，且旧副本仍健康、集群资源足够，旧版本应继续服务。这是演示条件下的行为，不是对所有故障零中断的保证。

## 恢复到上一版

```sh
kubectl rollout undo deployment/hello-web -n k8s-book
kubectl rollout status deployment/hello-web -n k8s-book --timeout=120s
kubectl get pods -n k8s-book
```

`undo` 恢复之前的 Pod 模板。它不会撤销数据库迁移，也不会把 ConfigMap、Secret 或 PVC 一起恢复。因此“能够回滚镜像”不能等同于“整个系统能够回到过去”。长期管理应让 Git 中的声明文件也与目标版本一致。

## 修改网页

将 `configmap.yaml` 中的欢迎语改成“我完成了第一次配置更新”，然后：

```sh
kubectl apply -n k8s-book -f configmap.yaml
kubectl rollout restart deployment/hello-web -n k8s-book
kubectl rollout status deployment/hello-web -n k8s-book --timeout=120s
```

重新启动端口转发并刷新浏览器。`rollout restart` 通过修改 Pod 模板注解触发滚动重建。此处用它来得到清晰、可预期的练习结果；大型系统通常会使用配置版本化、校验和注解或应用热加载机制。

**本章自测**：为什么更新 ConfigMap 不等于产生新镜像版本？Deployment 回滚能恢复昨天的数据库数据吗？

# 第 10 章　存储：为什么文件会消失

## 三种生命周期

容器可写层里的文件依附于该容器实例。容器重建时，不应指望这些修改保留。`emptyDir` 卷跟随 Pod 生命周期，在同一 Pod 内的容器重启后可继续使用，但 Pod 删除后数据通常就消失。持久卷则用来把数据生命周期与单个 Pod 分离。

**PersistentVolume（PV）**代表集群中的一份存储资源。**PersistentVolumeClaim（PVC）**代表应用申请存储的请求。**StorageClass** 描述动态供应存储的类别和参数。你可以把它们理解为仓库空间、租用申请和租赁规格。

PVC 不是备份。存储所在磁盘、节点或整个本地集群被删除时，数据仍可能丢失。尤其在 kind 中，即使 PVC 叫“持久”，删除节点容器也可能让底层数据一并消失。

## 一个独立的存储实验

先检查是否有默认 StorageClass：

```sh
kubectl get storageclass
```

如果没有标为默认的 StorageClass，下面省略 `storageClassName` 的申请可能一直 Pending。此时先了解所用环境的存储供应方式，不要为了让状态变绿随便填写一个名字。kind 常提供本地存储供应，但应以实际输出为准。

保存为 `storage.yaml`：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: notes
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: notes-writer
spec:
  containers:
    - name: tools
      image: busybox:1.37
      command: ["sh", "-c", "sleep 86400"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: notes
```

一个文件中可以用 `---` 分隔多个对象。`ReadWriteOnce` 通常表示卷可被单个节点以读写方式挂载，不代表永远只允许一个 Pod 访问，具体还取决于存储实现。

```sh
kubectl apply -n k8s-book -f storage.yaml
kubectl wait -n k8s-book --for=condition=Ready pod/notes-writer --timeout=120s
kubectl exec -n k8s-book notes-writer -- sh -c 'echo hello-storage > /data/note.txt'
kubectl exec -n k8s-book notes-writer -- cat /data/note.txt
kubectl delete pod notes-writer -n k8s-book
kubectl apply -n k8s-book -f storage.yaml
kubectl wait -n k8s-book --for=condition=Ready pod/notes-writer --timeout=120s
kubectl exec -n k8s-book notes-writer -- cat /data/note.txt
```

最后应仍能读到 `hello-storage`，因为你删除的是 Pod，PVC 还在。本轮 CI 用相同 PVC UID、不同 Pod UID 和实际读回文件验证这一点；没有删除 kind 节点或恢复整个集群，因此不能据此推断节点丢失后的数据恢复能力。动态供应使用 `WaitForFirstConsumer` 时，PVC 在使用它的 Pod 创建前保持 Pending 也可能正常。

若没有按预期启动，查看 `kubectl describe pvc notes -n k8s-book` 与 Pod 事件。清理时 `kubectl delete -n k8s-book -f storage.yaml` 会同时删除 Pod 和 PVC；回收策略为 Delete 时，底层卷也可能被删除，请先确认不需要数据。

## 数据库应该怎样学

StatefulSet 为有状态工作负载提供稳定身份、顺序和卷关联，但不会自动替你完成数据库复制、故障恢复和备份。新手先把网站应用作为无状态服务，把数据库可靠性作为单独专题学习。

**本章自测**：容器重启和 Pod 删除对 `emptyDir` 的影响相同吗？PVC 为什么不能代替备份？

# 第 11 章　排错：用证据缩小问题范围

## 一条通用路径

遇到问题，先确认目标，再看状态，再看事件，最后看应用输出。不要在不了解原因时连续删除资源；删除可能让关键现场消失。

```sh
kubectl config current-context
kubectl get pods -n k8s-book -o wide
kubectl get deployment,service -n k8s-book
kubectl get events -n k8s-book --sort-by=.metadata.creationTimestamp
```

接着选择具体 Pod，替换名称后检查：

```sh
kubectl describe pod <实际的Pod名称> -n k8s-book
kubectl logs <实际的Pod名称> -n k8s-book --tail=100
kubectl logs <实际的Pod名称> -n k8s-book --previous
```

`--previous` 查看同一 Pod 内上一次退出的容器实例日志，并非任意历史 Pod 的日志；如果没有上一次实例，报错是正常的。多容器 Pod 应增加 `-c 容器名`。应用没有把信息写到标准输出时，`logs` 不一定有你需要的内容。

## 常见状态与第一步

| 现象 | 常见方向 | 优先证据 |
|---|---|---|
| Pending | 资源不足、调度约束、PVC 未绑定 | describe 中的调度事件 |
| ContainerCreating | 拉镜像、挂载、网络初始化 | Pod 事件 |
| ImagePullBackOff | 镜像名错误、权限、网络 | 拉取镜像错误原文 |
| CrashLoopBackOff | 启动后反复退出 | 当前与 previous 日志、退出码 |
| Running 但未就绪 | 探针失败或依赖未准备好 | 探针事件、应用日志 |
| OOMKilled | 容器内存不足等 | 容器终止状态、内存限制 |
| Service 访问失败 | 选择器、端口、后端、DNS、网络策略 | EndpointSlice 与实际 Pod 标签 |

这些字符串并非都属于 Pod 的正式 `phase` 字段。`kubectl get pods` 的 STATUS 栏综合展示多种信息；例如 `CrashLoopBackOff` 表示容器处于重启退避状态，而不是一种独立的 Pod phase。

## 一次可恢复的网络故障实验

保留正常 `service.yaml`，只在实时对象中把选择器临时改错：

```sh
kubectl patch service hello-web -n k8s-book \
  --type=merge -p '{"spec":{"selector":{"app":"wrong-app"}}}'
kubectl get endpointslices -n k8s-book -l kubernetes.io/service-name=hello-web
```

此时后端会消失或没有可用地址，集群内部对该服务的请求会失败。空后端可能表现为没有可用切片、`endpoints: []` 或 `endpoints: null`；判断时应检查可用地址与实际请求，不能假设 API 永远返回非空数组。不要用已经连上的旧端口转发来判断，因为它可能仍指向之前选中的 Pod。

观察后恢复：

```sh
kubectl apply -n k8s-book -f service.yaml
kubectl get pods -n k8s-book --show-labels
kubectl get endpointslices -n k8s-book -l kubernetes.io/service-name=hello-web
```

这次实验让你把“服务不通”具体化为“Service 选择器没有选中正确的 Pod”。恢复后，重新运行第 6 章的临时客户端验证访问。

## 看懂四种常见报错

`connection refused` 可能表示目标端口没有进程监听，也可能出现在错误的 API 地址上，要先看它连接的是哪里。`NotFound` 先查名字、类型和命名空间。`Forbidden` 表示请求已被识别但权限不足，不应通过借用管理员凭据来草率绕过。`no matches for kind` 可能表示 API 版本或类型错误，也可能表示所需自定义资源尚未安装。

**本章自测**：镜像拉取失败时，先改探针有用吗？为什么排查 Service 要同时看选择器与 Pod 标签？

# 第 12 章　安全、监控与自动扩容的第一课

## 最小权限

RBAC 通过 Role、ClusterRole 和绑定对象管理访问权限。Role 通常描述命名空间范围的权限，RoleBinding 把权限授予用户、组或 ServiceAccount。ClusterRole 可以描述集群范围权限，也可通过 RoleBinding 在一个命名空间内授予适用的权限。

ServiceAccount 是工作负载向 Kubernetes API 表明身份的一种机制，不是普通网页登录账号。不要为了方便给每个应用绑定 `cluster-admin`。不需要访问 API 的应用，可以考虑在 Pod 中设置 `automountServiceAccountToken: false`。

网络策略（NetworkPolicy）用于表达允许哪些流量，但只有网络插件支持并执行时才有效。创建了策略对象，并不自动证明隔离已生效；要实际测试允许与拒绝两类流量。命名空间也不等于网络防火墙。

## 镜像与运行权限

生产实践通常包括可信镜像来源、漏洞扫描、固定摘要、以非 root 运行、减少 Linux capabilities、限制权限提升及只读根文件系统。不能把这些字段不加测试地塞入任意镜像：有些镜像需要写临时目录或使用特定用户，应选兼容镜像并明确配置。

本书使用常见 NGINX 镜像突出概念，未完成生产安全基线。把学习项目投入真实业务前，应先调整镜像与运行权限，再进行验证。

## 指标、日志与事件各回答什么

指标描述随时间变化的数值，如 CPU、内存、请求量。日志记录应用输出的细节。事件描述 Kubernetes 观察到的调度、拉取、启动等动作，通常不是长期存储的审计档案。

```sh
kubectl top pods -n k8s-book
```

这个命令依赖 Metrics API，常由 Metrics Server 提供。kind 不一定预装，所以报 `Metrics API not available` 不等于应用故障。本书不要求为了完成基础实验安装监控栈。生产中通常还需要长期指标存储、日志收集、告警和追踪。

## HPA 为什么不能凭空扩容

HorizontalPodAutoscaler 按指标调整副本数。以 CPU 利用率为目标时，计算通常依赖相应容器的 CPU requests；没有请求值，可能无法正确计算利用率。它还需要可用的指标接口。

HPA 增加的是 Pod，不会自动给集群增加机器。节点没有余量时，新 Pod 仍会 Pending。节点自动扩容通常属于另一套机制。初学阶段先学会手动扩缩容，再学习 HPA 的采样、稳定窗口和行为配置。

**本章自测**：HPA 与增加节点是一回事吗？创建 NetworkPolicy 就一定会阻断流量吗？

# 第 13 章　结业项目：交付你的小站

## 你要完成的成果

不看前面解释，尝试用一个独立命名空间运行两份网页服务，网页内容来自 ConfigMap，经 Service 提供集群内入口，并能通过本机端口转发访问。Deployment 应包含资源请求、限制、就绪与存活探针。你还要证明自己能恢复失败更新、定位一次错误选择器，并清理资源。

随书 `examples/project/` 提供完整起点：`namespace.yaml`、`configmap.yaml`、`deployment.yaml` 和 `service.yaml`。EPUB 内也已列出所有关键清单；单独拿到电子书的读者，可按第 7、8、6 章依次手工创建相应文件。

在书籍项目目录使用配套文件时：

```sh
kubectl config use-context kind-k8s-book
kubectl apply -f examples/project/namespace.yaml
kubectl apply -n k8s-book -f examples/project/configmap.yaml
kubectl apply -n k8s-book -f examples/project/deployment.yaml
kubectl apply -n k8s-book -f examples/project/service.yaml
kubectl rollout status deployment/hello-web -n k8s-book --timeout=120s
kubectl port-forward -n k8s-book service/hello-web 8080:80
```

若你手工建立了工作目录，就把 `examples/project/` 路径替换成实际文件位置。网页出现后，保存一次 Pod 列表和浏览器截图作为自己的学习记录。

## 验收清单

1. `kubectl get deployment hello-web -n k8s-book` 显示两个就绪副本。
2. 浏览器能看到你自己写的中文欢迎语。
3. 从集群内访问 `http://hello-web` 能得到相同页面。
4. 删除一个 Pod 后，控制器会补建新 Pod。
5. 错误镜像实验失败后，能通过回滚恢复到健康状态。
6. Service 选择器故意写错时，能从后端和标签找到原因，再恢复。
7. 能解释为什么这个项目还不是生产部署。

本轮发布已在隔离 kind 集群中实际完成这些验收，并额外检查 HTTP 就绪失败不重启、存活失败后重启、PVC 换 Pod 保留、CPU 请求过大和节点选择器不匹配时的调度失败。自动化入口为 `lab/run_kind.py`，配套实验包可下载源文件；运行记录见 [交付记录](https://github.com/Aias00/k8s-book-reader/blob/main/DELIVERY.md)。

这些结果来自记录中的 CI 版本与场景，没有在你的电脑上替你执行。没有验证 HPA、NetworkPolicy 执行、多节点容错、节点丢失后的存储恢复或生产安全基线。请继续在自己的隔离环境复现，不把“能部署小站”当作生产验收。

## 清理，不留下忘记的资源

先停止所有 `port-forward` 会话，再删除练习命名空间。下面命令会删除该命名空间内的所有对象，包括你创建的 PVC，务必确认里面只有可丢弃的实验数据。

```sh
kubectl config current-context
kubectl delete namespace k8s-book
```

如果整个 kind 集群都不再需要：

```sh
kind delete cluster --name k8s-book
kind get clusters
```

这会删除本地练习集群及其节点容器。不要把它当成“暂停”，数据可能无法找回。只想暂时休息时，可以先不删除集群。

# 第 14 章　接下来怎样学习

## 两周学习安排

| 天数 | 学习任务 | 当天产出 |
|---|---|---|
| 第 1 天 | 阅读第 1、2 章 | 画出集群、节点、Pod 的关系 |
| 第 2 天 | 第 3 章安装环境 | 一个 Ready 节点 |
| 第 3 天 | 第 4 章 YAML 与 Pod | 能打开欢迎页 |
| 第 4 天 | 第 5 章 Deployment | 解释并演示自愈 |
| 第 5 天 | 第 6 章 Service | 完成集群内访问 |
| 第 6 天 | 第 7 章配置 | 写出自己的网页 |
| 第 7 天 | 复习与整理笔记 | 用自己的话解释五个概念 |
| 第 8 天 | 第 8 章探针与资源 | 两个健康副本 |
| 第 9 天 | 第 9 章升级回滚 | 恢复错误镜像更新 |
| 第 10 天 | 第 10 章存储 | 重建 Pod 后读到原文件 |
| 第 11 天 | 第 11 章排错 | 一份故障原因记录 |
| 第 12 天 | 第 12 章安全与指标 | 解释三条生产差距 |
| 第 13 天 | 第 13 章结业项目 | 独立完成验收 |
| 第 14 天 | 清理和回顾 | 写出下一阶段计划 |

如果安装用了一整天，很正常。不要因为没赶上表格而跳过基础。学习速度以你能解释和复现为准。

## 按需求继续，而不是按名词数量继续

要部署更多应用，学习 Job 与 CronJob、Helm 和 Kustomize。Job 管理以完成为目标的任务，CronJob 按时间计划创建 Job；它们与长期运行的 Deployment 目标不同。Helm 用模板和包组织部署，Kustomize 基于基础清单做组合与覆盖。

要理解线上稳定性，学习 PodDisruptionBudget、亲和性与反亲和性、拓扑分布约束、优雅终止以及节点维护。PodDisruptionBudget 约束某些自愿中断，不会阻止所有故障，也不代替副本与跨节点设计。

要运行真正业务，学习镜像构建与发布流水线、GitOps、入口控制器或 Gateway API、TLS、DNS、监控告警和备份恢复。要准备认证，可以在熟悉基础操作后，再结合官方 CKA 或 CKAD 的能力范围安排练习。

最有效的练习方式是每次只改变一个因素，先预测结果，再运行命令，用观察检验预测。能讲清楚失败原因，比背下十条命令更接近掌握。

# 附录 A　自测参考答案

**第 1 章**：镜像是可分发的模板，容器是运行实例。Kubernetes 不保证程序没有 bug。控制器会尝试创建替代实例，前提是资源与其他条件允许。

**第 2 章**：本书的 kubectl 在你的电脑上运行，通过 API 与集群通信。调度器选择节点。由控制器管理的 Pod 被删除后，控制器为维持期望状态创建替代品。

**第 4 章**：对象名字与容器名字属于不同层级。端口声明不会创建对外网络入口，所以还需要转发或服务暴露机制。

**第 5 章**：Deployment 会通过 ReplicaSet 补建 Pod。新 Pod 是新对象，通常会有新名字和地址。

**第 6 章**：Service 根据标签选择器找到后端；先检查选择器、Pod 标签、就绪状态和 EndpointSlice，再检查端口与网络路径。

**第 7 章**：Base64 可以轻易解码，不能保护公开的密码。通过环境变量注入的值不会因 ConfigMap 更新而自动改变。

**第 8 章**：就绪失败通常使 Pod 暂停接收 Service 流量，不会单凭该探针触发重启。`100m` 是 0.1 CPU 核。挂载所引用的 ConfigMap 不存在时，容器所需卷无法准备完成。

**第 9 章**：ConfigMap 是独立对象，修改它不等于修改镜像或 Deployment 模板。Deployment 的回滚不负责数据库恢复。

**第 10 章**：`emptyDir` 可以跨同一 Pod 内容器重启保存，但不能跨 Pod 删除保存。PVC 不提供独立备份副本与恢复流程。

**第 11 章**：镜像都未拉取成功时，修改探针通常不能解决问题。选择器与标签不匹配，Service 就无法找到正确后端。

**第 12 章**：HPA 调整 Pod 数量，节点扩容由其他机制负责。NetworkPolicy 是否生效取决于网络实现，还需要实际验证。

# 附录 B　命令速查与术语

## 命令速查

```sh
# 我在操作哪个集群？
kubectl config current-context
# 节点状态
kubectl get nodes
# 创建或更新声明
kubectl apply -n k8s-book -f deployment.yaml
# 查应用、服务和 Pod
kubectl get deployments,services,pods -n k8s-book
# 查详细状态与事件；替换占位符后执行
kubectl describe pod <Pod名称> -n k8s-book
# 查最近日志
kubectl logs deployment/hello-web -n k8s-book --tail=100
# 观察一次发布是否完成
kubectl rollout status deployment/hello-web -n k8s-book --timeout=120s
# 调试访问
kubectl port-forward -n k8s-book service/hello-web 8080:80
```

`logs deployment/hello-web` 通常选择其中一个 Pod，并不自动汇总所有副本。需要按标签汇总时，应查阅 logs 的选择器、并发和容器参数，并留意输出所属副本。

## 小白术语表

| 术语 | 可以先这样理解 |
|---|---|
| API | 程序之间约定的交互接口 |
| 镜像 Image | 应用及运行所需内容的分发模板 |
| 容器 Container | 从镜像启动的运行实例 |
| Cluster | 一组受 Kubernetes 管理的资源 |
| Node | 为 Pod 提供运行资源的节点 |
| Pod | 一个或多个紧密相关容器的运行单位 |
| Deployment | 管理无状态应用副本和更新的控制器资源 |
| ReplicaSet | 维持一组 Pod 副本数的资源 |
| Service | 为一组后端提供稳定访问抽象 |
| Namespace | 资源的逻辑分组范围 |
| Label | 便于分组和筛选的键值标签 |
| Selector | 按条件选择对象的规则 |
| ConfigMap | 非敏感配置对象 |
| Secret | 承载需要谨慎处理的数据的对象 |
| PVC | 应用的持久存储申请 |
| Ingress | HTTP/HTTPS 入口路由规则资源 |
| Controller | 持续推动实际状态接近期望状态的程序 |
| Context | kubectl 当前使用的集群、身份与命名空间组合 |

# 附录 C　资料来源与延伸阅读

本书通过检索并获取以下官方资料组织内容。正文是原创教学编排，并非官方文档的逐页翻译。链接内容可能更新，读者应优先查看与实际集群版本匹配的文档。配套 `research/sources.json` 记录抓取日期、标题和结果，`research/` 保留用于核对的网页快照。

1. [Kubernetes 概述](https://kubernetes.io/docs/concepts/overview/)：用途、能力与边界，对应第 1 章。
2. [集群组件](https://kubernetes.io/docs/concepts/overview/components/)：控制平面、节点组件，对应第 2 章。
3. [Kubernetes 基础教程](https://kubernetes.io/docs/tutorials/kubernetes-basics/)：部署、查看、服务、扩容、更新的学习路径。
4. [安装工具](https://kubernetes.io/docs/tasks/tools/)：kubectl 等本地工具，对应第 3 章。
5. [kind 快速开始](https://kind.sigs.k8s.io/docs/user/quick-start/)：创建本地集群和运行要求。
6. [Docker 安装入口](https://docs.docker.com/get-started/get-docker/)：容器工具安装。
7. [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)：副本、更新与回滚，对应第 5、9 章。
8. [Service](https://kubernetes.io/docs/concepts/services-networking/service/)：服务类型、端口与选择器，对应第 6 章。
9. [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/)：配置注入与更新限制，对应第 7 章。
10. [Secret](https://kubernetes.io/docs/concepts/configuration/secret/)：数据表示与安全注意点，对应第 7、12 章。
11. [存活、就绪与启动探针](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)：探针行为，对应第 8 章。
12. [容器资源管理](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)：requests、limits 与单位，对应第 8 章。
13. [持久卷](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)：PV、PVC、回收与访问模式，对应第 10 章。
14. [调试应用](https://kubernetes.io/docs/tasks/debug/debug-application/)：按现象收集证据，对应第 11 章。
15. [RBAC 良好实践](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)：最小权限，对应第 12 章。
16. [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)：控制器前提与 API 状态，对应第 6 章。
17. [版本偏差政策](https://kubernetes.io/docs/setup/release/version-skew-policy/)：kubectl 与控制平面版本关系。

中文官方资料入口：[Kubernetes 中文文档](https://kubernetes.io/zh-cn/docs/)。部分中文页面的更新可能滞后于英文页面，涉及版本差异时可对照阅读。遇到陌生术语，先回到术语表，然后只阅读与你当前问题有关的一小段，不必一次读完全部文档。
