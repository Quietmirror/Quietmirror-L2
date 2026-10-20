# L2-r4 source revisions and rechecks

Status: CAD checks running. No L2-r4 Release is permitted until all CAD gates complete.

## Candidate 1

- Adopted the supplied execute-all plan and author evidence at f637118455159515a200e6e0f35c0eea1c7d1633 (descendant of the document reference 54dac615).
- D1-D6 are integrated into the BODY source generation sequence; the finished r3 BODY is not imported for boolean patching.
- D7 removes the remote tabs, moves hinges, scales the pads, and recalculates the 0.60 mm stop travel.
- The specified ear starts at Z19.85 but the hinge ends at Z19.5. Added a concealed root bridge joining the ear to the existing web; geometric and movement checks must pass before acceptance.
- A local outward stop land uses the entry slot allowance so the specified 1.0 mm slot does not inadvertently allow more than 0.5 degree outward play.
- Heavy processing runs on an isolated public GitHub runner. Each FEM solve must observe at least 10 GB available RAM and use default SPOOLES; no reduced mesh or omitted cases is allowed.

## Candidate 1 tool corrections

- CalculiX 2.21 version probe returns 201 despite printing its version; only this known probe response is accepted. Actual solver failures still fail the build.
- BODY and four new side parts passed STEP single-solid/valid round-trip; the first run stopped while measuring STL connected components because trimesh split implicitly invoked hole repair and required networkx. Changed component counting to scipy face-adjacency connected components, with no implicit mesh repair or hole filling. Final conforming Gmsh surface meshes are still required.

## Candidate 2 - pad sweep correction

- Independent rigid rotation of candidate 1 gave SF stop 7.24418094 degrees / 0.42158968 mm lateral slip; SR 6.75542490 degrees / 0.33405655 mm slip. Centered diameter 2.6 pads do not fully cover diameter 2.0 buttons at the endpoints. This is a CAD failure, not a hardware-pending item.
- Keep both pad diameters and key outlines; offset only crown centers in Y by SF +0.2018 mm and SR -0.1617 mm. Recomputed stops are +6.936485 / -6.540994 degrees. Conservative projected coverage margins are +0.08865 / +0.12981 mm at the endpoints. Actual final-part assembly and motion checks must still run.
- Trimesh's scipy component counter requires a NumPy array for explicit node IDs; corrected the range argument. No mesh repair is performed.
- Superseded work-branch CI jobs may be cancelled; only final candidate results count. This does not omit any required final mesh or load case.

## Candidate 2 measured outcome (source 59366156, results 013d5c78)

- Nine printable BReps passed single-solid validity and self-interference checks. All nine STL meshes are closed, consistently wound, and connected. Five newly generated meshes used conforming Gmsh triangulation without filling holes. BODY volume: 12644.254639 mm3. H STEP contains 92 independent components.
- Normal side-key presses through their respective stops had no intersections above 0.001 mm3. The forced extra 0.3-degree poses penetrate the intended inward stop (0.00556 / 0.00650 mm3); this is an intentionally blocked pose, not a physically permitted extra motion.
- Straight cap insertion FAILED: SF maximum 0.114403 mm3, SR maximum 0.140351 mm3, around the flat barrel end at Z15.5 and the rounded aperture corners. Merely fitting its Y bounds inside the rectangular aperture does not prove insertion.
- Outward limiting was not proved: both keys remained clear at 0.5 degree outward. The specified high +X stop arm/land does not fit the curved mother profile as assumed.
- Pad coverage correction passed the independent 101-pose conservative projected-rim calculation; minimum positive margins SF 0.088647 and SR 0.129808 mm.
- Retainer route execution stopped before geometry on an input UTF-8 BOM; updated input decoding to utf-8-sig. No route success was claimed.

## Candidate 3 - local interface corrections requiring complete recheck

- Keep the cap outside surface, side aperture outline, hinge axes, pad diameters, five feet and base interfaces. Shorten only the round hinge journal to Z16.4–18.6 (2.2 mm), retaining diameter 2.5 / bore 1.05 and both stationary steel-pin supports. This addresses the measured barrel/corner insertion clash without opening a larger visible hole.
- Reorient the radial outward stop arm inward: X26.7–29.0, Z18.6–19.5, width 0.8. Add its inboard stop and roof connection to the BODY source. This replaces the high +X ear and its external slot; the complete upper bearing remains intact. This is an explicit source correction to D7, not a claim that the original dimensions passed.
- Original retainer pilot radius 0.85 exceeded the SF edge distance 0.60, so the self-tapping hole broke out. New screw coordinates: SF (16.6,45.7), SR (16.6,70.4); round bosses radius 1.8, height 3.5, matching integrated floor pods radius 2.05. SF is between terminal rows. Retain diameter 1.7, depth 3.0 pilots. Update drivers, screws, assembly and stress checks together.
- Add two reference washers, OD3.6 / ID2.2 / thickness0.5. M2x5 shanks now start Z11.6 and end Z16.6; heads bear through washers onto the Z12.1 floor. The previous screw heads floated below the floor.
- Keep diameter1.5 x1.0 integral locating pins. Add an upper entry pocket Z13.0–13.7, leaving the lower 0.3 mm locating socket; enlarge terminal slots to Z15.6–17.2. Retainer routes use a 0.55 mm elevated approach, followed by aligned vertical seating. These changes still require actual voxel and BRep route tests.
- Side GPIO routes terminate at the side of the existing RF_IO_HEADER_EST instead of inside MCU_RADIO_EST; all route clearances remain subject to final checks.
- The CI now exposes each script as a separate job step. G6 cap translation computes exact overlap volume with PET installed, as requested; no unnecessary global-distance claim is made for these insertion poses. G5 still measures exact distances.


## Post-candidate-3 audit preparation

- Added source-feature contact decomposition for D7: whole key intersection remains checked; only the named inward rib/post and outward ear/stop are functional contacts. The rest retains 0.30 mm clearance.
- Main/wheel motion includes fixed H hardware and cables. Broad-phase bounds may prune impossible candidates only after an exact nearest distance is known; bounds are not returned as exact gaps.
- Appendix B root-load selection is explicitly Y35.5..42.5. The preserved author helper derives Y35..42 from the old root_y=38 parameter. The executable checks now follow the written interval; comparisons must disclose this difference and investigate any >3% discrepancy.
- Real slicing uses organic, build-plate-only support, all nine individual part slices, plus the complete 255x155 plate at scale1.0; no machine-certified G-code is supplied. Native FreeCAD output must be saved and reopened, and the full assembly STEP reimported. These are prepared steps, not yet passed results.
- Each future completed CI stage saves a work-branch checkpoint; this creates public candidate evidence, never a Release or automatic acceptance.


## Candidate 3 actual outcome (results df1c330a)

- All nine printable solids remain valid, connected, closed and self-interference-check valid. BODY volume 12677.681279 mm3. Both cap plus PET straight-insertion tests pass with maximum intersection exactly 0 mm3. The outward stops block the -/+0.5 degree diagnostic poses. Normal side motion full overlap stays below 0.001 mm3.
- SR switch route passes the voxel and exact waypoint checks. SF switch route fails because the preserved author obstacle model omitted installed SR terminals; actual terminal geometry collides. Both retainer approaches reach their final alignment, but SF locating pin overlaps the raised switch back by 0.050583 mm3 before descending.
- Both new driver corridors fail: BODY intersection 18.354724 / 0.649293 mm3. All three reserved-volume tests have no invasions above 0.001 mm3. Inherited main keys overlap the free plunger envelopes by 0.014574 mm3 each at rest.

## Candidate 4 corrections and required rechecks

- Shift only SF locating pin/hole from X17.9 to17.4, keeping diameter1.5/1.6, length1.0 and Y54. Update stress anchors with the same source parameter.
- Cut explicit radius2.05 screwdriver paths up to Z12.1; leave floor and washer contact faces intact. Recheck BODY validity, access, stiffness and all affected interfaces.
- Remove inherited main-key rib/plunger overlap with R1.13 spherical clearance around the modeled R1.10 plunger; preserve key exterior, width and actuation datum. Expand rigid-housing relief through the requested -0.5..3.1 degree range. Re-cut only main/wheel stop faces at requested 3.1/4.4 degrees.
- Plan a replacement SF route with actual SR terminals included, 0.25mm part point clouds, finite yaw samples and conservative 26-neighbor dilation. Search success is only a candidate route; replay and exact turning-point acceptance are mandatory. Retainer final alignment/descent is separately classified as seating, not an open-clearance route.

## Candidate 5 - measured hidden-hinge containment repair

- Candidate4 actual mother-profile subtraction found SF/SR upper fixed-lug material outside the mother surface by 2.214577/2.096916 mm3, and steel-pin material outside by0.068486/0.031634 mm3. The proposed X29 axes cannot satisfy the document's hidden-bearing requirement at the upper Z range.
- Parameterize both hinge X coordinates and move them to27.5, keeping Y45.3/69.7 and the complete external key surface. Upper fixed lug is Z19.8..20.6, lower lug unchanged. Clip fixed bearing additions to the actual mother surface. Keep diameter2.5 moving journals and diameter1x5.5 steel pins.
- Shorten only the concealed inboard ear radius2.3 to2.1 and place the outward stop riser X26.0..26.8 so both estimated micro housings retain space. The stop roof remains below the mother surface. This is a disclosed correction to the literal D7 coordinates, not a claim that those original dimensions passed.
- Recompute stop angles, pad coverage, source masks, pin access and rendering from hinge_x; all affected final gates must be rerun. No result is inferred from these source edits alone.

## Candidate4 assembly replay result and route correction

- Both retainer routes and SR micro route passed exact and voxel checks. The SF path had no voxel hits but many exact gaps below0.25mm (smallest0.023553mm); therefore it FAILED G6 despite zero solid intersection.
- Increase planner obstacle dilation from one to two26-neighbour0.25mm layers. Start lower and target an elevated/pre-alignment pose0.5mm forward of the divider; retain exact waypoint and final seating tests. This is added search margin, not a substituted acceptance criterion.
- Export named construction mating features for local contact checks. Clearance collars at continuous feature seams are recorded; all whole-solid intersections remain measured.
- Fixed side pin bores use diameter1.05 as required by the document; the old0.95mm press-fit reference would intentionally intersect a1mm cylinder and is removed from the current source. Real printed fit and retention remain hardware tests.
- Wire tube end spheres are trimmed only inside declared local termination balls at their matching connectors/COM junction. Mid-route geometry remains unchanged and must retain0.2mm clearance.

## Candidate5 measured outcome and candidate6 correction

- Exact containment now gives0mm3 outside the mother surface for both fixed hinge regions, both concealed moving ears, and both steel pins. Straight cap+PET insertion and diameter2 pin tool access pass.
- End-press intersections remain: SF0.227701/SR0.220540mm3, localized at the far cap corners inside the middle divider (SF Y56.088..56.748, SR Y57.659..58.311). These are real nonfunctional collisions, not stop contact.
- Keep cap exterior dimensions. Add source-defined backside clearance inside the middle divider, retaining the outer0.8mm X-offset lip; enlarge only each existing aperture's far end0.15mm. No extra hole is added. Recheck full movement, local wall geometry, window changes and final stiffness; the thin local aperture lip is explicitly distinguished from ordinary shell thickness.

## Candidate6 route and reference investigation checkpoint

- Geometry source85481b87332f9a698dcda3beb64891eac9f95741, checkpoint29842da7fb5bd076e532d9aa057b36984dde2b07: all four loose-part routes pass. Replay includes157 SR-switch,350 SF-switch,123 SR-retainer and206 SF-retainer poses; exact turning-point and seating checks also pass. The new SF route includes installed SR terminals.
- R3.2 reference run39243764463 completed12 serial SPOOLES solves across all three meshes. Written root interval35.5..42.5 increases coarse-grid stiffness by3.78%/3.27% versus the published table. Replaying the author's35..42 interval reproduces the coarse values within0.058%. Final G8 uses the written interval and the larger of the independently recomputed written baseline and the published baseline. Every>3% final-author discrepancy still requires investigation.
- Complete candidate verification reuses the exact saved C6 component bytes, without bootstrap overwriting the relieved main keys or trimmed wires. New report identity records bind geometry and verifier sources to results across CAD, FEM and Windows artifact phases. No CAD-complete status or Release is inferred from workflow success.

## Candidate6 full side-motion findings and candidate7 key-only correction

- Full33-pose side checks found zero unexplained overlap and all other-component clearances passed. However, both journals touched the underside of the fixed outward stop atZ18.6. SR ear clearance fell to0.263855mm at its physical stop and0.258083mm at the extra diagnostic pose. Therefore C6 side G5 failed despite no penetrations.
- C7 changes only generated key internals: journal top18.6 to18.25 (diameter2.5, bore1.05 and bottom16.4 retained); ear top19.5 to19.35; concealed bridge starts18.1 so it positively joins the shortened journal. The outer contact skin, BODY, fixed lugs, pins, electronics, floor and foot datums stay identical. Recheck full motion, cap insertion, key validity/mesh and affected assembly data. No pass inferred from dimensions alone.

## Candidate7 and8 measured local results; candidate9 corrections

- C7 removed the journal/stop contact and raised SR ear clearance above0.35mm. The new nearest surfaces exposed rod-to-aperture floor0.20mm, SF cap/post0.14249mm at physical stop and SR cap/divider0.15672mm. These remained failures, not allowed contacts.
- C8 reduced the concealed rod radius1.20 to1.05mm, shortened SR front edge58.10 to58.35, and relieved SF inner skin near its upper stop. Its nine-pose development test passed both keys at rest but still found curved far-corner/floor gaps below0.30mm. The development test was not promoted to G5.
- C9 retains the exact C6 BODY, fixed pin locations and stop angles. Exposed cap limits become SF Y44.30..56.05, SR Y58.35..70.70, Z15.65..19.45. Original BODY aperture dimensions are stored independently. Both cap inner skins receive one simple pocket enclosing the source-defined upper-post clearance sweep, with the intended stop rib restored separately. This is a small disclosed perimeter reduction, not a claim that the earlier cap outline passed. Rod radius1.05, hinge diameter2.5 and bore1.05 remain.
- Exact C7 wire checks found sensor-line gaps0.05/0.15mm to two boards, USB-line0.15mm to a header away from its termination, and two side-wire gaps0.10mm. R4-only route overrides shift the sensor outer segmentX13.65 to13.85 and low endZ16.15 to16.25; USB upper traverseZ22.30 to22.40; SR-NO segmentX14.30 to14.50. COM branch departure is raised0.30mm. Historical electronics.json is retained; all new segments require fresh G3 and hardware-intersection checks.

## Execution and print diagnostics

- Run39246099870 completed all18 final-BODY solves and same-mesh root interval investigations. Its last Git push failed remotely, so no final aggregate and no S7 run were claimed. ci_checkpoint now retries a failed fast-forward push and can resume an already-committed unsent checkpoint without overwriting an unrelated source update.
- Run39250371699 reruns all18 cases and adds the author-V2 geometric control before S7, serially. The numerical final-BODY values reproduced exactly. At2.4/2.0mm the control squeeze stiffness920.897515/923.889716 reproduces the author922.03/923.32 within−0.1228%/+0.0617%, supporting a geometric explanation for the final8–9% reduction. Fine-grid and final S7 results remain in their actual reports.
- FreeCAD1.1.4 saved/reopened94 valid independent components and reimported the full STEP. PrusaSlicer preparation initially lacked networkx; that dependency was added. The next run exported/reopened the nine-object3MF but the slicing engine exited3221225477. This is a failed real slice, not a mass estimate. Per-part isolation and actual engine-log retention were added before changing geometry or printing settings.
- Battery single-axis searches exhausted finite reachable sets (Y306 states, X453; finerY top/bottom8829). Exact local tests showed feasible small pitch/translation combinations, but no complete service route was claimed. A coupled pitch/yaw search now explores the existing windows with the same cell dimensions and retained frame, followed by exact per-pose0.5mm clearance. Search failure is retained rather than relabeled hardware pending.

## C9 finite checks, fixed-area S7 and slicer correction

- C9 nine-pose local side clearance probe passed both caps, including ordinary 0.30 mm non-contact regions. Full 33-pose checks with the remaining hardware are a separate required result and were still running at this checkpoint.
- G8 final aggregate reached COMPLETED: 18/18 cases pass, minimum ratio1.071705219. Author-V2 squeeze controls at2.4/2.0/1.6 reproduce the source table within−0.1228%/+0.0617%/−0.0616%; the remaining8.3–8.9% final squeeze reduction is geometric. Source interval investigation resolves the root-load deviations.
- Initial S7 stopped before the1.6mm solve: the inherited generic selected_load requires at least1mm2, while the specified stop patch is only1.2x0.5=0.6mm2. Earlier centroid-selected coarse meshes overestimated that patch. Added exact planar triangle clipping and quadratic consistent nodal traction for this patch, with independent5N force/moment and0.6mm2 area checks. No stress threshold or force was relaxed. All12 rerun S7 cases now pass; maximum globalP95=1.939979MPa. This is equivalent linear traction, not nonlinear contact certification.
- Nine individual Prusa2.9.6 slices passed. Repositioning the formal plate to leave room for the measured organic-support footprints and loading the identical explicit profile fixed the whole-plate export. C9 actual formal plate:36.10g,5h18m39s; the F2 trial was separately respaced after its previous log reported intersecting retainer paths. Final F2/native status remains tied to its own report.
- The first C9 matrix checkout lacked three config JSONs inherited only on the earlier main work branch. The jobs failed before numerical checks; complete current source/configuration has now been published to an independent validation branch. This was an execution packaging error, not a geometry result.
- Full rigid battery search now tests all six motion degrees and both top/bottom approaches. Approximate distance-field planning is only a proposal; exact BRep0.5mm checks at every dense replay pose are still mandatory. No battery dimension or acceptance threshold has been reduced.
- Cross-platform source identity may differ only by CRLF or final blank lines. Such equivalence requires the exact original producer source bytes saved as a digest-checked snapshot; normalized text must match completely. Changed code and changed geometry still invalidate evidence.


### C10：推杆和 PET 背衬交界修剪

C9 全部 672 项线束检查通过，765 项打印件/硬件相交检查仅 SF 键帽对其 PET 膜剩余 0.003832615 mm³ 相交。偏置球冠与推杆前端相交后，在球面背衬之外留下一小片推杆材料。源码生成步骤在 rod_end+0.40 到 +0.50 mm 区间只切去球面外的月牙状材料，保持球冠接触面和接触尺寸。修正同时用于正常键帽和 F2 样件；完整重建脚本加入该精修步骤。BODY、挡板、孔位、脚贴和电子布局均不改动。所有受影响的帽件、运动、干涉、原生装配和切片检查须重新取得结果。

### 跨平台证据字节布局

合并 Windows 产物时发现 Git 在提交时将 CRLF 转为 LF，而运行时证据记录的是原始 CRLF。已用原记录的 SHA-256 逐项验证还原后的字节：数值、STEP 实体数据和所有非换行字节完全不变；二进制文件不使用换行转换。最终校验保留原始生产者哈希，仅允许哈希可以验证的 LF/CRLF 形式。少数手动提交的源码末尾空行差异另保存原始生产者源码快照，禁止把真实代码/几何变动当作换行差异。

### 图像复核

已目视核对 C9 六视图拼图、俯视、右视、底视、等轴测、内部骨架、Z16.6剖面和真实单盘位置图。图示均来自实际 CAD；五脚和内部结构可见，九件排盘有清晰间距。图像检查不替代精确干涉检查。最终几何确定后按产物身份再生成相应视图。

### C11/C12：真实拓扑与滚轮全组净空修正

- C10 的后侧键虽为有效单实体、闭合网格，BOPAlgo 仍检出真实 Edge/Face 自相交：Y70.25 附近的铰链连接筋与圆角交界。错误不是小边阈值，也不能用网格检查通过代替。C12 源码把铰链连接筋外端内收0.4mm，保持外侧皮面。两帽 STEP 回读、BRep 自相交、PET 相交检查均通过；完整运动检查另行保留。
- 推杆直接从球冠背衬内开始生成，避免在成品帽上修剪；C11 单改推杆未消除后帽自相交，因此保留失败证据，不能把该尝试写成修复成功。
- 滚轮载架极限姿态发现编码器参考 PCB 边缘、端子尾部、主键钢销的非功能净空不足。提案调整自制转接板外形、端子尾长与两侧钢销内端，保持 BODY、轮轴、编码器本体基准和主键轮廓。转接板是新板形假设，不允许把它理解成可裁剪实际供体主板。端子焊接尺寸仍需实物确认。
- 完整滚轮扫掠又发现中间角度载架靠近主键微动螺钉；C12 在源码中加入45个设计姿态对应的0.32mm局部避让。独立23姿态验收标准仍为0.3mm，不能由设计切削包络替代验收。
- 同一最终 BODY 的 G8 18/18 结果继续保留。S7 的依赖源码随侧键生成更新，将按最终源码重新绑定或复算，不把旧报告直接当成新版本验收。

### 电池服务路径仍未闭合，备选包络独立测试

原18x22x6mm估计包络在多种姿态搜索和原尺寸布局搜索中尚未得到精确0.5mm通过的拆装路线。新增14x28x6、12x33x6、16x25x6mm三个体积接近的估计包络，仅作为独立候选；未验证前不替换正式 H 装配。先检查固定布局和整体母面包含，再检查密集路线的精确 BRep 距离。体积相近不代表容量相近，不作12h续航达标声明，也不把未通过的 CAD 项转成实物待测。

### 独立检查执行修正

六个窗口任务第一次缺少还原的 R3.2 基准文件，在开始数值计算前退出；已在每个任务前加入 restore_inputs。BODY 未变，仍各自执行200边界点、1000棱柱点和额外1000顶壳点检查。滚轮生成中的一次同类基准路径缺失也已修复，失败运行记录保留。

### C12 实测结果与 C13/C14 修正（均非发布声明）

- C12 九件打印几何均通过有效单实体、闭合网格及 BRep 自相交检查；MeshLab 九件自交面数均为0。两侧键各33姿态通过；四件散件装入路线分别157/350/123/206姿态通过。672项线束检查、765项打印件对硬件相交检查通过，硬件之间无超限相交，预留区无超限侵入。
- C12 完整滚轮诊断仍显示编码器 PCB 外角在+4.1°间隙0.049346mm、+4.4°接触。C13 把X>8.6区域限制为以(8.5,26.1)为心的R2.1圆形安装台，保持原R1.1孔与板厚；是新设计的转接板轮廓，不是裁切供体的指令。完整扫掠仍须通过。
- C12 局部功能配合复核保留三项真实失败：SR挡板前缘对中央隔板0间隙；SF挡板端子槽附近残余凸台到端子0.35mm（要求0.5）；编码器后金属固定脚到载架上升筋0.146544mm（要求0.3）。C14 直接修模型：端子槽半宽0.97、Z15.6..17.35；SR前缘Y55.3..56.05的X内面改到18.65（局部厚1.35）；载架仅在焊脚上方相邻筋处留0.32mm避让。未把这些非接触区域归入功能例外。BODY与五脚不变。挡板几何变动后S7和装入路线必须重跑。
- 最新一次与C12源码绑定的S7为12/12，最大P95=1.939979MPa；该结果是C12，不能代替C14挡板复核。

### 窗口定义的独立核对

最初按源二维多边形边界投影到外顶面，四个前中窗口通过，两个后窗在Y80.368附近出现占用，且原R3.2在完全相同位置也占用。原因是源窗口从Z11.34起切，而尾部外顶面已低至Z10.68..11.33：那里没有实际开口，不能把多边形投影误认为开口边界。检查改为原始母顶面与原切削工具（含底切平面和接触区保留遮罩）的实际交线，每孔仍按弧长取200点，并在顶面局部切平面内沿开口内法向移0.2。OCCT布尔交线本身的微米级3D逼近误差独立记录，XY位置投回精确母面后再判0.01mm距离；不改变BODY。每孔1000棱柱点及额外1000顶壳点不减量。

### 计算拆分和证据保留

主键25+25姿态、滚轮23姿态拆成互不重叠的五组角度索引；汇总器要求角度全集恰好出现一次，缺失、重复、旧版本输入均不得通过。侧键各31物理姿态加两项止挡诊断也准备相同分组。新近邻优化先测小组件，再以实际测得的最小距离和精确BODY裁剪距离证明远处材料不可能更近；裁剪外界只作为剔除证明，绝不作为实测距离输出。停止了已被新模型取代的旧候选重复计算，已有分支、提交和结果未删除。

### 电池备选范围的进一步说明

第一组近等体积包络14x28x6、12x33x6、16x25x6没有获得通过路径；第二组较厚包络在粗固定位置网格中无合格静态布局。继续以更细位置网格记录最接近方案及实际障碍物，并测试较小估计包络，报告每种体积变化。任何缩小均不得推导电池容量或12h达标。另独立检验原18x22x6包络的定向耦合抬升/旋转路线，优先保留原包络；全部尝试都保持最终精确0.5mm验收标准。

### C14有限元和切片；C15至C17编码器板诊断

C14挡板按最终几何重新计算S7，12/12通过，最大P95为1.993041504MPa；G8的18个同BODY工况仍有效。九件打印件的最终几何已完成真实单盘和逐件切片。C15/C16仅修改估计的编码器转接板；端部23姿态诊断未全通过，因此不发布。C17使板前段斜边进一步内收，保持Y34.25处后固定脚周围板材及前安装孔，待完整复核。其余打印件和BODY不变。

### 撤回裁剪BODY距离法，重跑受影响门槛

独立回归发现OCCT在部分BODY布尔裁剪时丢失局部几何。电池相邻姿态中，裁剪法报2.308833080mm和2.439835181mm，完整原始BODY分别只有0.561713853mm和0.506864449mm。默认和Tree极值算法对完整BODY一致。先前36项算法对照共用裁剪底层，因此不能证明该方法正确。任何采用裁剪BODY的旧距离、运动、装入端点、窗口占用结论均撤回验收用途；保留原结果供追溯。

所有当前距离检查显式调用exact_distance.py，直接给BRepExtrema传入完整原始实体；bounded_scene只用AABB排除不可能更近或违约的零件，不再裁剪实体。窗口检查直接对完整BODY和原始BODY分类。新增五姿态回归并重跑G1相关诊断、G2/G3/G4/G5/G6/G7。common.py旧实现保留只为历史源码和不依赖该函数的有限元证据版本，不得作为当前验收入口。S7/G8和真实切片不使用该距离路径，其实际结果继续保留。

电池候选路径规划仍只作为候选生成；粗场安全裕量提高至离开初始 bay 后0.85mm，最终每0.25mm/2.5度姿态仍按完整BRep的0.5mm要求验收。尚未把较小候选包络替换为正式H电池。

### C17完整原实体复核与电池方案选择

C17编码器板23个滚轮点击姿态全部通过，最小精确间隙0.402618546mm；打印件、固定BODY和轮轴均未改动。五个已知裁剪异常姿态的完整实体回归全部匹配，其中0.338881639mm姿态继续判失败；最终总表拒绝带旧裁剪标记的验收报告。

新的电池路径规划仍未给原18x22x6包络找到合格路线，这不是几何不可能性证明。12x18x6备选167姿态、14x20x6备选166姿态分别完成完整原始BODY精确距离检查，均通过0.5mm要求，最小0.600000000mm。选择较大的14x20x6mm候选；中心(-17,57,16.4)、原插头、19x23x7服务预留区、原线束及全部打印件保持原位。电池包络体积从2376降为1680mm3，减少29.29%；不据此推算容量。最终H导出件仍需复跑静态/运动/电子、服务路线、D板域、原生装配和视图；未闭合前不建Release。

### 功能接触分区的双向几何核对

为避免功能接触分解发生同类几何丢失，增加 `partition_check.py`。第一次按子实体体积简单相加，主键分区差0.052254573mm3；使用不同布尔容差仍重现。但将分区重新合并后，与原完整BODY双向求差均为0mm3、0个实体，说明是体积积分差异，不能把它当作材料丢失，也不能只忽略该差异。最终要求所有分区有效、重组有效，且原形减重组、重组减原形的体积均≤0.001mm3；另原样记录积分差异。LEFT、RIGHT、WHEEL三组本地检查均没有检测到丢失或新增材料；所有运动和功能接触检查必须采用此分区审计。

### 六窗口的原始中键支座占用

六窗口完整BODY复算中，ROOT_TRI_R的3个棱柱采样点位于原R3.2中键微动横向螺栓支座。逐点核对最终BODY、原始BODY和 `SWITCH_MIDDLE_MOUNT.step` 均包含该点，且Z≤13.35mm；此特征是原结构，几何未改变。汇总保留每个原始inside标志和初次未分类结论，只为这三个点补充具名源特征分类。六孔各200边界、1000棱柱和1000顶壳点仍全量保留；不使用“与旧版一样”作为泛化豁免。

### 发布分支只读复核

开发期主工作流曾按RUN配置重建模型并回写产物。最终工作分支改为只读 `gate_accounting.py --check-only`，避免推送已核对结果时意外重建或覆盖最终几何；数值计算保留在独立结果分支及对应源码中。只有全部G1–G11和产物身份通过后才进入PR、合并及Release阶段。

### 完整BODY键帽直推、母面包含与最终视图

独立代码复查发现诊断脚本的键帽直推仍先求局部BODY交集，因此最终入口改为 `cap_insertion_final.py`：两个键帽连同PET各41姿态、每0.25mm直接与完整保存的BODY求交，82姿态相交体积均为0。原诊断保留供追溯，但不得替代这份最终报告。隐藏结构母面包含新增局部分区重组核对，两侧均未检测到材料增减、铰耳/固定座/钢销越出母面体积均为0。BODY及打印几何没有变化。

实际最终C14打印件、C17转接板和14x20x6电池已生成50幅视图，含六面正交、内部六面、两个等轴测、剖面、动作图、20幅装配步骤及r3对照；均来自保存的STEP组件。目视核对六视图、前斜视和Z16.6剖面。装配外形88.236x66.096x26.164mm，含0.8mm脚贴。真实切片排盘图另沿用同一最终打印件的切片产物。

### C18：滚轮载架后部底面让位

完整实体滚轮验收在+4.4度检出载架非功能底缘到固定支座0.227428734mm，未达到0.30mm，虽未穿模仍判失败。最近点是载架(4.35,35.732552,9.276758)与固定支座(4.35,35.75,9.05)。这不是C17转接板问题，也不得扩大功能接触例外。源码将载架Y34.2..36.2区域底面从Z10.4抬到10.6，保留Z12.2上座面，剩余名义厚度1.60mm；BODY、五脚、轮轴、孔位和板上座面不变。用原生成步骤重建，只导出改变的载架；要求几何差集证明没有新增材料。C18完成前，旧载架相关运动、电子/静态、网格、切片、原生装配与视图均不作为C18验收。

原diagnostic_checks同时执行已被替代的原始侧键扫掠和局部区域直推，造成重复且漫长的检查。新入口geometry_checks_final、static_checks_final和access_kinematics_final从原验证逻辑逐块分离，判据和采样数保持原值；G5仍以完整运动分组为准，键帽直推仍用cap_insertion_final完整BODY检查。

C18重建只去除2.479742346mm3，新增材料0；载架体积587.077662802mm3，STEP为有效单实体，STL为单一闭合网格。原失败的+4.4度完整滚轮组复测通过，载架非功能区域间隙为0.417632533mm；其余角度仍由完整矩阵逐项重验，不把单个端点当作全程结论。C18整机本地FreeCAD再次保存、重开94个有效组件，并重新读入94实体STEP。九件打印体积重新积分为17640.328418219mm3。

C18九件G1再次通过单一有效实体、闭合网格、BRep及三角网格自相交检查；五脚粘贴面Z5.2共面。两键帽完整BODY直推82姿态相交体积全部0；隐藏铰耳、内止动耳和钢销未越出母面。距离算法五案例回归再次匹配，0.338881639mm案例保持失败。

### C19：中键座横梁球端真实干涉

C18完整实体电子检查检出BODY与SWITCH_MIDDLE相交0.006686004mm3；更严格体积积分得到同值，交集为有效实体，范围X[-3.3,-3.132532421]、Y[45.487652462,46.512347538]、Z[9.05,9.185615759]。原因是原中键座横梁的球形内端高出Z9.05平座面，侵入微动底角，不是数值噪声。尝试平移微动X+0.05仍相交0.002879564mm3；X+0.20又与螺栓支座相交5.839487021mm3，因此不移动或削改微动本体。

C19在wheel_mechanism.py的托架生成步骤，把横梁端部在6.0×13.0mm微动座投影内削平到原Z9.05座面，随后才并入托架。电子件、螺孔轴线、侧键、原五脚及外壳母面不变。必须从源码重建BODY，并比较新增/移除体积和Z9.0以下区域；修改BODY后G8/S7以及所有读取BODY的几何、运动、电子、装配和视图报告均须按新几何重验。C18结果保留为失败候选，不发布。

随后完成C18全部369项功能接触诊断，仅中键区域失败；该项还存在端子到低部中央连梁0.25mm的非功能间隙。原0.6×1.5mm端子的孔为1.2×2.0mm；C19把三孔改为1.8×2.7mm，提供0.60mm侧向名义净空，不把刚性端子当作可压缩软线。此项涉及中央连梁的内部孔，故原拟定的“Z9.0以下完全不变”不再成立；改为独立证明五个Ø8脚贴平台及其局部立柱区域、Z5.1以下低部不变，并重算完整BODY刚度。判据0.001mm3/0.5mm保持不变。微动本体、螺栓轴线和接触高度未改。

C18真实PrusaSlicer 2.9.6单盘切片为PLA36.11g、5h18m40s，九件对象、比例1、最小包围矩形间距13.032682419mm。3MF回读最大包围尺寸差0.000004803mm。F2独立试验件0.92g、13m55s。目视核对C18实际六视图拼图与排盘图；单盘耗材包含支撑，不能等同CAD聚合物质量或装电子后的整机重量。载架改变后重新生成的FCStd、STL/STEP、切片、报告和图像均按各自产物身份核对。

C19首轮源码已导出有效BODY，但审计脚本把两个确实为空的Z≤5.1截面交集传给布尔差，OCCT返回Null TopoDS_Shape。局部核对两侧均0实体、0面、0体积，故修正审计：仅在输入已确认没有实体时返回集合差的0体积；非空布尔错误仍直接失败。比较基准固定为C18保存实体，避免重跑时错误地把新BODY与自身比较；不修改几何或放宽判据。

低位区域的空交集不单独作为保留证明：另计算完整旧BODY减新BODY、新BODY减旧BODY，逐个记录变化实体范围，并要求全部变化位于Z5.1以上；五脚区域再与这些完整变化实体逐一做精确距离/相交检查。原裁剪比较原样保留为附加数据。

C18全部运动分组已汇总：LEFT/RIGHT各25姿态，WHEEL23姿态，两侧键各33姿态全部通过；D板域1607.720377mm2的指定平面构造通过完整实体净空，插头可达性和滚动包络通过。C18仍因中键原始相交0.006686mm3、端子净空0.25mm而失败，不发布。完整汇总保留在candidates/C18_complete_summary.json。

### C19完整重合实体布尔异常与边界审计

独立检查纠正上述“两个确实为空”的表述：空的是内核返回的截取结果，不能据此认定几何区域没有材料。Z<5.1的STL含实际面片，13个向内偏移的诊断点均被完整BODY分类为IN；小范围同高度截取能得到非零实体，大范围截取却返回空集。直接旧BODY减新BODY返回旧BODY的近似全部体积，新减旧同样返回整个新BODY。CadQuery、FreeCAD调用均复现；常规有效性、单壳体和自相交检查不解释这种布尔误分类。原失败数值保留，绝不把整壳布尔结果改写为0。

新增boundary_preservation.py：把新旧完整BODY的每一个边界面分别导出，按包含裁剪曲线、曲面和方向的完整递归STEP实体定义匹配；对所有未匹配面，在声明的修正盒X[-3.5,0.65]、Y[37,50]、Z[5.1,9.3]外做双向精确面差，并核对每个面的内外分区面积守恒。局部体积差另用盒内闭合实体计算，再以完整实体自适应体积积分作独立平衡检查。五脚区域完全在修正盒外，Z<5.1材料也在其外；不再用空BODY裁剪作为保留证明，不改变完整原始实体距离算法。

本地诊断匹配797个完整面，剩余旧34面/新36面在盒外双向面差面积均0；盒内移除20.409386047mm3、新增0，分为三个端子孔和一个球端帽。完整体积变化与局部变化差约0.000059mm3，低于0.001mm3。该审计另有正、负回归：盒内8mm3挖孔应通过，盒外另开孔必须拒绝（检测到16mm2边界变化）。正式报告仍须由重建工作流针对实际最终模型重新产生，随后重跑所有受BODY变化影响的门槛。

### 固定C19A实体，拒绝C19B重建变体

ed784e2源码工作流再次重建得到C19B（结果2385d5d），BODY体积12612.841732656mm3。中键相交仍为0、非功能净空0.60mm，但完整边界审计失败：圆柱面44在X[-31.8873,-5.46]、Y[44.55,48.85]、Z[8.4,12.7]处不能相互消去，完整/局部体积差约0.011141mm3。其包围尺寸差很小，尚不能把这种数值变化解释为可忽略或直接放宽判据；该变体明确拒绝，完整失败报告留在不可变提交，摘要为candidates/C19B_REJECTED_REBUILD.json。

选择此前由5adc6e7源码生成、保存在7d112c4的C19A BODY及配套源特征，所有正式验收锁定同一实体。该实体本地完整边界审计已通过；选择本身不替代后续G1–G11。C19A没有从成品STEP上修补，也没有混用C19B零件；沿用真实源生成产物，继续网格和装配阶段。candidates/C19_SELECTED_GEOMETRY.json记录构建源码、原始产物提交和文件身份。BODY_C19_RUN改为恢复基准、审计已固定实体、生成表面网格和装配；通用rebuild_all仍会从源码重新生成模型，重新生成的输出必须接受独立审计，不能继承这次通过状态，不保证CAD内核的位级确定性。


### C19A 真实切片与刚度偏差调查补项

C19A固定实体完成新的FreeCAD保存/重开：94个独立组件均为有效单实体；完整STEP回读94实体。PrusaSlicer 2.9.6九件原尺寸单盘切片PLA36.04g、5h18m13s（含支撑），最小包围矩形间距13.032682419mm，3MF回读最大尺寸差0.000004803mm。F2试验件0.92g、13m55s。对应不可变产物提交3442c7e，生产源码9151475。

C19A的18个主G8求解全部达到R3.2，最低比值104.406666%，位于h2.4的press_B_d16。该项58.686987104N/mm比作者60.53N/mm低约3.044791%；旧调查脚本只允许夹持工况待调查，因此明确失败并保留f68bd92记录，未将G8标为完成。扩展调查为逐个真实未解决工况匹配作者V2控制：三档夹持及h2.4指压B共四个对照；原18项结果保持原值，每个对照仍须在作者值3%以内且力/力矩平衡通过。比较结论包括几何所导致的重新网格化效应，不推断单个特征贡献。整壳近重合布尔差已证实不可靠，新调查仅报告完整有效实体自适应体积及源修改历史，不把错误布尔差当作移除/新增几何证据。S7在同一冻结BODY上继续串行执行。


### C19A G8和S7最终数值复核

新增对照源码6f4d8a7、结果b7148f3：四个作者V2控制求解全部通过。h2.4指压B控制为60.650570679N/mm，对作者60.53N/mm为+0.199192%；最终件仍为58.686987104N/mm，不替换原始值。三档夹持控制对作者偏差为-0.122825%、+0.061703%、-0.061580%。由最终几何及其网格变化引起的差异被单独列出；G8的18项最低R3.2比104.406666%，全部力/力矩平衡通过。S7的12项三档求解全部通过，整体与侧框区域最大P95为1.993041504MPa，限值10MPa；5N止挡力、每颗20N参考螺钉预紧和线弹性假设不变。前一补项脚本有局部变量遮蔽模块名的运行错误，已明确失败并以源码修正重跑；未改动模型或数值判据。


汇总阶段初次运行未恢复未纳入Git的R3.2基准STEP，combine_windows在加载基准时失败。已在汇总和视图入口明确先执行restore_inputs；基准来自已固定的R32_BASELINE.FCStd，未改数值或几何判据。
