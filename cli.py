import argparse
import sys
import os
from pathlib import Path

from utils import load_images
from slices import (
    create_vertical_slice,
    create_horizontal_slice,
    create_circular_sector_slice,
    create_elliptical_sector_slice,
    create_elliptical_band_slice,
    create_rectangular_band_slice,
    create_circular_band_slice,
    create_vertical_s_slice,
    create_horizontal_s_slice
)
from i18n import Translator

# Windows可执行文件判断
is_frozen = getattr(sys, 'frozen', False)


def get_translator(lang):
    """获取翻译器"""
    translator = Translator(lang)
    return translator


def run_timeslice(input_dir, output_dir, slice_type, position="center", linear=False, reverse=False,
                  progress_callback=None):
    """生成时间切片（仅Windows）"""
    translator = get_translator('en')

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "timeslice.jpg"

    # 加载图片
    images = load_images(input_dir, reverse)
    if not images:
        raise Exception(translator.tr("输入目录中没有找到图片"))

    # 检查尺寸
    base_size = images[0].size
    for img in images:
        if img.size != base_size:
            raise Exception(translator.tr("所有图片必须具有相同的尺寸"))

    # 进度回调
    if progress_callback:
        progress_callback(0)

    # 生成切片
    result = None
    try:
        if slice_type == "vertical":
            result = create_vertical_slice(images, position, linear)
        elif slice_type == "horizontal":
            result = create_horizontal_slice(images, position, linear)
        elif slice_type == "circular_sector":
            result = create_circular_sector_slice(images, linear)
        elif slice_type == "elliptical_sector":
            result = create_elliptical_sector_slice(images, linear)
        elif slice_type == "elliptical_band":
            result = create_elliptical_band_slice(images)
        elif slice_type == "rectangular_band":
            result = create_rectangular_band_slice(images)
        elif slice_type == "circular_band":
            result = create_circular_band_slice(images)
        elif slice_type == "vertical_s":
            result = create_vertical_s_slice(images)
        elif slice_type == "horizontal_s":
            result = create_horizontal_s_slice(images)
        else:
            raise ValueError(f"{translator.tr('未知切片类型:')} {slice_type}")
    except Exception as e:
        raise Exception(f"{translator.tr('生成切片失败:')} {str(e)}")

    # 保存图片
    try:
        result.save(output_path, "JPEG", quality=100, subsampling=0)
    except Exception as e:
        raise Exception(f"{translator.tr('保存图片失败:')} {str(e)}")

    return str(output_path)


def main():
    """CLI主函数（仅Windows）"""
    default_translator = get_translator('en')

    # 参数解析
    parser = argparse.ArgumentParser(
        description=default_translator.tr("时间切片照片生成器（Windows版）"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-i", "--input",
        default="input",
        help=default_translator.tr("输入文件夹路径（默认为\"input\"）")
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help=default_translator.tr("输出文件夹路径（默认为\"output\"）")
    )
    parser.add_argument(
        "-t", "--type",
        required=True,
        choices=["vertical", "horizontal", "circular_sector",
                 "elliptical_sector", "elliptical_band",
                 "rectangular_band", "circular_band",
                 "vertical_s", "horizontal_s"],
        help=default_translator.tr("切片类型（必需）")
    )
    parser.add_argument(
        "-p", "--position",
        default="center",
        help=default_translator.tr("条带位置：left/center/right/top/bottom 或 0.0-1.0")
    )
    parser.add_argument(
        "-l", "--linear",
        action="store_true",
        help=default_translator.tr("启用线性模式")
    )
    parser.add_argument(
        "-r", "--reverse",
        action="store_true",
        help=default_translator.tr("逆序排序")
    )
    parser.add_argument(
        "-lang", "--language",
        default="en",
        choices=["en", "zh_CN"],
        help=default_translator.tr("语言（en/zh_CN）")
    )

    args = parser.parse_args()
    translator = get_translator(args.language)

    try:
        # 进度回调
        def progress_callback(current):
            if not is_frozen:
                sys.stdout.write(f"\r{translator.tr('已处理')} {current} {translator.tr('张图片')}")
                sys.stdout.flush()

        # 生成切片
        output_path = run_timeslice(
            input_dir=args.input,
            output_dir=args.output,
            slice_type=args.type,
            position=args.position,
            linear=args.linear,
            reverse=args.reverse,
            progress_callback=progress_callback
        )

        # 输出结果
        print(f"\n{translator.tr('处理完成!')}")
        print(f"{translator.tr('时间切片已保存至:')} {output_path}")

        # Windows自动打开（可选）
        if input(f"{translator.tr('是否打开生成的图片？(y/n)')} ").lower() == 'y':
            os.startfile(output_path)

    except Exception as e:
        print(f"\n{translator.tr('错误:')} {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()