#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Agent 技术雷达工作流 -> 桌面 Agent 开发者经验库 同步引擎
将工作区 D:\Agent视频学习录 的流水线研读产物，结构化同步至:
C:\Users\jiang\Desktop\开发经验\开发者经验分析-Agent
"""

import os
import shutil
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SRC_DIR = r"D:\Agent视频学习录"
DEST_DIR = r"C:\Users\jiang\Desktop\开发经验\开发者经验分析-Agent"
VAULT_DIR = os.path.join(SRC_DIR, "output", "vault")

# 专题分类配置
TOPICS_CONFIG = [
    {
        "id": "01-conferences-lectures",
        "name": "01-顶级峰会与学术讲座专题",
        "category_src": "conference",
        "desc": "收录来自 Strange Loop、USENIX、QCon、GOTO 等全球顶尖技术峰会的硬核架构与语言设计讲座研读"
    },
    {
        "id": "02-podcasts-interviews",
        "name": "02-硬核科技播客与访谈专题",
        "category_src": "podcast",
        "desc": "收录来自 Dwarkesh Patel、Latent Space、Lex Fridman、硅谷101 等顶尖播客的 AI 科学家一手对话与行业思考"
    },
    {
        "id": "03-engineering-blogs",
        "name": "03-大厂工程与架构演进专题",
        "category_src": "blog",
        "desc": "收录 OpenAI、Anthropic、Cloudflare、Stripe、Netflix 等全球顶尖科技公司的工程架构与生产避坑沉淀"
    }
]

# 核心高价值独立直读报告映射配置
STANDALONE_REPORTS = [
    {
        "seq": "01",
        "domain": "顶级峰会",
        "title": "StrangeLoop-代码化鸟鸣DSL与编译器模式深度研读",
        "src_rel": "conference/20261012__Birdsong as code_ by Chris Ford (Strange Loop 2023).md",
        "desc": "Strange Loop 2023 经典讲座研读：用 Clojure/Lisp 将自然界复杂鸟鸣建模为 AST，剖析音乐形式语法、编译器领域特定语言 (DSL) 与符号计算模式",
        "topic_id": "01-conferences-lectures"
    },
    {
        "seq": "02",
        "domain": "大厂架构",
        "title": "Cloudflare-托管计算工作负载认证与零信任身份置换实战",
        "src_rel": "blog/20261012_Trading a Cloud Identity for Your Own_ Workload Attestation on Managed Compute.md",
        "desc": "Cloudflare 生产级安全架构研读：在多租户托管计算环境下，如何通过 SPIFFE/SPIRE 与 TPM 证明将云厂商临时身份安全置换为私有服务零信任凭据",
        "topic_id": "03-engineering-blogs"
    },
    {
        "seq": "03",
        "domain": "大厂落地",
        "title": "OpenAI-Daybreak安全大模型降本96%与自动化调查实战",
        "src_rel": "blog/20261012_Sophos cuts threat investigation time by 96% with OpenAI Daybreak.md",
        "desc": "OpenAI 工业级落地案例研读：全球顶级安全厂商 Sophos 如何利用 OpenAI Daybreak 自动化处理 52% MDR 案件，调查耗时狂降 96% 的架构与人机协同机制",
        "topic_id": "03-engineering-blogs"
    },
    {
        "seq": "04",
        "domain": "大厂架构",
        "title": "Stripe-代币化计费演进困境与计量系统韧性设计解析",
        "src_rel": "blog/20261012_Why I tried to kill token billing (and why we kept it).md",
        "desc": "Stripe 计量计费架构研读：大模型时代 Token-based 计费的技术复杂性、高并发实时计数器的一致性困境、以及兼顾用户心理学与财务韧性的权衡",
        "topic_id": "03-engineering-blogs"
    },
    {
        "seq": "05",
        "domain": "硬核访谈",
        "title": "DwarkeshPatel-从AlphaFold到前沿生物AI大模型边界深度研读",
        "src_rel": "podcast/20261012_Why AlphaFold Didn't Solve Protein Folding — Pushmeet Kohli, Google DeepMind & S.md",
        "desc": "Google DeepMind 副总裁 Pushmeet Kohli 深度访谈：剖析 AlphaFold 3 的本质局限、结构生物学与药物研发中 AI 模型的泛化瓶颈与下一代范式",
        "topic_id": "02-podcasts-interviews"
    },
    {
        "seq": "06",
        "domain": "前沿播客",
        "title": "LatentSpace-大模型时代用户体感瓶颈与端到端产品破局",
        "src_rel": "podcast/20261012_E255｜模型越来越强，为什么用户没感觉？再访阿里国际站总裁张阔.md",
        "desc": "硅谷与全球 AI 落地反思：为什么底层基础模型能力指数级跃升，终端用户却感知平淡？解构从 Raw Model 到垂直场景工作流封装的关键断点",
        "topic_id": "02-podcasts-interviews"
    },
    {
        "seq": "07",
        "domain": "顶级峰会",
        "title": "QCon-Zig系统级编程与下一代高并发内存安全解析",
        "src_rel": "conference/20261012_Systems Programming with Zig • Garrison Hinson-Hasty & Trevor Berrange Sanchez •.md",
        "desc": "系统级软件工程研读：Zig 语言显式内存管理、Comptime 编译期执行哲学与零隐式控制流，如何在保持 C 语言极简的同时提供现代系统级工程安全",
        "topic_id": "01-conferences-lectures"
    },
    {
        "seq": "08",
        "domain": "大厂架构",
        "title": "Anthropic-全模态Clef模型演进与低成本推理优化实战",
        "src_rel": "blog/20261012_Introducing Clef-omni with full multimodality, plus a faster Clef and a cheaper .md",
        "desc": "前沿大模型工程化研读：多模态端到端融合架构设计、轻量级推理引擎加速策略与企业级推理成本骤降的工程实现方案",
        "topic_id": "03-engineering-blogs"
    }
]

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def generate_readme(standalone_items, topics_tree):
    """生成桌面经验库根目录下的 README.md 知识全景总看板"""
    lines = [
        "# Agent 开发者经验分析知识库 (Agent Dev Experience Vault)\n",
        "> **库定位**：由 Agent 依据自动化技术雷达流水线全天候抓取、排重、六段式深度研读沉淀的工业级知识库。  ",
        f"> **工作区来源**：[`D:\\Agent视频学习录`](file:///D:/Agent视频学习录)  ",
        "> **执行规范**：[开发者经验分析与Agent自动化执行规范.md](./开发者经验分析与Agent自动化执行规范.md)\n",
        "---\n",
        "## 一、知识全景拓扑图 (Knowledge Map)\n",
        "```mermaid",
        "flowchart TD",
        '    Root["Agent 开发者经验分析知识库"] --> T1["01-顶级峰会与学术讲座"]',
        '    Root --> T2["02-硬核科技播客与访谈"]',
        '    Root --> T3["03-大厂工程与架构演进"]',
        '    T1 --> F1["01-StrangeLoop-代码化鸟鸣DSL模式"]',
        '    T1 --> F7["07-QCon-Zig系统级编程内存安全"]',
        '    T2 --> F5["05-Dwarkesh-AlphaFold前沿生物AI边界"]',
        '    T2 --> F6["06-LatentSpace-大模型体感瓶颈与破局"]',
        '    T3 --> F2["02-Cloudflare-零信任身份置换实战"]',
        '    T3 --> F3["03-OpenAI-Daybreak安全大模型降本96%"]',
        '    T3 --> F4["04-Stripe-代币化计费演进困境解析"]',
        '    T3 --> F8["08-Anthropic-全模态Clef模型低成本推理"]',
        "```\n",
        "---\n",
        "## 二、根目录独立直读资产 (Standalone Direct-Access Reports)\n",
        "| 编号 | 领域分类 | 报告标题 | 核心工程价值与沉淀要点 | 独立直读文档链接 | 专题归档 |",
        "| :---: | :--- | :--- | :--- | :--- | :--- |"
    ]

    for item in standalone_items:
        standalone_filename = f"{item['seq']}-{item['domain']}-{item['title']}.md"
        topic_dir = item['topic_id']
        lines.append(
            f"| **{item['seq']}** | `{item['domain']}` | **{item['title']}** | {item['desc']} | [{standalone_filename}](./{standalone_filename}) | [专题库](./topics/{topic_dir}/) |"
        )

    lines.extend([
        "\n---\n",
        "## 三、结构化专题目录索引 (Topics Hierarchy)\n"
    ])

    for t in TOPICS_CONFIG:
        topic_id = t["id"]
        files = topics_tree.get(topic_id, [])
        lines.append(f"### 📂 [专题] [{t['name']}](./topics/{topic_id}/README.md)")
        lines.append(f"> {t['desc']}\n")
        if files:
            for f in files:
                lines.append(f"- [{f}](./topics/{topic_id}/{f})")
        else:
            lines.append("- *(暂无文档)*")
        lines.append("")

    lines.extend([
        "---\n",
        "## 四、知识库数据流向与自动化保障\n",
        "```mermaid",
        "flowchart LR",
        '    Radar["全球权威源矩阵<br/>StrangeLoop/OpenAI/Dwarkesh等"] --> Fetch["轻量极速摄取<br/>Atom探测+字幕提取"]',
        '    Fetch --> Dedup["SHA-256增量去重<br/>state_store.db 门禁"]',
        '    Dedup --> Synth["Agent 六段式深度研读<br/>Mermaid拓扑+盲区+工程载荷"]',
        '    Synth --> Output["工作区沉淀<br/>D:\\Agent视频学习录\\output\\vault"]',
        '    Output --> Sync["自动增量同步<br/>C:\\Users\\jiang\\Desktop\\开发经验\\开发者经验分析-Agent"]',
        "```\n",
        "> [!NOTE]",
        "> 本知识库所有内容均由 Agent 严格按照流水线标准化作业程序自动产出，并由 `sync_to_desktop.py` 执行强一致同步。\n"
    ])

    return "\n".join(lines)

def main():
    print(f"🚀 开始同步 Agent 开发者经验分析知识库...")
    print(f"   源目录: {SRC_DIR}")
    print(f"   目标库: {DEST_DIR}")

    ensure_dir(DEST_DIR)

    # 1. 拷贝规范文档
    spec_src = os.path.join(SRC_DIR, "开发者经验分析与Agent自动化执行规范.md")
    spec_dest = os.path.join(DEST_DIR, "开发者经验分析与Agent自动化执行规范.md")
    if os.path.exists(spec_src):
        shutil.copy2(spec_src, spec_dest)
        print(f"✅ 已同步执行规范: {os.path.basename(spec_dest)}")

    # 2. 同步 topics 专题库
    topics_tree = {}
    for t in TOPICS_CONFIG:
        topic_dest_dir = os.path.join(DEST_DIR, "topics", t["id"])
        ensure_dir(topic_dest_dir)
        topics_tree[t["id"]] = []

        # 拷贝源分类下的所有 markdown 文件
        cat_src_dir = os.path.join(VAULT_DIR, t["category_src"])
        if os.path.exists(cat_src_dir):
            for fname in os.listdir(cat_src_dir):
                if fname.endswith(".md"):
                    src_file = os.path.join(cat_src_dir, fname)
                    dest_file = os.path.join(topic_dest_dir, fname)
                    shutil.copy2(src_file, dest_file)
                    topics_tree[t["id"]].append(fname)

        # 为该专题生成 README.md 索引
        topic_readme = os.path.join(topic_dest_dir, "README.md")
        tr_lines = [
            f"# {t['name']}\n",
            f"> {t['desc']}\n",
            "---\n",
            "## 专题归档文档列表\n"
        ]
        for f in topics_tree[t["id"]]:
            tr_lines.append(f"- [{f}](./{f})")
        with open(topic_readme, "w", encoding="utf-8") as trf:
            trf.write("\n".join(tr_lines))

    # 3. 生成根目录独立直读报告
    active_standalone = []
    for item in STANDALONE_REPORTS:
        src_file = os.path.join(VAULT_DIR, item["src_rel"].replace("/", os.sep))
        standalone_name = f"{item['seq']}-{item['domain']}-{item['title']}.md"
        dest_file = os.path.join(DEST_DIR, standalone_name)

        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            active_standalone.append(item)
            print(f"✅ 生成独立直读报告: {standalone_name}")
        else:
            print(f"⚠️ 未找到源文件: {src_file}")

    # 4. 同步总看板 00-技术雷达总看板.md
    dash_src = os.path.join(VAULT_DIR, "00-技术雷达总看板.md")
    if os.path.exists(dash_src):
        shutil.copy2(dash_src, os.path.join(DEST_DIR, "00-技术雷达总看板.md"))
        print(f"✅ 同步 Dataview 总看板: 00-技术雷达总看板.md")

    # 5. 生成全局总看板 README.md
    readme_content = generate_readme(active_standalone, topics_tree)
    readme_path = os.path.join(DEST_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as rf:
        rf.write(readme_content)
    print(f"✅ 已生成知识库总看板 README.md")

    print(f"\n🎉 桌面 Agent 开发者经验库同步完成！目标路径: {DEST_DIR}\n")

if __name__ == "__main__":
    main()
