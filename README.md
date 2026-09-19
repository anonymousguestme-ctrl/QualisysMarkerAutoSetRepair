<div align="center">

# Qualisys CAST Marker Auto Set & Repair

### 用静态试次校准动态标记，自动检查错标、断线和缺点，并通过刚体关系完成补点

面向 Qualisys QTM、CAST Lower Body 和 Visual3D 的可复用 Codex Skill 与 QTM REST 工具。

中文

</div>

---

## 为什么做它

下肢步态数据的难点往往不是“有没有 28 个点”，而是这些点是否对应了正确的物理标记。

QTM 中一个点的位置看起来合理，也可能已经被赋成错误标签。错标后，点虽然还在，CAST 连线却会交叉或连接到错误位置；如果继续用这个点作为 relational 参考，错误还会被传播到后续补点。

这个项目把一套可复核的处理方法固化下来：

- 使用人工确认过的静态试次作为身份和刚体几何基准；
- 区分真正缺点、轨迹错标、跳点和错误补点；
- 检查 TH、SK 四点刚体板的六条内部距离；
- 结合前后帧连续性判断标签，而不是只看单帧距离；
- 使用同一刚体板上的可靠点执行 relational 补点；
- 检查左右颜色、CAST 连线、点数和 Visual3D 解算条件；
- measured 数据优先于 relational、插值或其他合成数据；
- 只把已有物理 marker 对应到骨性关节点，不为凑齐 28/36 点创造 marker；
- 修改前保存备份，输出到新文件，绝不覆盖、重命名或删除原始采集文件。

GitHub：<https://github.com/anonymousguestme-ctrl/QualisysMarkerAutoSetRepair>

## 它能处理什么

| 问题 | 判断方式 | 处理方式 |
| --- | --- | --- |
| 动态文件缺点 | 检查每条轨迹的 gap range 和逐帧点数 | 使用同刚体参考点 relational 补点 |
| TH/SK 点识别错误 | 对比静态六边距离、前后帧和轨迹片段 | 拆分并移动错误 trajectory part |
| 点在但连线错误 | 核对标签身份和 bone topology | 修正标签并按 marker list 重建连线 |
| 单点突然飞出 | 检查位移、速度和刚体距离突变 | 覆盖异常范围后再 relational 重建 |
| 多个点同时缺失 | 分析可靠参考点和两端锚点 | 先两参考修复一个点，再三参考修复另一个 |
| 首尾没有达到 100% | 区分边界缺点和内部缺点 | 默认裁剪分析范围，不盲目外推 |
| Visual3D 无法稳定解算 | 检查名称一致性和每段有效跟踪点 | 修复分析区间内的缺失或错标 |

> [!IMPORTANT]
> “每帧有 28 个点”不等于数据正确。28 个点全部存在但标签身份错误，仍然会产生错误连线和错误的节段姿态。

## 原始数据保护

原始采集文件优先于所有修复结果。开始处理前先生成只读清单，记录每个候选原始 trial 的完整路径、文件名、大小、修改时间和 SHA-256；trial 编号以用户确认的采集顺序为准，不能假定编号连续。

- 原始 `.qtm` 只读，所有标记、改线和补点都在副本上完成；
- 输出使用 `_corrected_measured`、`_relational` 等明确后缀；
- 清理文件时使用精确白名单，不使用通配符删除整个目录；
- `.qpr`、PAF 配置/依赖、标定文件和工程目录关系都属于受保护内容，不把它们当成“多余工程文件”删除或重建；
- 不把 `identity_normalized`、`before_fragments`、`before_relational` 等处理中间版本称为“字节级原始文件”；
- 恢复缺失文件时先按采集日期和时间排除其他实验的同名 trial，只复制到不存在的目标，并核对源/目标 SHA-256；
- 清理过程中不清空回收站。

对于 `2026-09-18/CAST - Lower body_esp32-ao-flexsensor4.5` 这次采集，用户确认的原始动态 trial 为 `1、3、4、5、6、7`。这个编号只适用于该次采集，不能套用到其他实验。

> [!CAUTION]
> “最早的处理副本”不一定是原始采集文件。如果只能找到 `identity_normalized` 等副本，必须明确报告其处理阶段，不能声称它与原文件字节完全一致。

> [!CAUTION]
> 即使 `.qtm` 仍在，删除 `data.qpr` 或相关 PAF 工程依赖也可能导致工程无法正常加载。除非已经完成字节级备份并得到明确确认，否则不得触碰这些文件。

## 工作原理

```text
人工确认的静态 CAST 试次
        │
        ├── 标签名称与左右颜色
        ├── CAST bone 连接关系
        └── 每个四点刚体板的六条基准距离
                        │
                        ▼
              动态 QTM 逐帧审计
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       缺点/gap      错标/跳点      连线错误
          │             │             │
          └─────────────┼─────────────┘
                        ▼
        轨迹连续性 + 刚体距离 + 片段边界
                        │
                        ▼
       同刚体两参考/三参考 relational 修复
                        │
                        ▼
       点数、颜色、连线、刚体误差、画面复核
                        │
                        ▼
               输出新的 QTM 修正版
```

距离匹配只用于提出候选身份。对于接近对称的四点板，不同排列可能得到相近的误差，因此最终还必须检查前后帧连续性、trajectory part 边界和 QTM 画面。

## CAST 点位约定

### 动态 28 个跟踪点

| 区域 | 标记 | 结构 |
| --- | --- | --- |
| 骨盆 | `L_IAS`, `L_IPS`, `R_IPS`, `R_IAS` | 四点骨盆跟踪组 |
| 左大腿 | `L_TH1` 至 `L_TH4` | 四点刚体板 |
| 右大腿 | `R_TH1` 至 `R_TH4` | 四点刚体板 |
| 左小腿 | `L_SK1` 至 `L_SK4` | 四点刚体板 |
| 右小腿 | `R_SK1` 至 `R_SK4` | 四点刚体板 |
| 左足 | `L_FCC`, `L_FM1`, `L_FM2`, `L_FM5` | 四个跟踪点 |
| 右足 | `R_FCC`, `R_FM1`, `R_FM2`, `R_FM5` | 四个跟踪点 |

静态文件通常包含 36 个点，因为还包括解剖定位点。动态文件保留 28 个跟踪点是正常情况。

当前项目约定左侧为青色、右侧为绿色。换项目时应先从人工确认的静态文件读取颜色，不能把该配色当作所有实验室的通用标准。

## 需要准备什么

| 项目 | 要求 | 用途 |
| --- | --- | --- |
| Qualisys QTM | 开启 Scripting REST Interface | 读取和修改当前打开的测量 |
| Python | Python 3.10 或更高版本 | 运行审计和修复脚本 |
| 静态试次 | 由用户人工检查并补全 | 作为标签和刚体几何基准 |
| 动态试次 | CAST Lower Body QTM 文件 | 待审计和修复数据 |
| Codex | 支持本地 Skill | 执行完整诊断、修复和复核流程 |

QTM REST 接口默认地址：

```text
http://127.0.0.1:7979/api/scripting/qtm
```

## 快速开始

### 1. 下载项目

```powershell
git clone https://github.com/anonymousguestme-ctrl/QualisysMarkerAutoSetRepair.git
cd QualisysMarkerAutoSetRepair
```

### 2. 安装为 Codex Skill

将仓库放到以下目录：

```text
%USERPROFILE%\.codex\skills\qualisys-cast-gap-repair
```

然后在任务中调用：

```text
$qualisys-cast-gap-repair 检查当前打开的 CAST 动态文件，在修改前先告诉我问题范围。
```

### 3. 从静态试次生成模板

在 QTM 中打开已经人工确认的静态文件，然后运行：

```powershell
py scripts\qtm_cast_tool.py capture-template `
  --output C:\QualisysWork\cast-static-template.json
```

模板记录每个标签的中位位置、四点组的六条距离、颜色和 bone 数量。

### 4. 只读审计动态试次

在 QTM 中打开动态文件：

```powershell
py scripts\qtm_cast_tool.py audit `
  --template C:\QualisysWork\cast-static-template.json `
  --include-permutations
```

审计不会修改数据，会输出：

- 当前 QTM 文件路径和是否存在未保存修改；
- label 和 bone 数量；
- 左右颜色是否符合项目约定；
- 每帧有效标记点数量；
- 每条轨迹的 gap ranges；
- 各刚体组的中位、95% 分位和最大 RMS 误差；
- 可能存在标签排列错误的帧。

### 5. 预演 relational 修复

以下命令把 QTM 界面显示的第 493 至 523 帧作为候选范围。默认 `--frame-base 1` 会转换为 API 的 492 至 522 sample：

```powershell
py scripts\qtm_cast_tool.py repair `
  --target R_TH1 `
  --start 493 --end 523 `
  --references R_TH2 R_TH3 R_TH4
```

不加 `--execute` 时只输出计划，不会写入 QTM 文件。

### 6. 确认后执行修复

```powershell
py scripts\qtm_cast_tool.py repair `
  --target R_TH1 `
  --start 493 --end 523 `
  --references R_TH2 R_TH3 R_TH4 `
  --backup C:\QualisysWork\trial-before-rth1.qtm `
  --output C:\QualisysWork\trial-rth1-fixed.qtm `
  --execute
```

工具要求 backup 和 output 都是尚不存在的新路径，避免意外覆盖文件。

## 多点重叠缺失怎么补

假设 `R_TH1` 和 `R_TH3` 同时异常，但 `R_TH2` 和 `R_TH4` 可靠：

```text
第一步：R_TH3 ← relational(R_TH2, R_TH4)
第二步：R_TH1 ← relational(R_TH2, 修复后的 R_TH3, R_TH4)
第三步：重新检查六条刚体距离、两个边界和 QTM 连线
```

不能直接让两个错误点互相作为参考。每完成一步都应重新审计，再执行下一步。

## 刚体误差怎么判断

对四点刚体板计算六条边相对于静态模板的误差：

```text
error_ij = dynamic_distance_ij - static_distance_ij
RMS = sqrt(sum(error_ij^2) / 6)
```

本项目可使用以下范围作为初步筛查：

| RMS | 初步判断 |
| ---: | --- |
| `<= 3 mm` | 刚体关系较强 |
| `3-5 mm` | 需要结合画面和连续性复核 |
| `> 5 mm` | 可疑，检查跳点、错标或软组织移动 |

这些不是所有采集条件下的硬阈值。最终阈值应结合静态数据本身的波动、标记固定情况和相机重建质量。

## Visual3D 前检查

- 静态试次标签完整且稳定；
- 动态 28 个 tracking marker 名称与静态一致；
- 分析区间内没有未处理的身份交换；
- 每个 TH/SK 刚体段至少有三个不共线的有效跟踪点；
- 中间缺点已可靠修复，或从分析区间排除；
- 首尾缺点没有为了达到 100% 而被不合理外推；
- QTM 中左右颜色、CAST 连线和实际身体侧一致。

> [!NOTE]
> Visual3D 导入不要求所有轨迹在每一帧都达到 100%。分析区间内的身份正确性和每个节段的有效几何约束，比首尾填满更重要。

## 数据安全

- 默认命令为只读审计；
- 只有 `repair --execute` 才会修改当前打开的测量；
- target 与 references 必须属于同一个 CAST cluster；
- 修复区间两侧必须存在可靠的目标点锚点；
- 执行时必须提供独立 backup 和 output；
- 工具拒绝覆盖已经存在的模板、备份或输出文件；
- `.gitignore` 排除了 QTM、C3D、TRC、STO 和常见报告文件，避免误上传受试者数据。

> [!CAUTION]
> QTM relational fill 会覆盖指定范围内的全部 sample，包括原本存在的 measured sample。只有确认该范围属于错误数据后才能执行。

## 项目结构

```text
SKILL.md                       Codex Skill 入口与强制规则
agents/openai.yaml             Skill 的显示名称和默认提示词
references/marker-set.md       CAST 28/36 点、颜色和刚体定义
references/workflow.md         标签诊断、补点顺序和验证流程
references/qtm-api.md          QTM REST 方法、帧号和命令示例
scripts/qtm_cast_tool.py       静态模板、只读审计和定点修复工具
.gitignore                     排除采集数据和本地输出
LICENSE                        MIT License
```

## 开发检查

```powershell
py -m py_compile .\scripts\qtm_cast_tool.py
py .\scripts\qtm_cast_tool.py --help
```

Skill 结构可以使用 Codex 自带的 `skill-creator` 校验器检查。

## 故障排查

### 提示 “Open a QTM measurement”

先启动 QTM 并打开一个 `.qtm` 测量文件。仅打开 Project Data Tree、但没有打开测量，不算有效状态。

### 无法连接 `127.0.0.1:7979`

确认 QTM 正在运行，并在项目设置中启用了 Scripting REST Interface。检查端口是否被防火墙或其他程序占用。

### 点数是 28，但连线仍然错误

这是标签身份问题，不是缺点问题。检查刚体 permutation、轨迹 part 边界和 bone topology，不要继续填点。

### relational 补点后形状还是不对

至少一个 reference 可能也是错误点。回到异常前后的可靠帧，先修复参考点，再修复依赖它的目标点。

### 修复范围比用户指出的帧更早

用户通常在错误变明显时才看到问题。应通过位移、速度和刚体距离向前追踪真实起点，并明确说明 QTM 显示帧与 API sample 的差异。

### 首尾仍有少量缺点

默认不外推边界。若缺点不在分析窗口内，可在 Visual3D 中裁剪；只有下游确实需要这些帧时才考虑有依据的外推。

## 当前限制

- 默认 marker 配置只适用于本仓库记录的 CAST Lower Body；
- 颜色值是当前项目约定，不是全局 Qualisys 标准；
- 距离匹配无法单独解决近似对称板的身份歧义；
- 工具不会自动判断所有 trajectory fragment 的物理身份；
- 最终结果仍需要在 QTM 中检查关键帧和连线；
- 不包含 Visual3D 模型构建或动力学计算。

## License

本项目使用 [MIT License](LICENSE)。
