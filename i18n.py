import json
import os
from pathlib import Path


class Translator:
    def __init__(self, lang='en'):
        self.translations = {}
        self.load_translations(lang)

    def load_translations(self, lang):
        """加载Windows系统的翻译文件"""
        try:
            lang_file = Path(__file__).parent / f"languages/{lang}.locpak"
            if lang_file.exists():
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            else:
                en_file = Path(__file__).parent / "languages/en.locpak"
                if en_file.exists():
                    with open(en_file, 'r', encoding='utf-8') as f:
                        self.translations = json.load(f)
        except Exception as e:
            print(f"加载翻译文件失败: {e}")
            self.translations = {}

    def tr(self, text):
        """翻译文本"""
        return self.translations.get(text, text)