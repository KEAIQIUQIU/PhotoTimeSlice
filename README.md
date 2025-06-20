# 时间切片照片生成器

这是一个用于创建时间切片(time slice)照片的Python工具，可以从一系列连续拍摄的照片中生成具有时间维度效果的合成图像。

## 功能特点

- 支持多种时间切片模式：
  - **垂直切片**：纵向时间条带效果
  - **水平切片**：横向时间条带效果
  - **圆形切片**：径向时间切片效果
- **支持广泛的图像格式**：
  - 普通格式: JPG, JPEG, PNG, TIF, TIFF
  - RAW格式: NEF(Nikon), DNG(Adobe), CR2/CR3(Canon), ARW(Sony), RAF(Fujifilm), ORF(Olympus), RW2(Panasonic)
- 可调节切片位置和方向
- 输出尺寸与输入图像一致
- 输出高质量无损JPEG图像
- 简化参数：仅使用 `--linear` 控制所有线性模式
- 支持正序/逆序排序

## 安装依赖

所需依赖：
```
Pillow
tqdm
rawpy (用于处理RAW格式)
```

## 使用方法

```bash
python timeslice.py -t [切片类型] -i [输入目录] -o [输出目录] [选项]
```

### 基本参数

| 参数 | 简写 | 描述 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入目录，包含源图片 | `input` |
| `--output` | `-o` | 输出目录，保存结果 | `output` |
| `--type` | `-t` | **必须**：切片类型 (`vertical`, `horizontal`, `circular`) | 无 |

### 高级选项

| 选项 | 简写 | 描述 | 适用切片类型 |
|------|------|------|-------------|
| `--position` | `-p` | 条带位置 (`left`, `center`, `right`, `top`, `bottom` 或 0.0-1.0) | 垂直/水平 |
| `--linear` | `-l` | 启用线性模式：<br>- 垂直/水平切片：每张图片取不同部位<br>- 圆形切片：扇形大小随时间变化 | 所有类型 |
| `--reverse` | `-r` | 逆序排序（使用时间倒序的照片序列） | 所有类型 |

### 使用示例

1. **垂直时间切片（居中位置）**：
   ```bash
   python timeslice.py -t vertical -p center -i photos -o result
   ```

2. **水平时间切片（线性模式）**：
   ```bash
   python timeslice.py -t horizontal -p top -l -i photos -o result
   ```

3. **圆形时间切片（统一大小模式）**：
   ```bash
   python timeslice.py -t circular -i photos -o result
   ```

4. **圆形时间切片（变化大小模式）**：
   ```bash
   python timeslice.py -t circular -l -i photos -o result
   ```

5. **逆序时间切片（时间倒流效果）**：
   ```bash
   python timeslice.py -t vertical -r -i photos -o result
   ```

## 输入要求

1. 所有输入图片必须具有相同的尺寸
2. 图片按时间顺序命名（支持自然排序）
3. **支持格式**：
   - **普通格式**: JPG, JPEG, PNG, TIF, TIFF
   - **RAW格式**:
     - Nikon: NEF
     - Canon: CR2, CR3
     - Sony: ARW
     - Fujifilm: RAF
     - Olympus: ORF
     - Panasonic: RW2
     - Adobe: DNG

## 输出结果

结果将保存为无损JPEG格式，文件名为 `timeslice.jpg`，位于指定的输出目录中。

## 切片类型说明

### 垂直切片
- 从每张图片中提取一个纵向条带
- 条带位置可通过 `--position` 参数控制
- 线性模式 (`--linear`) 下，条带位置变化
- 输出图像尺寸与输入相同

### 水平切片
- 从每张图片中提取一个横向条带
- 条带位置可通过 `--position` 参数控制
- 线性模式 (`--linear`) 下，条带位置变化
- 输出图像尺寸与输入相同

### 圆形切片
- 从中心点向外创建径向时间切片
- **默认模式**：统一大小的扇形（覆盖整个圆）
- **线性模式** (`--linear`)：扇形大小变化（从中心向外）

## 圆形切片模式对比

| 模式 | 参数 | 效果描述 | 适用场景 |
|------|------|---------|---------|
| **统一大小** | `-l` 关闭 | 所有扇形大小相同，覆盖整个圆形区域 | 展示不同时间点在同一场景的对比 |
| **变化大小** | `-l` 开启 | 扇形半径随时间变化（从中心向外生长） | 强调时间流逝的方向性和渐进变化 |

## 逆序功能说明

`-r` 选项允许您反转照片序列顺序：
- **正序模式**（默认）：照片按时间顺序从最早到最新处理
- **逆序模式**（`-r`）：照片按时间倒序从最新到最早处理

逆序功能适用于所有切片类型，可以创建"时间倒流"效果。

## 注意事项

- 处理RAW格式需要安装`rawpy`库
- 图片数量越多，处理时间越长
- 输出图像尺寸与输入图像相同
- 确保所有输入图片尺寸一致
- 支持的RAW格式取决于rawpy库的版本，某些较新的相机RAW格式可能需要更新rawpy

## 格式支持扩展

最新版本增加了对以下格式的支持：
- **普通格式**: PNG, TIF, TIFF
- **RAW格式**:
  - Canon: CR2, CR3
  - Sony: ARW
  - Fujifilm: RAF
  - Olympus: ORF
  - Panasonic: RW2

```
主要更新内容：
1. 扩展了支持的图片格式
2. 添加了“逆序排序”选项