# ZMXYOL_AUTO

《造梦西游 OL》每日自动化。基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework)，在 [MAA-zmxy](https://github.com/luser-user/MAA-zmxy) 的流水线与 Agent 之上做了日常向定制。

## 能做什么

打开 MFA 客户端后，选择预设即可一键跑完日常：

1. 启动游戏并等到进入村庄
2. 冰霜遗迹
3. 一键碾压
4. 仙盟建设
5. 关卡扫荡
6. 联盟（魔窟探险 / 炼妖塔 / 通告任务）
7. 法相挖宝
8. 关闭游戏

如果已经停在村庄界面，使用预设 **游戏内日常**，不会重复启停客户端。

## 使用前

- 模拟器分辨率短边 **720**，ADB 连接正常
- 安装的游戏渠道包名与「游戏渠道」选项一致，默认按腾讯应用宝 `com.tencent.tmgp.zmxyol` 启动
- 关卡扫荡开始前应能进入天庭；其余日常任务从村庄/世界地图入口识别

详细说明见 [每日自动化说明](./docs/zh_cn/user/daily.md)。开发调试见 [如何开发](./docs/zh_cn/develop/how_to_develop.md)。

## 本地开发

```bash
git clone https://github.com/wobushibingshan/ZMXYOL_AUTO.git
cd ZMXYOL_AUTO
git submodule update --init --recursive
python tools/configure.py
python -m unittest discover -s tests -v
```

OCR 模型由 `tools/configure.py` 从 `assets/MaaCommonAssets` 复制到 `assets/resource/base/model/ocr/`，不要把模型提交进仓库。

## 致谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 驱动，任务资源参考 **[MAA-zmxy](https://github.com/luser-user/MAA-zmxy)**。
