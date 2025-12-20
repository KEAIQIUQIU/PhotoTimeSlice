import re
import sys
import os
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from datetime import datetime

# 判断是否为打包环境
is_frozen = getattr(sys, 'frozen', False)


def get_base_path():
    """获取正确的基础路径（兼容开发环境和打包环境）"""
    if is_frozen:
        # 如果是打包的exe，使用临时解压目录
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境，使用当前文件目录
        return os.path.dirname(os.path.abspath(__file__))


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """Windows文件自然排序"""
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(str(s))]


def get_file_creation_time(path):
    """获取文件创建时间"""
    try:
        return os.path.getctime(path)
    except:
        return os.path.getmtime(path)


def get_file_modification_time(path):
    """获取文件修改时间"""
    return os.path.getmtime(path)


def load_images(input_dir, sort_by='name', reverse=False):
    """加载Windows目录中的图片，支持多种排序方式"""
    # 确保输入目录存在
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    # 支持的图片格式
    image_extensions = [
        "*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff",
        "*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf", "*.orf", "*.rw2"
    ]

    # 遍历目录
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(Path(input_dir).glob(ext))

    if not image_paths:
        raise FileNotFoundError(f"在目录 {input_dir} 中未找到支持的图片文件")

    # 根据排序规则排序
    if sort_by == 'name':
        image_paths.sort(key=natural_sort_key)
    elif sort_by == 'created_time':
        image_paths.sort(key=get_file_creation_time)
    elif sort_by == 'modified_time':
        image_paths.sort(key=get_file_modification_time)
    else:
        image_paths.sort(key=natural_sort_key)  # 默认按名称

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