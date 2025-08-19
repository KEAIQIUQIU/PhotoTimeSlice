# gui.py
import os
import platform
import subprocess
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QCheckBox, QFileDialog, QProgressBar,
                             QGroupBox, QMessageBox, QTextEdit, QMenuBar, QMenu, QAction, QSpinBox, QSlider)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent, QTranslator, QLocale, QSettings
from PyQt5.QtGui import QPalette, QColor

# Add current directory to sys.path
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from cli import run_timeslice


class LogEvent(QEvent):
    """Custom event for thread-safe log updates"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, text):
        super().__init__(LogEvent.EVENT_TYPE)
        self.text = text


class TimesliceWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            self.progress_signal.emit(0, "开始处理图像...")
            output_path = run_timeslice(
                input_dir=self.params['input_dir'],
                output_dir=self.params['output_dir'],
                slice_type=self.params['slice_type'],
                position=self.params['position'],
                linear=self.params['linear'],
                reverse=self.params['reverse']
            )
            self.progress_signal.emit(100, "处理完成!")
            self.finished_signal.emit(output_path)
        except Exception as e:
            self.error_signal.emit(str(e))


class TimesliceGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("TimeslicePhotoGenerator", "Settings")
        self.translator = QTranslator()
        self.app = QApplication.instance()

        self.init_ui()
        self.load_language()
        self.load_theme()

        self.setWindowTitle(self.tr("时间切片照片生成器"))
        self.setGeometry(100, 100, 800, 600)

        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.current_output_path = ""

        self.worker = None

    def init_ui(self):
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)

        # 文件菜单
        self.file_menu = QMenu(self.tr("文件(&F)"))
        self.menu_bar.addMenu(self.file_menu)
        self.exit_action = QAction(self.tr("退出(&X)"), self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # 视图菜单 - 新增主题选项
        self.view_menu = QMenu(self.tr("视图(&V)"))
        self.menu_bar.addMenu(self.view_menu)

        # 主题选项
        self.theme_menu = QMenu(self.tr("主题"))
        self.view_menu.addMenu(self.theme_menu)

        self.light_theme_action = QAction(self.tr("浅色模式"), self)
        self.light_theme_action.triggered.connect(lambda: self.change_theme('light'))
        self.theme_menu.addAction(self.light_theme_action)

        self.dark_theme_action = QAction(self.tr("深色模式"), self)
        self.dark_theme_action.triggered.connect(lambda: self.change_theme('dark'))
        self.theme_menu.addAction(self.dark_theme_action)

        self.system_theme_action = QAction(self.tr("跟随系统"), self)
        self.system_theme_action.triggered.connect(lambda: self.change_theme('system'))
        self.theme_menu.addAction(self.system_theme_action)

        # 语言菜单
        self.lang_menu = QMenu(self.tr("语言(&L)"))
        self.menu_bar.addMenu(self.lang_menu)
        self.chinese_action = QAction("中文", self)
        self.chinese_action.triggered.connect(lambda: self.change_language('zh'))
        self.lang_menu.addAction(self.chinese_action)
        self.english_action = QAction("English", self)
        self.english_action.triggered.connect(lambda: self.change_language('en'))
        self.lang_menu.addAction(self.english_action)

        # 帮助菜单
        self.help_menu = QMenu(self.tr("帮助(&H)"))
        self.menu_bar.addMenu(self.help_menu)
        self.about_action = QAction(self.tr("关于(&A)"), self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.title_label = QLabel(self.tr("时间切片照片生成器"))
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

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

        self.slice_group = QGroupBox(self.tr("切片设置"))
        slice_layout = QVBoxLayout()
        type_layout = QHBoxLayout()
        self.type_label = QLabel(self.tr("切片类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            self.tr("垂直切片"),
            self.tr("水平切片"),
            self.tr("圆形扇形切片"),  # 修改为"圆形扇形切片"
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
        self.linear_check.stateChanged.connect(self.update_position_state)
        self.reverse_check = QCheckBox(self.tr("逆序排序"))
        self.auto_open_check = QCheckBox(self.tr("完成后自动打开图片"))
        options_layout.addWidget(self.linear_check)
        options_layout.addWidget(self.reverse_check)
        options_layout.addWidget(self.auto_open_check)
        slice_layout.addLayout(options_layout)

        self.slice_group.setLayout(slice_layout)
        main_layout.addWidget(self.slice_group)

        self.type_combo.currentIndexChanged.connect(self.update_controls_state)

        self.progress_group = QGroupBox(self.tr("进度信息"))
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        self.progress_group.setLayout(progress_layout)
        main_layout.addWidget(self.progress_group)

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
        self.status_bar.showMessage(self.tr("准备就緒"))
        self.redirect_output()
        self.update_controls_state(0)

    def load_theme(self):
        """加载保存的主题设置"""
        theme = self.settings.value("theme", "system")
        self.change_theme(theme)

    def change_theme(self, theme):
        """更改应用程序主题"""
        self.settings.setValue("theme", theme)

        if theme == 'system':
            # 检测系统主题
            if platform.system() == 'Darwin':  # macOS
                try:
                    mode = subprocess.check_output(['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                                                   stderr=subprocess.DEVNULL).decode().strip()
                    theme = 'dark' if mode == 'Dark' else 'light'
                except:
                    theme = 'light'  # 默认为浅色模式
            elif platform.system() == 'Windows':  # Windows
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                         r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                    theme = 'light' if value == 1 else 'dark'
                except:
                    theme = 'light'  # 默认为浅色模式
            else:  # Linux和其他系统
                theme = 'light'  # 默认为浅色模式

        # 应用主题
        self.apply_theme(theme)

    def apply_theme(self, theme):
        """应用具体的主题样式"""
        if theme == 'dark':
            # 深色模式样式
            self.setStyleSheet("""
                QMainWindow, QDialog, QWidget {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QGroupBox {
                    background-color: #34495e;
                    border: 1px solid #3498db;
                    border-radius: 8px;
                    margin-top: 1ex;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 5px;
                    background-color: #34495e;
                    color: #3498db;
                }
                QLabel {
                    color: #ecf0f1;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #7f8c8d;
                }
                QComboBox, QLineEdit {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    border-radius: 4px;
                    padding: 5px;
                }
                QTextEdit {
                    background-color: #1a252f;
                    color: #ecf0f1;
                    border: 1px solid #3498db;
                    border-radius: 4px;
                    font-family: Consolas, Monaco, monospace;
                }
                QProgressBar {
                    border: 1px solid #3498db;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #2c3e50;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    width: 10px;
                }
                QMenuBar {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QMenu {
                    background-color: #34495e;
                    color: #ecf0f1;
                    border: 1px solid #3498db;
                }
                QMenu::item:selected {
                    background-color: #3498db;
                }
            """)
        else:
            # 浅色模式样式
            self.setStyleSheet("""
                QMainWindow, QDialog, QWidget {
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QGroupBox {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 8px;
                    margin-top: 1ex;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 5px;
                    background-color: #ffffff;
                    color: #2c3e50;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                }
                QComboBox, QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 5px;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    font-family: Consolas, Monaco, monospace;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #ffffff;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    width: 10px;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                }
                QMenu::item:selected {
                    background-color: #3498db;
                    color: white;
                }
            """)

        # 更新标题颜色以适应主题
        if theme == 'dark':
            self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        else:
            self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")

    def load_language(self):
        lang = self.settings.value("language", "zh")
        self.change_language(lang)

    def change_language(self, lang):
        self.settings.setValue("language", lang)
        self.retranslate_ui()

    def retranslate_ui(self):
        lang = self.settings.value("language", "zh")

        self.file_menu.setTitle(self.tr("文件(&F)") if lang == "zh" else "File(&F)")
        self.exit_action.setText(self.tr("退出(&X)") if lang == "zh" else "Exit(&X)")
        self.lang_menu.setTitle(self.tr("语言(&L)") if lang == "zh" else "Language(&L)")
        self.chinese_action.setText("中文")
        self.english_action.setText("English")
        self.help_menu.setTitle(self.tr("帮助(&H)") if lang == "zh" else "Help(&H)")
        self.about_action.setText(self.tr("关于(&A)") if lang == "zh" else "About(&A)")
        self.view_menu.setTitle(self.tr("视图(&V)") if lang == "zh" else "View(&V)")
        self.theme_menu.setTitle(self.tr("主题") if lang == "zh" else "Theme")
        self.light_theme_action.setText(self.tr("浅色模式") if lang == "zh" else "Light Mode")
        self.dark_theme_action.setText(self.tr("深色模式") if lang == "zh" else "Dark Mode")
        self.system_theme_action.setText(self.tr("跟随系统") if lang == "zh" else "System Default")

        self.setWindowTitle(self.tr("时间切片照片生成器") if lang == "zh" else "Time Slice Photo Generator")
        self.title_label.setText(self.tr("时间切片照片生成器") if lang == "zh" else "Time Slice Photo Generator")
        self.input_group.setTitle(self.tr("输入设置") if lang == "zh" else "Input Settings")
        self.input_dir_label.setText(self.tr("输入目录:") if lang == "zh" else "Input Directory:")
        self.input_dir_edit.setPlaceholderText(
            self.tr("选择包含照片的目录") if lang == "zh" else "Select directory containing photos")
        self.output_dir_label.setText(self.tr("输出目录:") if lang == "zh" else "Output Directory:")
        self.output_dir_edit.setPlaceholderText(
            self.tr("选择结果保存目录") if lang == "zh" else "Select directory to save result")

        self.slice_group.setTitle(self.tr("切片设置") if lang == "zh" else "Slice Settings")
        self.type_label.setText(self.tr("切片类型:") if lang == "zh" else "Slice Type:")
        self.position_label.setText(self.tr("位置设置:") if lang == "zh" else "Position:")

        current_slice_type = self.type_combo.currentIndex()
        self.type_combo.clear()
        if lang == "zh":
            self.type_combo.addItems([
                "垂直切片",
                "水平切片",
                "圆形扇形切片",  # 修改为"圆形扇形切片"
                "椭圆形扇形切片",
                "椭圆形环带切片",
                "矩形环带切片",
                "圆形环带切片",
                "垂直S型曲线",
                "水平S型曲线"
            ])
        else:
            self.type_combo.addItems([
                "Vertical Slice",
                "Horizontal Slice",
                "Circular Sector Slice",  # 修改为"Circular Sector Slice"
                "Elliptical Sector Slice",
                "Elliptical Band Slice",
                "Rectangular Band Slice",
                "Circular Band Slice",
                "Vertical S-Curve",
                "Horizontal S-Curve"
            ])
        self.type_combo.setCurrentIndex(current_slice_type)

        current_position = self.position_combo.currentIndex()
        self.position_combo.clear()
        if lang == "zh":
            self.position_combo.addItems(["左侧", "居中", "右侧", "顶部", "底部"])
        else:
            self.position_combo.addItems(["Left", "Center", "Right", "Top", "Bottom"])
        self.position_combo.setCurrentIndex(current_position)

        self.linear_check.setText(self.tr("线性模式") if lang == "zh" else "Linear Mode")
        self.reverse_check.setText(self.tr("逆序排序") if lang == "zh" else "Reverse Order")
        self.auto_open_check.setText(
            self.tr("完成后自动打开图片") if lang == "zh" else "Auto open image after completion")
        self.progress_group.setTitle(self.tr("进度信息") if lang == "zh" else "Progress Information")
        self.process_btn.setText(self.tr("生成时间切片") if lang == "zh" else "Generate Time Slice")
        self.status_bar.showMessage(self.tr("准备就绪") if lang == "zh" else "Ready")
        self.update_controls_state(0)

    def redirect_output(self):
        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        try:
            if hasattr(self, 'log_text') and self.log_text and QApplication.instance():
                QApplication.postEvent(self, LogEvent(text))
            else:
                self.original_stdout.write(text)
        except Exception as e:
            try:
                self.original_stdout.write(f"Error in write: {str(e)}\n")
                self.original_stdout.write(text)
            except:
                pass

    def flush(self):
        try:
            if hasattr(self, 'original_stdout') and self.original_stdout:
                self.original_stdout.flush()
        except:
            pass

    def event(self, event):
        if event.type() == LogEvent.EVENT_TYPE:
            self.log_text.append(event.text)
            return True
        return super().event(event)

    def closeEvent(self, event):
        try:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
        except:
            pass
        super().closeEvent(event)

    def show_about(self):
        lang = self.settings.value("language", "zh")
        if lang == "zh":
            title = "关于时间切片照片生成器"
            message = ("时间切片照片生成器 v3.4\n\n"
                       "一个用于创建时间切片(time slice)照片的工具，"
                       "可以从一系列连续拍摄的照片中生成具有时间维度效果的合成图像。\n\n"
                       "支持多种时间切片模式，包括垂直切片、水平切片、"
                       "圆形扇形切片、椭圆形扇形切片以及S型曲线效果。")  # 更新描述
        else:
            title = "About Time Slice Photo Generator"
            message = ("Time Slice Photo Generator v3.4\n\n"
                       "A tool for creating time slice photos that generates composite images "
                       "with time dimension effects from a series of continuously taken photos.\n\n"
                       "Supports multiple time slice modes including vertical, horizontal, "
                       "circular sector, elliptical sector, and S-curve effects.")  # 更新描述
        QMessageBox.about(self, title, message)

    def select_input_dir(self):
        lang = self.settings.value("language", "zh")
        title = self.tr("选择输入目录") if lang == "zh" else "Select Input Directory"
        dir_path = QFileDialog.getExistingDirectory(self, title)
        if dir_path:
            self.input_dir_edit.setText(dir_path)
            if lang == "zh":
                self.log(f"输入目录设置为: {dir_path}")
            else:
                self.log(f"Input directory set to: {dir_path}")

    def select_output_dir(self):
        lang = self.settings.value("language", "zh")
        title = self.tr("选择输出目录") if lang == "zh" else "Select Output Directory"
        dir_path = QFileDialog.getExistingDirectory(self, title)
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            if lang == "zh":
                self.log(f"输出目录设置为: {dir_path}")
            else:
                self.log(f"Output directory set to: {dir_path}")

    def update_controls_state(self, index):
        lang = self.settings.value("language", "zh")
        slice_type = self.type_combo.currentText()

        if slice_type in ["垂直切片", "Vertical Slice"]:
            current_position = self.position_combo.currentIndex()
            self.position_combo.clear()
            if lang == "zh":
                positions = ["左侧", "居中", "右侧"]
            else:
                positions = ["Left", "Center", "Right"]
            self.position_combo.addItems(positions)
            if 0 <= current_position < len(positions):
                self.position_combo.setCurrentIndex(current_position)
            else:
                self.position_combo.setCurrentIndex(1)
            self.position_combo.setEnabled(not self.linear_check.isChecked())
            self.linear_check.setEnabled(True)
            if lang == "zh":
                self.linear_check.setToolTip("启用线性模式：每张图片取不同部位")
            else:
                self.linear_check.setToolTip("Enable linear mode: take different parts from each image")

        elif slice_type in ["水平切片", "Horizontal Slice"]:
            current_position = self.position_combo.currentIndex()
            self.position_combo.clear()
            if lang == "zh":
                positions = ["顶部", "居中", "底部"]
            else:
                positions = ["Top", "Center", "Bottom"]
            self.position_combo.addItems(positions)
            if 0 <= current_position < len(positions):
                self.position_combo.setCurrentIndex(current_position)
            else:
                self.position_combo.setCurrentIndex(1)
            self.position_combo.setEnabled(not self.linear_check.isChecked())
            self.linear_check.setEnabled(True)
            if lang == "zh":
                self.linear_check.setToolTip("启用线性模式：每张图片取不同部位")
            else:
                self.linear_check.setToolTip("Enable linear mode: take different parts from each image")

        elif slice_type in ["圆形扇形切片", "Circular Sector Slice"]:  # 更新类型名称
            self.position_combo.clear()
            if lang == "zh":
                self.position_combo.addItems(["居中"])
            else:
                self.position_combo.addItems(["Center"])
            self.position_combo.setCurrentIndex(0)
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(True)
            if lang == "zh":
                self.linear_check.setToolTip("启用线性模式：控制扇形大小变化")
            else:
                self.linear_check.setToolTip("Enable linear mode: control sector size changes")

        elif slice_type in ["椭圆形扇形切片", "Elliptical Sector Slice"]:
            self.position_combo.clear()
            if lang == "zh":
                self.position_combo.addItems(["居中"])
            else:
                self.position_combo.addItems(["Center"])
            self.position_combo.setCurrentIndex(0)
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(True)
            if lang == "zh":
                self.linear_check.setToolTip("启用线性模式：控制扇形大小变化")
            else:
                self.linear_check.setToolTip("Enable linear mode: control sector size changes")

        elif slice_type in ["垂直S型曲线", "Vertical S-Curve", "水平S型曲线", "Horizontal S-Curve"]:
            self.position_combo.clear()
            if lang == "zh":
                self.position_combo.addItems(["无"])
            else:
                self.position_combo.addItems(["None"])
            self.position_combo.setCurrentIndex(0)
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(False)
            self.linear_check.setChecked(False)
            if lang == "zh":
                self.linear_check.setToolTip("此切片类型不支持位置和线性模式")
            else:
                self.linear_check.setToolTip("Position and linear mode not supported for this slice type")

        else:
            self.position_combo.clear()
            if lang == "zh":
                self.position_combo.addItems(["居中"])
            else:
                self.position_combo.addItems(["Center"])
            self.position_combo.setCurrentIndex(0)
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(False)
            self.linear_check.setChecked(False)
            if lang == "zh":
                self.linear_check.setToolTip("此切片类型不支持线性模式")
            else:
                self.linear_check.setToolTip("Linear mode not supported for this slice type")

    def update_position_state(self):
        lang = self.settings.value("language", "zh")
        slice_type = self.type_combo.currentText()
        if slice_type in ["垂直切片", "Vertical Slice", "水平切片", "Horizontal Slice"]:
            self.position_combo.setEnabled(not self.linear_check.isChecked())
            if self.linear_check.isChecked():
                if lang == "zh":
                    self.position_combo.setCurrentText("居中")
                else:
                    self.position_combo.setCurrentText("Center")
        self.update_controls_state(0)

    def log(self, message):
        self.log_text.append(message)
        self.status_bar.showMessage(message)

    def validate_inputs(self):
        lang = self.settings.value("language", "zh")
        input_dir = self.input_dir_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        if not input_dir:
            if lang == "zh":
                QMessageBox.warning(self, "输入错误", "请选择输入目录")
            else:
                QMessageBox.warning(self, "Input Error", "Please select input directory")
            return False

        if not os.path.exists(input_dir):
            if lang == "zh":
                QMessageBox.warning(self, "输入错误", f"输入目录不存在: {input_dir}")
            else:
                QMessageBox.warning(self, "Input Error", f"Input directory does not exist: {input_dir}")
            return False

        if not output_dir:
            if lang == "zh":
                QMessageBox.warning(self, "输入错误", "请选择输出目录")
            else:
                QMessageBox.warning(self, "Input Error", "Please select output directory")
            return False

        return True

    def get_position_value(self):
        position = self.position_combo.currentText()
        if position in ["左侧", "Left"]:
            return "left"
        elif position in ["顶部", "Top"]:
            return "top"
        elif position in ["居中", "Center"]:
            return "center"
        elif position in ["右侧", "Right"]:
            return "right"
        elif position in ["底部", "Bottom"]:
            return "bottom"
        else:
            return "center"

    def get_slice_type_value(self):
        slice_type = self.type_combo.currentText()
        if slice_type in ["垂直切片", "Vertical Slice"]:
            return "vertical"
        elif slice_type in ["水平切片", "Horizontal Slice"]:
            return "horizontal"
        elif slice_type in ["圆形扇形切片", "Circular Sector Slice"]:  # 更新类型名称
            return "circular_sector"  # 更新为circular_sector
        elif slice_type in ["椭圆形扇形切片", "Elliptical Sector Slice"]:
            return "elliptical_sector"
        elif slice_type in ["椭圆形环带切片", "Elliptical Band Slice"]:
            return "elliptical_band"
        elif slice_type in ["矩形环带切片", "Rectangular Band Slice"]:
            return "rectangular_band"
        elif slice_type in ["圆形环带切片", "Circular Band Slice"]:
            return "circular_band"
        elif slice_type in ["垂直S型曲线", "Vertical S-Curve"]:
            return "vertical_s"
        elif slice_type in ["水平S型曲线", "Horizontal S-Curve"]:
            return "horizontal_s"

    def process_images(self):
        lang = self.settings.value("language", "zh")
        if not self.validate_inputs():
            return

        params = {
            'input_dir': self.input_dir_edit.text().strip(),
            'output_dir': self.output_dir_edit.text().strip(),
            'slice_type': self.get_slice_type_value(),
            'position': self.get_position_value(),
            'linear': self.linear_check.isChecked(),
            'reverse': self.reverse_check.isChecked()
        }

        if lang == "zh":
            self.log("开始处理图像...")
            self.log(f"切片类型: {params['slice_type']}")
            self.log(f"位置: {params['position']}")
            self.log(f"线性模式: {'开启' if params['linear'] else '关闭'}")
            self.log(f"逆序排序: {'开启' if params['reverse'] else '关闭'}")
        else:
            self.log("Starting image processing...")
            self.log(f"Slice type: {params['slice_type']}")
            self.log(f"Position: {params['position']}")
            self.log(f"Linear mode: {'Enabled' if params['linear'] else 'Disabled'}")
            self.log(f"Reverse order: {'Enabled' if params['reverse'] else 'Disabled'}")

        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = TimesliceWorker(params)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_process_finished)
        self.worker.error_signal.connect(self.on_process_error)
        self.worker.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.log(message)

    def on_process_finished(self, output_path):
        lang = self.settings.value("language", "zh")
        self.progress_bar.setValue(100)
        if lang == "zh":
            self.log("处理完成!")
            self.log(f"结果已保存至: {output_path}")
        else:
            self.log("Processing completed!")
            self.log(f"Result saved to: {output_path}")

        self.current_output_path = output_path
        self.process_btn.setEnabled(True)

        if self.auto_open_check.isChecked():
            self.open_image(output_path)

        if lang == "zh":
            QMessageBox.information(self, "完成", f"时间切片已成功生成并保存至:\n{output_path}")
        else:
            QMessageBox.information(self, "Completed", f"Time slice has been generated and saved to:\n{output_path}")

    def on_process_error(self, error_msg):
        lang = self.settings.value("language", "zh")
        if lang == "zh":
            self.log(f"错误: {error_msg}")
            QMessageBox.critical(self, "处理错误", f"处理过程中发生错误:\n{error_msg}")
        else:
            self.log(f"Error: {error_msg}")
            QMessageBox.critical(self, "Processing Error", f"An error occurred during processing:\n{error_msg}")
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(True)

    def open_image(self, image_path):
        lang = self.settings.value("language", "zh")
        if not image_path or not os.path.exists(image_path):
            if lang == "zh":
                self.log("错误: 无法打开不存在的图片文件")
            else:
                self.log("Error: Cannot open non-existent image file")
            return

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(image_path)
            elif system == "Darwin":
                subprocess.call(["open", image_path])
            else:
                subprocess.call(["xdg-open", image_path])
            if lang == "zh":
                self.log(f"已使用默认程序打开图片: {image_path}")
            else:
                self.log(f"Opened image with default program: {image_path}")
        except Exception as e:
            if lang == "zh":
                self.log(f"打开图片时出错: {str(e)}")
                QMessageBox.warning(self, "打开图片错误", f"无法打开图片:\n{str(e)}")
            else:
                self.log(f"Error opening image: {str(e)}")
                QMessageBox.warning(self, "Open Image Error", f"Cannot open image:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    LogEvent.EVENT_TYPE = QEvent.registerEventType()
    window = TimesliceGUI()
    window.show()
    app.exec_()