# 时间切片照片生成器（Windows 版）
### 一款专为 Windows 系统设计的时间切片照片生成工具，支持多种切片算法，可将一系列连续拍摄的照片合成为时间切片效果。
## 功能特点
✅ 支持 9 种切片类型（垂直 / 水平 / 圆形扇形 / 椭圆形扇形 / 环带类 / S 型曲线等）✅ 主题切换：浅色模式（默认）/ 深色模式（菜单带选中标记✓）✅ 语言切换：中文 / English（菜单带选中标记✓）✅ 进度实时显示，支持批量图片处理✅ 自动识别图片顺序，支持逆序排序✅ 完成后可自动打开生成的图片✅ 错误日志实时输出，便于问题排查
## 环境要求
操作系统：Windows 10/11（32/64 位均可）
Python 版本：3.7+
依赖库：PyQt5、Pillow、numpy、tqdm、rawpy（可选，用于处理 RAW 格式图片）
## 安装步骤
1. 克隆 / 下载项目
bash
运行
git clone https://github.com/KEAIQIUQIU/PhotoTimeSlice.git
cd PhotoTimeSlice
2. 安装依赖
```bash
pip install pyqt5 pillow numpy tqdm rawpy
```
## 使用方法
### 方式 1：图形界面（推荐）
直接运行 GUI 程序：
```bash
python gui.py
```
### 方式 2：命令行（CLI）
```bash
python cli.py -i 输入目录 -o 输出目录 -t 切片类型
```
完整参数示例
```bash
python cli.py -i ./input_photos -o ./output -t vertical -p center -l -r -lang zh_CN
```
CLI 参数说明

-i/--input	输入目录路径（默认：input）
-o/--output	输出目录路径（默认：output）
-t/--type	切片类型（必需），可选值：
vertical/horizontal/circular_sector/elliptical_sector/elliptical_band/rectangular_band/circular_band/vertical_s/horizontal_s
-p/--position	位置参数（仅垂直 / 水平 / S 型切片有效）：left/center/right/top/bottom（默认：center）
-l/--linear	启用线性模式（默认：关闭）
-r/--reverse	逆序排序图片（默认：关闭）
-lang/--language	语言：zh_CN/en（默认：en）

切片类型说明

垂直切片（vertical）	按垂直方向分割图片，每个切片取自对应位置的垂直条带
水平切片（horizontal）	按水平方向分割图片，每个切片取自对应位置的水平条带
圆形扇形切片	以图片中心为原点，按扇形角度分割图片
椭圆形扇形切片	以图片中心为原点，按椭圆形扇形角度分割图片
椭圆形环带切片	以图片中心为原点，按椭圆形环带（同心圆）分割图片
矩形环带切片	按矩形环带（等宽竖条）分割图片
圆形环带切片	以图片中心为原点，按圆形环带（同心圆）分割图片
垂直 S 型曲线	按垂直方向生成 S 型曲线切片，呈现动态扭曲效果
水平 S 型曲线	按水平方向生成 S 型曲线切片，呈现动态扭曲效果

## 注意事项
输入目录中的图片需为同一尺寸，否则会提示错误
推荐使用连续拍摄的照片（如延时摄影），效果最佳
支持的图片格式：JPG/PNG/TIF/JPEG（基础格式）、NEF/CR2/ARW/DNG 等（需安装 rawpy）