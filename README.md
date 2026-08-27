# ZMXYOL_AUTO

《造梦西游 OL》安卓端每日自动化。基于图像识别（[MaaFramework](https://github.com/MaaXYZ/MaaFramework)）连接模拟器，按预设把日常任务跑完。任务流水线参考 [MAA-zmxy](https://github.com/luser-user/MAA-zmxy)，本仓库按「一键长草」做了定制，后续功能会在此基础上重写或拆分。

当前能力是：**启动游戏 → 做完一套日常 → 关掉游戏**。不碰战斗数值，也不替代你自己点的非日常玩法。

## 能用来干什么

| 场景 | 怎么用 |
| --- | --- |
| 每天清日常 | 选预设「一键日常」，模拟器挂机跑完 |
| 人已经在村庄里 | 选「游戏内日常」，不重复启停客户端 |
| 只想进游戏、关弹窗 | 选「仅启动到村庄」 |
| 多角色轮换 | 一套日常结束后手动跑「切换角色」，再跑「游戏内日常」 |
| 后续重写某个玩法 | 按下表定位任务、流水线和自定义动作，单独替换即可 |

运行前提：

- 安卓模拟器，ADB 能连上
- 分辨率短边 **720**
- 安装包渠道和「游戏渠道」一致（默认腾讯应用宝 `com.tencent.tmgp.zmxyol`）
- 关卡扫荡要求能进天庭；其余日常从村庄世界地图识别入口

## 怎么使用

### 发版包（给使用者）

1. 从 Releases 下载 Windows 包并解压
2. 打开 `MFAAvalonia.exe`
3. 连接模拟器
4. 选「游戏渠道」
5. 选预设后点开始

### 开发目录（给后续重构）

1. 克隆仓库，准备 OCR 模型：

    ```bash
    git clone https://github.com/wobushibingshan/ZMXYOL_AUTO.git
    cd ZMXYOL_AUTO
    python tools/configure.py
    python -m unittest discover -s tests -v
    ```

    没有 `assets/MaaCommonAssets` 子模块时，`configure.py` 会自动下载中文 PPOCR。模型不要提交进仓库。

2. 用 MFA / MaaDebugger 加载 `assets/interface.json`
3. 连模拟器，短边 720
4. 选预设运行，或勾选单个任务调试

### 预设

| 预设 | 会做什么 |
| --- | --- |
| **一键日常** | 启动游戏 → 冰霜遗迹 → 一键碾压 → 仙盟建设 → 关卡扫荡 → 联盟 → 法相挖宝 → 关闭游戏 |
| **游戏内日常** | 同上，但不启停客户端 |
| **仅启动到村庄** | 只启动，关掉公告/活动弹窗，停在世界地图 |

联盟默认全选：魔窟探险、炼妖塔、联盟通告。关卡扫荡默认全选：五庄观、龙门福地、虚空之境、八仙过海、龙宫。都可以在任务选项里取消。

### 渠道包名

| 渠道 | 包名 |
| --- | --- |
| 腾讯应用宝 | `com.tencent.tmgp.zmxyol` |
| 小米 | `com.zmxyol.union.mi` |
| UC 九游 | `com.zmxyol.union.uc` |
| 其他 | 选「自定义包名」，填 `adb shell pm list packages` 里的完整包名 |

## 功能概览（重构对照）

下面按「用户能勾选的任务」列出。重写某个功能时，改对应的任务定义、Pipeline 和（如有）Agent 动作即可，不必先动整仓。

### 启停

| 任务 | 做什么 | 任务定义 | Pipeline | 入口节点 | 选项 |
| --- | --- | --- | --- | --- | --- |
| 启动游戏 | StartApp，处理加载页 / 开始界面 / 进入游戏 / 公告 / 活动弹窗，直到识别到村庄世界地图 | `assets/resource/tasks/GameLifecycle.json` | `assets/resource/base/pipeline/启动游戏.json` | `启动游戏` | 游戏渠道 |
| 关闭游戏 | StopApp，包名与启动相同 | 同上 | 同上 | `关闭游戏` | 游戏渠道 |

### 日常

| 任务 | 做什么 | 任务定义 | Pipeline | 入口节点 | 选项 / 自定义动作 |
| --- | --- | --- | --- | --- | --- |
| 冰霜遗迹 | 从世界地图进入并完成冰霜遗迹 | `FrostRuins.json` | `冰霜遗迹.json` | `冰霜遗迹任务开始前的等待` | Agent：`CheckRemainingCount` |
| 一键碾压 | 从世界地图进入并执行一键碾压 | `Oneclicksweep.json` | `一键扫荡.json` | `一键碾压任务开始前的等待` | Agent：`CheckOneClickDominationCost` |
| 仙盟建设 | 从世界地图进入并完成仙盟建设 | `Construction.json` | `仙盟建设.json` | `仙盟建设任务开始前的等待` | — |
| 关卡扫荡 | 进天庭后按勾选关卡扫荡 | `StageSweep.json` | `stages/关卡扫荡入口.json` 及各关卡 JSON | `关卡扫荡任务开始前的等待` | 关卡扫荡列表 |
| 联盟 | 魔窟探险 / 炼妖塔 / 通告任务 | `AnnouncementTasks.json` | `联盟.json`、`Alliance/*` | `联盟任务入口` | 联盟列表；Agent：`CheckExplorationCount`、`RunAnnouncementTaskLoop` |
| 法相挖宝 | 完成法相挖宝 | `DharmaCharacteristic.json` | `法相挖宝.json` | `法相挖宝任务入口` | Agent：`CheckChaosRelicCount` |

关卡扫荡子项与文件对应：

| 子项 | Pipeline |
| --- | --- |
| 五庄观 | `assets/resource/base/pipeline/stages/五庄观.json` |
| 龙门福地 | `stages/龙门福地.json` |
| 虚空之境 | `stages/虚空之境.json` |
| 八仙过海 | `stages/八仙过海.json` |
| 龙宫 | `stages/龙宫.json` |
| 公共入口 / 滑动 / 校验 | `stages/关卡扫荡入口.json`、`stages/关卡扫荡公共.json` |

联盟子项与文件对应：

| 子项 | Pipeline | Agent |
| --- | --- | --- |
| 魔窟探险 | `Alliance/魔窟探险.json` | `check_exploration_count.py`（`CheckExplorationCount`） |
| 炼妖塔 | `Alliance/炼妖塔.json` | — |
| 联盟通告 | `Alliance/通告任务.json` | `check_announcement_task.py`（领取/提交循环） |

### 独立任务

| 任务 | 做什么 | 任务定义 | Pipeline | 入口节点 |
| --- | --- | --- | --- | --- |
| 切换角色 | 在村庄打开菜单切到下一个角色；不在一键日常里 | `ChangeRole.json` | `切换角色.json` | `确认在村庄` |

### 预设

预设在 `assets/resource/tasks/preset/Daily.json`，只编排上面这些任务的勾选和默认选项，不含识别逻辑。重排日常顺序或拆新套餐，改这个文件即可。

## 目录（重构时从这里进）

```text
assets/interface.json          # 项目入口：控制器、资源、任务分组、导入列表
assets/resource/tasks/         # 用户可见任务、选项、预设
assets/resource/base/pipeline/ # 识别与点击流水线
assets/resource/base/image/    # 模板图
agent/                         # 复杂逻辑（OCR 次数判断、通告循环等）
tools/configure.py             # OCR 模型准备
tools/install.py               # 发版打包
tools/check_interface.py       # 预设 / 入口 / 模板图一致性
tests/                         # 不依赖真机的单测
```

约定：

- `interface.json` 只做装配，具体任务拆到 `assets/resource/tasks/`
- 能用 JSON Pipeline 表达的流程放 Pipeline；次数判断、通告翻页等放 `agent/custom/action/`
- 识别图按玩法分子目录，公共按钮在 `image/public/`
- 改任务名或入口节点后跑：`python tools/check_interface.py`

## 已知限制（重写时优先看）

- 分辨率锁短边 720，模板图按这个切的
- 关卡扫荡的勾选是用 `pipeline_override` 把节点串起来的，少选中间某一关可能让后续衔接断掉
- 「切换角色」没有自动循环多号，要手动再跑一轮日常
- 启动游戏按模板轮询加载/开始/进游戏/弹窗，渠道包登录页如果和现有图差太多需要单独补
- `stages/test1.json`、`stages/test2.json` 是调试残留，重构时可删
- 游戏界面一改，对应 PNG 和 ROI 就要重录；这是图像方案的固有成本

开发细节见 [如何开发](./docs/zh_cn/develop/how_to_develop.md)。日常操作短说明见 [每日自动化](./docs/zh_cn/user/daily.md)。

## 致谢

由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 驱动，任务资源参考 [MAA-zmxy](https://github.com/luser-user/MAA-zmxy)。
