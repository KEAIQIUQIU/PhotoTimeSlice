import re
import sys
from pathlib import Path
from PIL import Image
from tqdm import tqdm

# Windows可执行文件判断
is_frozen = getattr(sys, 'frozen', False)

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """Windows文件自然排序"""
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(str(s))]

def load_images(input_dir, reverse=False):
    """加载Windows目录中的图片"""
    # 支持的图片格式
    image_extensions = [
        "*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff",
        "*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf", "*.orf", "*.rw2"
    ]

    # 遍历目录
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(Path(input_dir).glob(ext))

    # 排序
    image_paths.sort(key=natural_sort_key)
    if reverse:
        image_paths = list(reversed(image_paths))

    # 加载图片
    images = []
    if not is_frozen:
        print(f"加载 {len(image_paths)} 张图片...")

    for path in tqdm(image_paths, desc="加载图片", disable=is_frozen):
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
            try:
                images.append(Image.open(path))
            except Exception as e:
                print(f"无法打开图片 {path}: {e}")

    return images