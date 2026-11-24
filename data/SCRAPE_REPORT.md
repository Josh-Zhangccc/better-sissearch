# SIS 2026-27 Term 2 课程数据抓取报告

- **学期**：2026-27 Term 2（strm `2620`）
- **数据源**：sis.cuhk.edu.cn Class Search（只读；connector `cuhksz-cli` 的 `sis` 后端）
- **生成时间**：2026-11-23
- **输出**：`data/courses.json`（`term` / `count` / `courses` / `subjects`）

## 1. 总量

| 指标 | 数值 |
|---|---:|
| 课程数（`count`，去重后的课程号） | **498** |
| section 数（class 行，4 位 class number） | **1574** |
| 覆盖 subject 数 | **53 / 115** |
| 空 subject（SIS 返回 0 门 open 课） | 62 |
| 失败 subject | **0** |
| 分桶不可达桶（unreachable） | **0** |
| 重复 class number | **0** |
| 带上课时间的 section | 1524 / 1574（其余为 RSC/THE/PRA 等无固定时间） |

section 类型分布：LEC 824 · TUT 664 · SUP 29 · LAB 23 · PRA 15 · RSC 14 · IND 3 · EXM 1 · THE 1。

> 注：任务描述里的「116 个 subject」与页面下拉不一致——实测下拉选项为 **115 个**（全部为纯字母代码，无被 `isalpha()` 过滤掉的项），本报告以 115 为准。

## 2. 关于验收标准「count > 1000」

**该项未达成，且已确认不是分桶漏课。** 证据链：

1. `count` 统计的是**去重课程号**（与旧 `data/courses.json` 的 `count=98` 口径一致）。本轮 498 个课程号对应 1574 个 class（section）。若按 SIS 的「50 classes」口径（class = 课程-分节行），总量是 **1574 > 1000**。
2. `open_only` 只能传 `True`：把隐藏字段 `SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$3` 改成 `N`（或去掉复选框）时，SIS 会直接退回 `SSR_CLSRCH_ENTRY` 入口页、不返回结果——与任务里「open_only=False 返回空」的实测一致。因此本抓取只能拿到 **当前 open 的班级**。
3. 62 个空 subject 是 SIS 的真实返回（subject-only 查询 0 门、无 notice）。其中 **24 个在 2026-27 Term 1 有课**（AIR/AIS/BSC/CBH/CIE/EPB/FEX/GEW/GGE/IBA/ICS/LAW/LIN/LSC/MBI/MBM/MCE/MDS/MES/MFE/MFM/PUB/SUD/URB），另外 38 个两个学期都没有（多为交换/语言/未开设代码）。说明空列表是**学期开课差异**，不是抓取失败。
4. Term 2 选课预约期为 **2026-11-23 ~ 11-25**（抓取当天开放），课表已发布，open 集合即当前可选集合。
5. 独立完整性验证（见第 4 节）显示所有可验证桶 **missing = 0**，无漏课。

## 3. 各 subject 明细

| Subject | Courses | Sections |
|---|---:|---:|
| MAT | 26 | 159 |
| ENG | 8 | 143 |
| MED | 12 | 73 |
| PHY | 30 | 67 |
| CSC | 17 | 64 |
| MUS | 56 | 63 |
| FIN | 8 | 61 |
| PED | 20 | 60 |
| ECO | 15 | 56 |
| GEC | 20 | 51 |
| ACT | 14 | 48 |
| DDA | 17 | 46 |
| GFH | 1 | 46 |
| GEA | 1 | 43 |
| GFN | 1 | 42 |
| GED | 13 | 39 |
| AIE | 12 | 38 |
| ECE | 12 | 38 |
| GEB | 13 | 37 |
| STA | 11 | 36 |
| CEC | 3 | 30 |
| CHI | 6 | 29 |
| BIO | 17 | 27 |
| MGT | 15 | 23 |
| PSY | 15 | 21 |
| BME | 11 | 18 |
| CHM | 10 | 18 |
| MKT | 11 | 16 |
| MSE | 9 | 15 |
| DAI | 1 | 14 |
| MIS | 3 | 14 |
| TRA | 7 | 13 |
| CLC | 5 | 11 |
| ENB | 10 | 11 |
| ENE | 7 | 11 |
| URM | 11 | 11 |
| BIM | 5 | 9 |
| DMS | 3 | 9 |
| HSS | 5 | 9 |
| PHM | 7 | 9 |
| FMA | 2 | 8 |
| GLB | 7 | 7 |
| ERG | 6 | 6 |
| BMA | 2 | 4 |
| FRN | 1 | 4 |
| JPN | 1 | 4 |
| LIT | 3 | 3 |
| CSS | 1 | 2 |
| DME | 1 | 2 |
| IDE | 2 | 2 |
| KOR | 2 | 2 |
| ITE | 1 | 1 |
| SPN | 1 | 1 |
| **合计** | **498** | **1574** |

## 4. 完整性验证

两类独立校验（脚本 `verify.py` / `verify2.py`）：

**(a) component 并集校验**（对 10 个超限 subject）。每个 class 恰好属于一个 component，所以「逐 component 求和」在不超 50 时就是精确真值：

- CSC 64/64、ECO 56/56、FIN 61/61、GEC 51/51、PHY 67/67 — **完全一致**
- ENG / MAT / MED / MUS / PED 的 LEC 或 TUT 单 component 仍超 50（无法整体校验），但其**可验证 component 全部 missing = 0**

**(b) 逐课程校验**（对上列 day 分桶的 component）。单门课一般 < 50 class，可用 `catalog = <号>` + component 精确取全：

- ENG-LEC 7 门、MAT-TUT 24 门、MED-TUT 8 门、MUS-LEC 51 门、PED-LEC 20 门、PHY-LEC 21 门
- 结果：**missing = 0 / extra = 0**（0 门不一致）
- 唯一不可单独校验的是 ENG 1002（单课 62 个 LEC sections > 50）；其 section 标签连续 L01–L62、class number 1048–1109 连续，可视为完整

**与既有数据的回归**：旧 `data/courses.json` 的 9 个 subject（AIE/ECE/CHI/MGT/BIO/GEA/GED/STA/MKT）在本次结果中合计 **98 门**，与旧文件 `count=98` 完全一致。

**抽查**：MAT 3004（Abstract Algebra I，2 sections）存在；CSC 17 门；MAT 1002 共 50 sections（10 LEC + 40 TUT）；ENG 2002B 21、ENG 2002S 41 sections。

## 5. 空 subject 列表（62）

```
ACM AIR AIS AIT ART BGE BSC CBH CIE CLCC DUM EIE ENL EPB EXFE EXGA EXGB EXGBE
EXGBI EXGC EXGD EXGSCLM EXME EXNE EXSE FEMBA FEX FREN FTE GBI GER GERM GEW GGE
GNB HKSL HST IBA ICS IEG IER JAP KORE LAW LIN LSC MAN MBI MBM MCE MDS MES MFE
MFM PHI PUB RMS SFL SPAN SSE SUD URB
```
其中 24 个在 Term 1 有开课（见第 2 节），38 个两学期均无（`data/empty_subject_t1.json`）。

## 6. 方法与实现要点

`scrape.py` 的 `collect()` 无法直接用于真实超限 subject：`[0,0]` 会无限递归（`catalog >= 0` 恒等于全量），且不处理「单门课 > 50 class」。本项目新增（未改动 `connectors/cuhksz-cli`、未动 `index.html`）：

- **`sissearch.py`**：两段式 AJAX Class Search 封装 + Additional Search Criteria（component / units / campus / location / instruct mode / day）+ View All Sections 展开 + 多日时间解析（`TuTh 10:30AM` → 拆成 Tu、Th 两个 meeting，符合 `index.html` 的 `Mo…Su` 单日模型）。
- **`scrape_full.py`**：分桶算法
  1. 先用 `greater than or equal to`(G) / `less than or equal to`(T) 双边数值二分：`G(lo) − G(hi+1)` 或 `T(hi) − T(lo−1)`；
  2. 两端都超限时，按「每班恰取一个值」的维度切分（component → units → campus → location → mode → day），day 最后兜底（跨天重复按 class number 合并）；
  3. 单门课仍超 50（如 MAT 1002、ENG 1002）由维度切分解决；
  4. 只保留的课程行才做 View All Sections 展开（SIS 默认只渲染前 3 节）。

踩到的 SIS 坑（已在代码中处理）：

1. **状态漂移**：做过 View All Sections 后，复用旧的 `win0` 表单快照会让后续查询**静默丢弃 Additional Criteria**。修复：展开后标记 dirty，下一次查询前重新 GET 入口页。
2. **展开时序**：展开用的是「最后一次请求」的 payload/状态；若先查 G(lo) 再查 G(hi+1)，用 G(lo) 的旧状态展开会失败（ENG 2002B/2002S 曾因此少 50 个 section）。修复：先查被排除的边界，再查要保留的边界。
3. `career` 字段只要显式传 `UGCU`/`PGCU` 就返回 0，必须留空（与 connector 注释一致）。
4. `catalog` 的 G/T 是**数值**比较（不是字典序），因此可以用数值区间二分；`contains` 是子串匹配，无法当区间用。

## 7. 复现

```bash
cd /home/april/repo/projects/better-sissearch
/home/april/repo/connectors/cuhksz-cli/.venv/bin/python scrape_full.py            # 全量，逐 subject 缓存到 data/parts/
/home/april/repo/connectors/cuhksz-cli/.venv/bin/python scrape_full.py --only MAT # 单科
/home/april/repo/connectors/cuhksz-cli/.venv/bin/python verify.py                 # component 并集校验
/home/april/repo/connectors/cuhksz-cli/.venv/bin/python verify2.py                # 逐课程校验
```

`data/parts/<SUBJECT>.json` 是逐科原始行缓存（断点续跑）；删除对应文件即可重抓该科。

## 8. 失败清单

无。10 个超限 subject 全部分桶成功，`failures=[]`、`unreachable=[]`。
