import argparse
from PIL import Image, ImageDraw
from pathlib import Path
from tqdm import tqdm
import re


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """自然排序键函数，支持数字顺序"""
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(str(s))]


def load_images(input_dir, reverse=False):
    """加载输入文件夹中的所有图片，支持多种格式，按文件名自然排序"""
    # 支持的图像格式扩展名
    image_extensions = [
        # 普通格式
        "*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff",
        # RAW格式
        "*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf", "*.orf", "*.rw2"
    ]

    image_paths = []
    for ext in image_extensions:
        image_paths.extend(Path(input_dir).glob(ext))

    # 使用自然排序对文件名排序
    image_paths.sort(key=natural_sort_key)

    # 如果需要逆序排序
    if reverse:
        image_paths = list(reversed(image_paths))

    images = []
    print(f"加载 {len(image_paths)} 张图片...")
    for path in tqdm(image_paths, desc="加载图片"):
        if path.suffix.lower() in ['.nef', '.dng', '.cr2', '.cr3', '.arw', '.raf', '.orf', '.rw2']:
            try:
                import rawpy
                with rawpy.imread(str(path)) as raw:
                    rgb = raw.postprocess()
                img = Image.fromarray(rgb)
                images.append(img)
            except ImportError:
                raise ImportError("请安装rawpy库以处理RAW格式: pip install rawpy")
        else:
            images.append(Image.open(path))

    return images


def create_vertical_slice(images, position, linear=False):
    """创建纵向条形时间切片 - 输出尺寸与输入相同"""
    img_w, img_h = images[0].size
    num_images = len(images)

    # 创建输出图像 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h))

    # 条带宽度 = 总宽度 / 图片数量
    strip_width = max(1, img_w // num_images)

    print("生成纵向切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        # 计算裁剪位置
        if linear:
            # 线性模式：每张图片取不同部位
            crop_x = int(i * (img_w - strip_width) / (num_images - 1)) if num_images > 1 else 0
        else:
            # 固定位置模式
            if position == "left":
                crop_x = 0
            elif position == "right":
                crop_x = img_w - strip_width
            elif position == "center":
                crop_x = (img_w - strip_width) // 2
            else:  # 自定义位置 (0.0-1.0)
                try:
                    pos = float(position)
                    crop_x = int((img_w - strip_width) * pos)
                except ValueError:
                    crop_x = (img_w - strip_width) // 2

        # 计算粘贴位置
        paste_x = i * strip_width

        # 裁剪条带
        strip = img.crop((crop_x, 0, crop_x + strip_width, img_h))

        # 如果条带宽度需要调整
        if strip.width < strip_width:
            strip = strip.resize((strip_width, img_h))
        elif strip.width > strip_width:
            strip = strip.crop((0, 0, strip_width, img_h))

        # 粘贴到结果图像
        result.paste(strip, (paste_x, 0))

    return result


def create_horizontal_slice(images, position, linear=False):
    """创建横向条形时间切片 - 输出尺寸与输入相同"""
    img_w, img_h = images[0].size
    num_images = len(images)

    # 创建输出图像 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h))

    # 条带高度 = 总高度 / 图片数量
    strip_height = max(1, img_h // num_images)

    print("生成横向切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        # 计算裁剪位置
        if linear:
            # 线性模式：每张图片取不同部位
            crop_y = int(i * (img_h - strip_height) / (num_images - 1)) if num_images > 1 else 0
        else:
            # 固定位置模式
            if position == "top":
                crop_y = 0
            elif position == "bottom":
                crop_y = img_h - strip_height
            elif position == "center":
                crop_y = (img_h - strip_height) // 2
            else:  # 自定义位置 (0.0-1.0)
                try:
                    pos = float(position)
                    crop_y = int((img_h - strip_height) * pos)
                except ValueError:
                    crop_y = (img_h - strip_height) // 2

        # 计算粘贴位置
        paste_y = i * strip_height

        # 裁剪条带
        strip = img.crop((0, crop_y, img_w, crop_y + strip_height))

        # 如果条带高度需要调整
        if strip.height < strip_height:
            strip = strip.resize((img_w, strip_height))
        elif strip.height > strip_height:
            strip = strip.crop((0, 0, img_w, strip_height))

        # 粘贴到结果图像
        result.paste(strip, (0, paste_y))

    return result


def create_circular_slice(images, linear=False):
    """
创建圆形时间切片 - 填满整个图像
linear: 是否启用线性模式（控制扇形大小变化）
    """
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    radius = min(center_x, center_y)
    num_images = len(images)

    # 创建空白画布 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))

    # 计算角度步长
    angle_step = 360 / num_images

    print("生成圆形切片...")
    for i, src_img in enumerate(tqdm(images, desc="处理图片")):
        # 计算当前扇形的角度范围
        start_angle = i * angle_step
        end_angle = (i + 1) * angle_step

        # 统一扇形大小：所有扇形使用最大半径
        if not linear:
            r = radius
        # 线性变化：从中心到边缘均匀分布
        else:
            r = radius * (i / (num_images - 1)) if num_images > 1 else radius

        # 创建扇形蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.pieslice(
            [center_x - r, center_y - r,
             center_x + r, center_y + r],
            start_angle, end_angle, fill=255
        )

        # 应用蒙版并粘贴
        masked_img = Image.composite(src_img, result, mask)
        result.paste(masked_img, (0, 0))

    return result


def main():
    parser = argparse.ArgumentParser(description="时间切片照片生成器")
    parser.add_argument("-i", "--input", default="input", help="输入文件夹路径")
    parser.add_argument("-o", "--output", default="output", help="输出文件夹路径")
    parser.add_argument("-t", "--type", required=True,
                        choices=["vertical", "horizontal", "circular"],
                        help="切片类型: vertical, horizontal, circular")
    parser.add_argument("-p", "--position", default="center",
                        help="条带位置: left/center/right/top/bottom 或 0.0-1.0")
    parser.add_argument("-l", "--linear", action="store_true",
                        help="启用线性模式：垂直/水平切片取不同部位；圆形切片使用变化的扇形大小")
    parser.add_argument("-r", "--reverse", action="store_true",
                        help="逆序排序：使用时间倒序的照片序列")

    args = parser.parse_args()

    # 创建输出目录
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # 加载图像
    images = load_images(args.input, args.reverse)
    if not images:
        print("错误: 输入目录中没有找到图片")
        return

    # 检查所有图片尺寸是否一致
    base_size = images[0].size
    for img in images:
        if img.size != base_size:
            print("错误: 所有图片必须具有相同的尺寸")
            return

    # 创建时间切片
    print(f"开始创建 {args.type} 类型时间切片...")
    if args.type == "vertical":
        result = create_vertical_slice(images, args.position, args.linear)
    elif args.type == "horizontal":
        result = create_horizontal_slice(images, args.position, args.linear)
    elif args.type == "circular":
        result = create_circular_slice(images, args.linear)

    # 保存结果（无损JPEG）
    output_path = Path(args.output) / "timeslice.jpg"
    print("保存无损JPEG图像...")
    result.save(output_path, "JPEG", quality=100, subsampling=0)
    print(f"时间切片已保存至: {output_path}")


if __name__ == "__main__":
    main()