import os
import platform
import subprocess
import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QCheckBox, QFileDialog, QProgressBar,
                             QGroupBox, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QEvent

# 添加当前目录到系统路径，确保打包后能正确导入模块
if getattr(sys, 'frozen', False):
    # 打包后的可执行文件
    application_path = sys._MEIPASS
else:
    # 正常开发环境
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

# 导入 timeslice_core 模块
from timeslice_core import run_timeslice


class LogEvent(QEvent):
    """自定义事件用于线程安全的日志更新"""
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
            # 运行核心功能
            self.progress_signal.emit(0, "开始处理图像...")

            # 调用真正的核心功能
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
        self.setWindowTitle("时间切片照片生成器")
        self.setGeometry(100, 100, 800, 600)

        # 保存原始标准输出和错误
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
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
        """)

        self.init_ui()
        self.worker = None
        self.current_output_path = ""  # 添加当前输出路径

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 标题
        title_label = QLabel("时间切片照片生成器")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 输入设置组
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()

        # 输入目录选择
        input_dir_layout = QHBoxLayout()
        input_dir_label = QLabel("输入目录:")
        self.input_dir_edit = QLineEdit()
        self.input_dir_edit.setPlaceholderText("选择包含照片的目录")
        input_dir_btn = QPushButton("浏览...")
        input_dir_btn.clicked.connect(self.select_input_dir)
        input_dir_layout.addWidget(input_dir_label)
        input_dir_layout.addWidget(self.input_dir_edit)
        input_dir_layout.addWidget(input_dir_btn)
        input_layout.addLayout(input_dir_layout)

        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("输出目录:")
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择结果保存目录")
        output_dir_btn = QPushButton("浏览...")
        output_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(output_dir_btn)
        input_layout.addLayout(output_dir_layout)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # 切片设置组
        slice_group = QGroupBox("切片设置")
        slice_layout = QVBoxLayout()

        # 切片类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("切片类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "垂直切片",
            "水平切片",
            "圆形切片",
            "椭圆形扇形切片",
            "椭圆形环带切片",
            "矩形环带切片",
            "圆形环带切片"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        slice_layout.addLayout(type_layout)

        # 位置设置
        position_layout = QHBoxLayout()
        position_label = QLabel("位置设置:")
        self.position_combo = QComboBox()
        self.position_combo.addItems(["左侧", "居中", "右侧", "顶部", "底部"])
        self.position_combo.setEnabled(True)
        self.type_combo.currentIndexChanged.connect(self.update_controls_state)
        position_layout.addWidget(position_label)
        position_layout.addWidget(self.position_combo)
        slice_layout.addLayout(position_layout)

        # 选项设置
        options_layout = QHBoxLayout()
        self.linear_check = QCheckBox("线性模式")
        self.linear_check.stateChanged.connect(self.update_position_state)
        self.reverse_check = QCheckBox("逆序排序")
        self.auto_open_check = QCheckBox("完成后自动打开图片")
        options_layout.addWidget(self.linear_check)
        options_layout.addWidget(self.reverse_check)
        options_layout.addWidget(self.auto_open_check)
        slice_layout.addLayout(options_layout)

        slice_group.setLayout(slice_layout)
        main_layout.addWidget(slice_group)

        # 进度和日志
        progress_group = QGroupBox("进度信息")
        progress_layout = QVBoxLayout()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # 日志框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # 操作按钮
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton("生成时间切片")
        self.process_btn.clicked.connect(self.process_images)
        self.process_btn.setMinimumHeight(40)
        button_layout.addWidget(self.process_btn)
        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 状态栏
        self.statusBar().showMessage("准备就绪")

        # 设置默认值
        self.current_output_path = ""
        self.update_controls_state(0)

        # 重定向输出（在UI初始化完成后）
        self.redirect_output()

    def redirect_output(self):
        """重定向标准输出到日志框"""
        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        """写入日志文本"""
        try:
            # 确保日志框存在且应用程序仍在运行
            if hasattr(self, 'log_text') and self.log_text and QApplication.instance():
                # 使用线程安全的方式更新UI
                QApplication.postEvent(self, LogEvent(text))
            else:
                # 回退到原始标准输出
                self.original_stdout.write(text)
        except Exception as e:
            # 错误处理 - 避免递归错误
            try:
                self.original_stdout.write(f"Error in write: {str(e)}\n")
                self.original_stdout.write(text)
            except:
                pass

    def flush(self):
        """必须实现的flush方法"""
        try:
            if hasattr(self, 'original_stdout') and self.original_stdout:
                self.original_stdout.flush()
        except:
            pass

    def event(self, event):
        """处理自定义事件"""
        if event.type() == LogEvent.EVENT_TYPE:
            self.log_text.append(event.text)
            return True
        return super().event(event)

    def closeEvent(self, event):
        """窗口关闭时恢复标准输出"""
        try:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
        except:
            pass
        super().closeEvent(event)

    def select_input_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if dir_path:
            self.input_dir_edit.setText(dir_path)
            self.log(f"输入目录设置为: {dir_path}")

    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.log(f"输出目录设置为: {dir_path}")

    def update_controls_state(self, index):
        """根据选择的切片类型更新控件状态"""
        slice_type = self.type_combo.currentText()

        # 位置设置状态
        if slice_type == "垂直切片":
            self.position_combo.clear()
            self.position_combo.addItems(["左侧", "居中", "右侧"])
            self.position_combo.setEnabled(not self.linear_check.isChecked())
            self.linear_check.setEnabled(True)
            self.linear_check.setToolTip("启用线性模式：每张图片取不同部位")
        elif slice_type == "水平切片":
            self.position_combo.clear()
            self.position_combo.addItems(["顶部", "居中", "底部"])
            self.position_combo.setEnabled(not self.linear_check.isChecked())
            self.linear_check.setEnabled(True)
            self.linear_check.setToolTip("启用线性模式：每张图片取不同部位")
        elif slice_type == "圆形切片":
            self.position_combo.clear()
            self.position_combo.addItems(["居中"])
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(True)
            self.linear_check.setToolTip("启用线性模式：控制扇形大小变化")
        elif slice_type == "椭圆形扇形切片":
            self.position_combo.clear()
            self.position_combo.addItems(["居中"])
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(True)
            self.linear_check.setToolTip("启用线性模式：控制扇形大小变化")
        else:  # 环带类切片
            self.position_combo.clear()
            self.position_combo.addItems(["居中"])
            self.position_combo.setEnabled(False)
            self.linear_check.setEnabled(False)
            self.linear_check.setChecked(False)
            self.linear_check.setToolTip("此切片类型不支持线性模式")

    def update_position_state(self):
        """更新位置设置的状态（当线性模式状态改变时调用）"""
        slice_type = self.type_combo.currentText()

        # 对于垂直和水平切片，线性模式启用时禁用位置设置
        if slice_type in ["垂直切片", "水平切片"]:
            self.position_combo.setEnabled(not self.linear_check.isChecked())

            # 如果启用了线性模式，设置位置为居中（但禁用选择）
            if self.linear_check.isChecked():
                self.position_combo.setCurrentText("居中")
        # 调用一次控件状态更新以确保其他控件状态正确
        self.update_controls_state(0)

    def log(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        self.statusBar().showMessage(message)

    def validate_inputs(self):
        """验证输入参数"""
        input_dir = self.input_dir_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        if not input_dir:
            QMessageBox.warning(self, "输入错误", "请选择输入目录")
            return False

        if not os.path.exists(input_dir):
            QMessageBox.warning(self, "输入错误", f"输入目录不存在: {input_dir}")
            return False

        if not output_dir:
            QMessageBox.warning(self, "输入错误", "请选择输出目录")
            return False

        return True

    def get_position_value(self):
        """将位置选项转换为核心函数需要的值"""
        position = self.position_combo.currentText()

        if position == "左侧":
            return "left"
        elif position == "顶部":
            return "top"
        elif position == "居中":
            return "center"
        elif position == "右侧":
            return "right"
        elif position == "底部":
            return "bottom"
        else:
            return "center"

    def get_slice_type_value(self):
        """将切片类型转换为核心函数需要的值"""
        slice_type = self.type_combo.currentText()
        if slice_type == "垂直切片":
            return "vertical"
        elif slice_type == "水平切片":
            return "horizontal"
        elif slice_type == "圆形切片":
            return "circular"
        elif slice_type == "椭圆形扇形切片":
            return "elliptical_sector"
        elif slice_type == "椭圆形环带切片":
            return "elliptical_band"
        elif slice_type == "矩形环带切片":
            return "rectangular_band"
        elif slice_type == "圆形环带切片":
            return "circular_band"
        else:
            return "circular"

    def process_images(self):
        """处理图像生成时间切片"""
        if not self.validate_inputs():
            return

        # 准备参数
        params = {
            'input_dir': self.input_dir_edit.text().strip(),
            'output_dir': self.output_dir_edit.text().strip(),
            'slice_type': self.get_slice_type_value(),
            'position': self.get_position_value(),
            'linear': self.linear_check.isChecked(),
            'reverse': self.reverse_check.isChecked()
        }

        self.log("开始处理图像...")
        self.log(f"切片类型: {params['slice_type']}")
        self.log(f"位置: {params['position']}")
        self.log(f"线性模式: {'开启' if params['linear'] else '关闭'}")
        self.log(f"逆序排序: {'开启' if params['reverse'] else '关闭'}")

        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # 创建工作线程
        self.worker = TimesliceWorker(params)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_process_finished)
        self.worker.error_signal.connect(self.on_process_error)
        self.worker.start()

    def update_progress(self, value, message):
        """更新进度条和日志"""
        self.progress_bar.setValue(value)
        self.log(message)

    def on_process_finished(self, output_path):
        """处理完成回调"""
        self.progress_bar.setValue(100)
        self.log("处理完成!")
        self.log(f"结果已保存至: {output_path}")

        # 更新当前输出路径
        self.current_output_path = output_path
        self.process_btn.setEnabled(True)

        # 检查是否需要自动打开图片
        if self.auto_open_check.isChecked():
            self.open_image(output_path)

        QMessageBox.information(self, "完成", f"时间切片已成功生成并保存至:\n{output_path}")

    def on_process_error(self, error_msg):
        """处理错误回调"""
        self.log(f"错误: {error_msg}")
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "处理错误", f"处理过程中发生错误:\n{error_msg}")

    def open_image(self, image_path):
        """使用系统默认程序打开图片"""
        if not image_path or not os.path.exists(image_path):
            self.log("错误: 无法打开不存在的图片文件")
            return

        try:
            # 根据操作系统使用不同的命令打开图片
            system = platform.system()
            if system == "Windows":
                os.startfile(image_path)
            elif system == "Darwin":  # macOS
                subprocess.call(["open", image_path])
            else:  # Linux
                subprocess.call(["xdg-open", image_path])
            self.log(f"已使用默认程序打开图片: {image_path}")
        except Exception as e:
            self.log(f"打开图片时出错: {str(e)}")
            QMessageBox.warning(self, "打开图片错误", f"无法打开图片:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建自定义事件类型
    LogEvent.EVENT_TYPE = QEvent.registerEventType()

    window = TimesliceGUI()
    window.show()
    app.exec_()