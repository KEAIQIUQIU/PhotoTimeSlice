import argparse
from pathlib import Path
import sys

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

is_frozen = getattr(sys, 'frozen', False)

def run_timeslice(input_dir, output_dir, slice_type, position, linear, reverse):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "timeslice.jpg"

    images = load_images(input_dir, reverse)
    if not images:
        raise Exception("输入目录中没有找到图片")

    base_size = images[0].size
    for img in images:
        if img.size != base_size:
            raise Exception("所有图片必须具有相同的尺寸")

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
        raise ValueError(f"未知切片类型: {slice_type}")

    result.save(output_path, "JPEG", quality=100, subsampling=0)
    return str(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="时间切片照片生成器")
    parser.add_argument("-i", "--input", default="input", help="输入文件夹路径")
    parser.add_argument("-o", "--output", default="output", help="输出文件夹路径")
    parser.add_argument("-t", "--type", required=True,
                        choices=["vertical", "horizontal", "circular_sector",
                                 "elliptical_sector", "elliptical_band",
                                 "rectangular_band", "circular_band",
                                 "vertical_s", "horizontal_s"],
                        help="切片类型")
    parser.add_argument("-p", "--position", default="center",
                        help="条带位置: left/center/right/top/bottom 或 0.0-1.0")
    parser.add_argument("-l", "--linear", action="store_true",
                        help="启用线性模式")
    parser.add_argument("-r", "--reverse", action="store_true",
                        help="逆序排序")

    args = parser.parse_args()

    try:
        output_path = run_timeslice(
            input_dir=args.input,
            output_dir=args.output,
            slice_type=args.type,
            position=args.position,
            linear=args.linear,
            reverse=args.reverse
        )
        print(f"时间切片已保存至: {output_path}")
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)