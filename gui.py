import os
import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QCheckBox, QFileDialog, QProgressBar,
                             QGroupBox, QMessageBox, QTextEdit, QMenuBar, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent, QSettings, QTimer
from PyQt5.QtGui import QPalette, QColor, QFont

# 配置调试日志（可选）
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加当前目录到系统路径
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from cli import run_timeslice
from i18n import Translator  # 导入翻译器


class LogEvent(QEvent):
    """用于线程安全日志更新的自定义事件"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, text, is_error=False):
        super().__init__(LogEvent.EVENT_TYPE)
        self.text = text
        self.is_error = is_error


class TimesliceWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            from utils import load_images
            images = load_images(self.params['input_dir'], self.params['reverse'])
            total_images = len(images)

            if total_images == 0:
                raise Exception(self.tr("输入目录中没有找到图片"))

            self.log_signal.emit(f"找到 {total_images} 张图片，开始处理...")

            def progress_callback(current):
                self.progress_signal.emit(current)

            output_path = run_timeslice(
                input_dir=self.params['input_dir'],
                output_dir=self.params['output_dir'],
                slice_type=self.params['slice_type'],
                position=self.params['position'],
                linear=self.params['linear'],
                reverse=self.params['reverse'],
                progress_callback=progress_callback
            )

            self.progress_signal.emit(total_images)
            self.finished_signal.emit(output_path)
        except Exception as e:
            self.error_signal.emit(str(e))

    def tr(self, text):
        """翻译方法（线程内）"""
        translator = Translator()
        return translator.tr(text)


class TimesliceGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("TimeslicePhotoGenerator", "Settings")

        # 初始化翻译器
        self.translator = Translator()
        self.current_lang = self.settings.value("language", "zh_CN")
        self.translator.load_translations(self.current_lang)

        self.app = QApplication.instance()
        # 移除跟随系统，无需主题检测定时器
        self.theme_check_timer = QTimer()

        # 初始化主题（默认浅色）
        self.current_theme = self.settings.value("theme", "light")

        self.init_ui()
        self.load_theme()

        self.setWindowTitle(self.tr("时间切片照片生成器"))
        self.setGeometry(100, 100, 800, 600)

        self.current_output_path = ""
        self.total_images = 0
        self.worker = None

    def tr(self, text):
        """翻译方法"""
        return self.translator.tr(text)

    def apply_theme_style(self, theme_type):
        """应用Windows主题样式"""
        palette = QPalette()

        if theme_type == "dark":
            # Windows深色模式样式
            self.app.setStyle("Fusion")
            dark_color = QColor(45, 45, 45)
            light_color = QColor(180, 180, 180)

            # 主界面调色板
            palette.setColor(QPalette.Window, dark_color)
            palette.setColor(QPalette.WindowText, light_color)
            palette.setColor(QPalette.Base, QColor(30, 30, 30))
            palette.setColor(QPalette.AlternateBase, dark_color)
            palette.setColor(QPalette.ToolTipBase, light_color)
            palette.setColor(QPalette.ToolTipText, light_color)
            palette.setColor(QPalette.Text, light_color)
            palette.setColor(QPalette.Button, dark_color)
            palette.setColor(QPalette.ButtonText, light_color)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)

            # 统一样式表
            menu_style = """
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #b4b4b4;
                    border: none;
                }
                QMenuBar::item {
                    background-color: #2d2d2d;
                    color: #b4b4b4;
                    padding: 4px 8px;
                }
                QMenuBar::item:selected {
                    background-color: #2a82da;
                    color: black;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #b4b4b4;
                    border: 1px solid #555;
                }
                QMenu::item {
                    padding: 4px 20px;
                }
                QMenu::item:selected {
                    background-color: #2a82da;
                    color: black;
                }
                QGroupBox {
                    color: #b4b4b4;
                    border: 1px solid #555;
                    margin-top: 10px;
                    padding-top: 8px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ff6b6b;
                    border: 1px solid #555;
                }
                QProgressBar {
                    background-color: #333;
                    border: 1px solid #555;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #2a82da;
                }
                QLineEdit {
                    background-color: #333;
                    color: #b4b4b4;
                    border: 1px solid #555;
                    padding: 2px;
                }
                QComboBox {
                    background-color: #333;
                    color: #b4b4b4;
                    border: 1px solid #555;
                }
                QComboBox::drop-down {
                    border-left: 1px solid #555;
                }
                QCheckBox {
                    color: #b4b4b4;
                }
                QPushButton {
                    background-color: #333;
                    color: #b4b4b4;
                    border: 1px solid #555;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #444;
                }
                QPushButton:pressed {
                    background-color: #1e1e1e;
                }
            """
            self.error_log.setStyleSheet("background-color: #1e1e1e; color: #ff6b6b; border: 1px solid #555;")

        else:
            # Windows浅色模式样式（默认）
            self.app.setStyle("Fusion")
            palette = QPalette()

            menu_style = """
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #333;
                    border: none;
                }
                QMenuBar::item {
                    background-color: #f0f0f0;
                    color: #333;
                    padding: 4px 8px;
                }
                QMenuBar::item:selected {
                    background-color: #d0d0d0;
                    color: #000;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333;
                    border: 1px solid #ccc;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                    color: #000;
                }
                QGroupBox {
                    color: #333;
                    border: 1px solid #ccc;
                    margin-top: 10px;
                    padding-top: 8px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0 4px;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #d32f2f;
                    border: 1px solid #ccc;
                }
                QProgressBar {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #2196f3;
                }
                QLineEdit {
                    background-color: #fff;
                    color: #333;
                    border: 1px solid #ccc;
                    padding: 2px;
                }
                QComboBox {
                    background-color: #fff;
                    color: #333;
                    border: 1px solid #ccc;
                }
                QCheckBox {
                    color: #333;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333;
                    border: 1px solid #ccc;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """
            self.error_log.setStyleSheet("background-color: #ffffff; color: #d32f2f; border: 1px solid #ccc;")

        # 应用样式
        self.app.setPalette(palette)
        self.menu_bar.setStyleSheet(menu_style)
        self.setStyleSheet(menu_style)

    def load_theme(self):
        """加载主题设置（默认浅色）"""
        theme = self.current_theme
        logging.debug(f"加载主题设置：{theme}")

        if theme == "dark":
            self.apply_theme_style("dark")
        else:
            self.apply_theme_style("light")

        # 更新主题菜单选中标记
        self.update_menu_check_state()

    def change_theme(self, theme):
        """切换主题（仅浅色/深色）"""
        self.current_theme = theme
        self.settings.setValue("theme", theme)
        logging.debug(f"切换主题到：{theme}")

        self.apply_theme_style(theme)
        # 更新菜单选中状态
        self.update_menu_check_state()

    def change_language(self, lang):
        """切换语言并更新菜单标记"""
        self.current_lang = lang
        self.settings.setValue("language", lang)
        self.translator.load_translations(lang)

        # 重新初始化UI并更新菜单标记
        self.init_ui()
        self.load_theme()

    def update_menu_check_state(self):
        """更新菜单选中标记（✓）"""
        # 更新主题菜单
        if hasattr(self, 'light_theme_action'):
            self.light_theme_action.setChecked(self.current_theme == "light")
            self.dark_theme_action.setChecked(self.current_theme == "dark")

        # 更新语言菜单
        if hasattr(self, 'chinese_action'):
            self.chinese_action.setChecked(self.current_lang == "zh_CN")
            self.english_action.setChecked(self.current_lang == "en")

    def init_ui(self):
        """初始化Windows界面（移除跟随系统+添加选中标记）"""
        # 设置Windows字体
        font = QFont()
        font.setFamily("SimHei")
        self.setFont(font)

        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)

        # 文件菜单
        self.file_menu = QMenu(self.tr("文件(&F)"))
        self.menu_bar.addMenu(self.file_menu)
        self.exit_action = QAction(self.tr("退出(&X)"), self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # 视图菜单（移除跟随系统）
        self.view_menu = QMenu(self.tr("视图(&V)"))
        self.menu_bar.addMenu(self.view_menu)

        # 主题选项（仅浅色/深色）
        self.theme_menu = QMenu(self.tr("主题"))
        self.view_menu.addMenu(self.theme_menu)

        # 浅色模式（添加选中标记）
        self.light_theme_action = QAction(self.tr("浅色模式"), self)
        self.light_theme_action.setCheckable(True)  # 可选中
        self.light_theme_action.triggered.connect(lambda: self.change_theme('light'))
        self.theme_menu.addAction(self.light_theme_action)

        # 深色模式（添加选中标记）
        self.dark_theme_action = QAction(self.tr("深色模式"), self)
        self.dark_theme_action.setCheckable(True)  # 可选中
        self.dark_theme_action.triggered.connect(lambda: self.change_theme('dark'))
        self.theme_menu.addAction(self.dark_theme_action)

        # 语言菜单（添加选中标记）
        self.lang_menu = QMenu(self.tr("语言(&L)"))
        self.menu_bar.addMenu(self.lang_menu)

        self.chinese_action = QAction("中文", self)
        self.chinese_action.setCheckable(True)  # 可选中
        self.chinese_action.triggered.connect(lambda: self.change_language('zh_CN'))
        self.lang_menu.addAction(self.chinese_action)

        self.english_action = QAction("English", self)
        self.english_action.setCheckable(True)  # 可选中
        self.english_action.triggered.connect(lambda: self.change_language('en'))
        self.lang_menu.addAction(self.english_action)

        # 帮助菜单
        self.help_menu = QMenu(self.tr("帮助(&H)"))
        self.menu_bar.addMenu(self.help_menu)
        self.about_action = QAction(self.tr("关于(&A)"), self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)

        # 主布局
        main_layout = QVBoxLayout()

        self.title_label = QLabel(self.tr("时间切片照片生成器"))
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        # 输入设置
        self.input_group = QGroupBox(self.tr("输入设置"))
        input_layout = QVBoxLayout()

        input_dir_layout = QHBoxLayout()
        self.input_dir_label = QLabel(self.tr("输入目录:"))
        self.input_dir_edit = QLineEdit()
        self.input_dir_edit.setPlaceholderText(self.tr("选择包含照片的目录"))
        self.input_dir_btn = QPushButton(self.tr("浏览..."))
        self.input_dir_btn.clicked.connect(self.select_input_dir)
        input_dir_layout.addWidget(self.input_dir_label)
        input_dir_layout.addWidget(self.input_dir_edit)
        input_dir_layout.addWidget(self.input_dir_btn)
        input_layout.addLayout(input_dir_layout)

        output_dir_layout = QHBoxLayout()
        self.output_dir_label = QLabel(self.tr("输出目录:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText(self.tr("选择结果保存目录"))
        self.output_dir_btn = QPushButton(self.tr("浏览..."))
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(self.output_dir_label)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        input_layout.addLayout(output_dir_layout)

        self.input_group.setLayout(input_layout)
        main_layout.addWidget(self.input_group)

        # 切片设置
        self.slice_group = QGroupBox(self.tr("切片设置"))
        slice_layout = QVBoxLayout()

        type_layout = QHBoxLayout()
        self.type_label = QLabel(self.tr("切片类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            self.tr("垂直切片"),
            self.tr("水平切片"),
            self.tr("圆形扇形切片"),
            self.tr("椭圆形扇形切片"),
            self.tr("椭圆形环带切片"),
            self.tr("矩形环带切片"),
            self.tr("圆形环带切片"),
            self.tr("垂直S型曲线"),
            self.tr("水平S型曲线")
        ])
        type_layout.addWidget(self.type_label)
        type_layout.addWidget(self.type_combo)
        slice_layout.addLayout(type_layout)

        position_layout = QHBoxLayout()
        self.position_label = QLabel(self.tr("位置设置:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems([
            self.tr("左侧"),
            self.tr("居中"),
            self.tr("右侧"),
            self.tr("顶部"),
            self.tr("底部")
        ])
        self.position_combo.setEnabled(True)
        self.type_combo.currentIndexChanged.connect(self.update_controls_state)
        position_layout.addWidget(self.position_label)
        position_layout.addWidget(self.position_combo)
        slice_layout.addLayout(position_layout)

        options_layout = QHBoxLayout()
        self.linear_check = QCheckBox(self.tr("线性模式"))
        self.reverse_check = QCheckBox(self.tr("逆序排序"))
        self.auto_open_check = QCheckBox(self.tr("完成后自动打开图片"))
        options_layout.addWidget(self.linear_check)
        options_layout.addWidget(self.reverse_check)
        options_layout.addWidget(self.auto_open_check)
        slice_layout.addLayout(options_layout)

        self.slice_group.setLayout(slice_layout)
        main_layout.addWidget(self.slice_group)

        # 进度信息
        self.progress_group = QGroupBox(self.tr("进度信息"))
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(self.tr("已处理 %v/%m 张"))
        progress_layout.addWidget(self.progress_bar)

        self.error_log = QTextEdit()
        self.error_log.setReadOnly(True)
        self.error_log.setPlaceholderText(self.tr("错误日志将显示在这里..."))
        progress_layout.addWidget(self.error_log)

        self.progress_group.setLayout(progress_layout)
        main_layout.addWidget(self.progress_group)

        # 生成按钮
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton(self.tr("生成时间切片"))
        self.process_btn.clicked.connect(self.process_images)
        self.process_btn.setMinimumHeight(40)
        button_layout.addWidget(self.process_btn)
        main_layout.addLayout(button_layout)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage(self.tr("准备就绪"))
        self.update_controls_state(0)

        # 初始化菜单选中状态
        self.update_menu_check_state()

    def select_input_dir(self):
        """选择输入目录"""
        dir_path = QFileDialog.getExistingDirectory(self, self.tr("选择输入目录"))
        if dir_path:
            self.input_dir_edit.setText(dir_path)

    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, self.tr("选择输出目录"))
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def update_controls_state(self, index):
        """更新控件状态"""
        slice_type = self.type_combo.currentText()
        position_enabled = slice_type in [
            self.tr("垂直切片"),
            self.tr("水平切片"),
            self.tr("垂直S型曲线"),
            self.tr("水平S型曲线")
        ]
        self.position_combo.setEnabled(position_enabled)

    def process_images(self):
        """处理图片"""
        input_dir = self.input_dir_edit.text()
        output_dir = self.output_dir_edit.text()

        if not input_dir:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择输入目录"))
            return

        if not output_dir:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择输出目录"))
            return

        # 映射切片类型
        slice_type_map = {
            self.tr("垂直切片"): "vertical",
            self.tr("水平切片"): "horizontal",
            self.tr("圆形扇形切片"): "circular_sector",
            self.tr("椭圆形扇形切片"): "elliptical_sector",
            self.tr("椭圆形环带切片"): "elliptical_band",
            self.tr("矩形环带切片"): "rectangular_band",
            self.tr("圆形环带切片"): "circular_band",
            self.tr("垂直S型曲线"): "vertical_s",
            self.tr("水平S型曲线"): "horizontal_s"
        }

        slice_type = slice_type_map.get(self.type_combo.currentText(), "vertical")

        # 映射位置
        position_map = {
            self.tr("左侧"): "left",
            self.tr("居中"): "center",
            self.tr("右侧"): "right",
            self.tr("顶部"): "top",
            self.tr("底部"): "bottom"
        }
        position = position_map.get(self.position_combo.currentText(), "center")

        # 准备参数
        params = {
            'input_dir': input_dir,
            'output_dir': output_dir,
            'slice_type': slice_type,
            'position': position,
            'linear': self.linear_check.isChecked(),
            'reverse': self.reverse_check.isChecked()
        }

        # 重置状态
        self.error_log.clear()
        self.process_btn.setEnabled(False)

        # 加载图片
        from utils import load_images
        try:
            images = load_images(input_dir, self.reverse_check.isChecked())
            self.total_images = len(images)
            self.progress_bar.setRange(0, self.total_images)
            self.progress_bar.setValue(0)

            if self.total_images == 0:
                QMessageBox.warning(self, self.tr("警告"), self.tr("输入目录中没有找到图片"))
                self.process_btn.setEnabled(True)
                return
        except Exception as e:
            self.error_log.append(f"{self.tr('错误:')} {str(e)}")
            self.process_btn.setEnabled(True)
            return

        # 启动线程
        self.worker = TimesliceWorker(params)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.error_signal.connect(self.process_error)
        self.worker.log_signal.connect(self.log_message)
        self.worker.start()

    def update_progress(self, value):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(f"{self.tr('已处理')} {value}/{self.total_images} {self.tr('张图片')}")

    def log_message(self, message):
        """日志消息"""
        self.status_bar.showMessage(message)

    def process_error(self, error_msg):
        """处理错误"""
        self.error_log.append(f"{self.tr('错误:')} {error_msg}")
        self.process_btn.setEnabled(True)
        self.status_bar.showMessage(self.tr("处理出错"))

    def process_finished(self, output_path):
        """处理完成"""
        self.status_bar.showMessage(f"{self.tr('时间切片已保存至:')} {output_path}")
        self.process_btn.setEnabled(True)

        # Windows自动打开图片
        if self.auto_open_check.isChecked():
            try:
                os.startfile(output_path)
            except Exception as e:
                self.error_log.append(f"{self.tr('无法打开图片:')} {str(e)}")

    def show_about(self):
        """关于对话框"""
        QMessageBox.about(self, self.tr("关于"),
                          f"{self.tr('时间切片照片生成器')}\n\n"
                          f"{self.tr('版本 4.2')}\n"
                          f"{self.tr('适用于Windows系统的时间切片照片生成工具')}")

    def closeEvent(self, event):
        """关闭窗口"""
        self.theme_check_timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
    app.setStyle("Fusion")
    window = TimesliceGUI()
    window.show()
    sys.exit(app.exec_())