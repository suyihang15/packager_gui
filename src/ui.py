import os
import sys
import subprocess
import threading
import queue
from pathlib import Path

from src.core import run_packaging

try:
    from PySide6 import QtWidgets, QtCore
except Exception:
    QtWidgets = None


def run_app():
    if QtWidgets is None:
        return _run_tk()

    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if QtWidgets is not None:
    class MainWindow(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('Python 打包器')
            self.resize(1000, 680)
            self.log_queue = queue.Queue()
            self._build_ui()
            self._start_timer()

        def _build_ui(self):
            main_layout = QtWidgets.QVBoxLayout(self)

            form_layout = QtWidgets.QGridLayout()
            form_layout.setHorizontalSpacing(12)
            form_layout.setVerticalSpacing(12)

            self.script_edit = QtWidgets.QLineEdit()
            self.script_edit.setPlaceholderText('选择要打包的 Python 脚本文件')
            browse_script = QtWidgets.QPushButton('选择脚本')
            browse_script.clicked.connect(self._browse_script)
            form_layout.addWidget(QtWidgets.QLabel('主脚本：'), 0, 0)
            form_layout.addWidget(self.script_edit, 0, 1)
            form_layout.addWidget(browse_script, 0, 2)

            self.output_edit = QtWidgets.QLineEdit(str(Path.cwd() / 'dist'))
            browse_output = QtWidgets.QPushButton('选择输出目录')
            browse_output.clicked.connect(self._browse_output)
            form_layout.addWidget(QtWidgets.QLabel('输出目录：'), 1, 0)
            form_layout.addWidget(self.output_edit, 1, 1)
            form_layout.addWidget(browse_output, 1, 2)

            self.icon_edit = QtWidgets.QLineEdit()
            self.icon_edit.setPlaceholderText('可选：Windows .ico 图标文件')
            browse_icon = QtWidgets.QPushButton('选择图标')
            browse_icon.clicked.connect(self._browse_icon)
            form_layout.addWidget(QtWidgets.QLabel('图标文件：'), 2, 0)
            form_layout.addWidget(self.icon_edit, 2, 1)
            form_layout.addWidget(browse_icon, 2, 2)

            self.requirements_edit = QtWidgets.QLineEdit()
            self.requirements_edit.setPlaceholderText('可选：requirements.txt 文件')
            browse_requirements = QtWidgets.QPushButton('选择依赖文件')
            browse_requirements.clicked.connect(self._browse_requirements)
            form_layout.addWidget(QtWidgets.QLabel('依赖文件：'), 3, 0)
            form_layout.addWidget(self.requirements_edit, 3, 1)
            form_layout.addWidget(browse_requirements, 3, 2)

            self.onefile_cb = QtWidgets.QCheckBox('单文件模式 (--onefile)')
            self.onefile_cb.setChecked(True)
            self.windowed_cb = QtWidgets.QCheckBox('隐藏控制台 (--windowed)')
            self.venv_cb = QtWidgets.QCheckBox('使用隔离临时 venv 构建')
            self.venv_cb.setChecked(True)
            flags_layout = QtWidgets.QHBoxLayout()
            flags_layout.addWidget(self.onefile_cb)
            flags_layout.addWidget(self.windowed_cb)
            flags_layout.addWidget(self.venv_cb)
            flags_layout.addStretch()
            form_layout.addLayout(flags_layout, 4, 0, 1, 3)

            main_layout.addLayout(form_layout)

            resource_group = QtWidgets.QGroupBox('资源 / 附件文件 (.py 以外的资源、文件夹等)')
            resource_layout = QtWidgets.QVBoxLayout(resource_group)
            buttons_layout = QtWidgets.QHBoxLayout()
            add_file_btn = QtWidgets.QPushButton('添加文件')
            add_file_btn.clicked.connect(self._add_file)
            add_folder_btn = QtWidgets.QPushButton('添加文件夹')
            add_folder_btn.clicked.connect(self._add_folder)
            remove_btn = QtWidgets.QPushButton('移除选中项')
            remove_btn.clicked.connect(self._remove_selected)
            buttons_layout.addWidget(add_file_btn)
            buttons_layout.addWidget(add_folder_btn)
            buttons_layout.addWidget(remove_btn)
            buttons_layout.addStretch()
            resource_layout.addLayout(buttons_layout)

            self.resource_list = QtWidgets.QListWidget()
            self.resource_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            resource_layout.addWidget(self.resource_list)
            main_layout.addWidget(resource_group)

            action_layout = QtWidgets.QHBoxLayout()
            self.start_button = QtWidgets.QPushButton('开始打包')
            self.start_button.clicked.connect(self._start_pack)
            open_output_button = QtWidgets.QPushButton('打开输出目录')
            open_output_button.clicked.connect(self._open_output_folder)
            action_layout.addWidget(self.start_button)
            action_layout.addWidget(open_output_button)
            action_layout.addStretch()
            main_layout.addLayout(action_layout)

            self.log_view = QtWidgets.QPlainTextEdit()
            self.log_view.setReadOnly(True)
            self.log_view.setStyleSheet('background: #121212; color: #e8e8e8;')
            main_layout.addWidget(QtWidgets.QLabel('日志输出：'))
            main_layout.addWidget(self.log_view, 1)

            self.status_label = QtWidgets.QLabel('准备就绪。')
            main_layout.addWidget(self.status_label)

        def _start_timer(self):
            timer = QtCore.QTimer(self)
            timer.timeout.connect(self._flush_log)
            timer.start(150)

        def _flush_log(self):
            while not self.log_queue.empty():
                text = self.log_queue.get_nowait()
                self.log_view.appendPlainText(text)
                self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

        def _browse_script(self):
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择 Python 脚本', str(Path.cwd()), 'Python Files (*.py)')
            if path:
                self.script_edit.setText(path)

        def _browse_output(self):
            path = QtWidgets.QFileDialog.getExistingDirectory(self, '选择输出目录', str(Path.cwd()))
            if path:
                self.output_edit.setText(path)

        def _browse_icon(self):
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择图标(.ico)', str(Path.cwd()), 'Icon Files (*.ico)')
            if path:
                self.icon_edit.setText(path)

        def _browse_requirements(self):
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择 requirements.txt', str(Path.cwd()), 'Text Files (*.txt);;All Files (*)')
            if path:
                self.requirements_edit.setText(path)

        def _add_file(self):
            paths, _ = QtWidgets.QFileDialog.getOpenFileNames(self, '添加资源文件', str(Path.cwd()), 'All Files (*)')
            for p in paths:
                self._append_resource(p)

        def _add_folder(self):
            path = QtWidgets.QFileDialog.getExistingDirectory(self, '添加资源文件夹', str(Path.cwd()))
            if path:
                self._append_resource(path)

        def _append_resource(self, src_path):
            item = QtWidgets.QListWidgetItem(str(src_path))
            item.setData(QtCore.Qt.UserRole, str(src_path))
            self.resource_list.addItem(item)

        def _remove_selected(self):
            for item in self.resource_list.selectedItems():
                self.resource_list.takeItem(self.resource_list.row(item))

        def _open_output_folder(self):
            out = self.output_edit.text().strip()
            if not out:
                return
            path = Path(out).resolve()
            if not path.exists():
                return
            if sys.platform.startswith('win'):
                os.startfile(str(path))
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(path)])
            else:
                subprocess.Popen(['xdg-open', str(path)])

        def _log(self, message):
            self.log_queue.put(message)

        def _start_pack(self):
            script = self.script_edit.text().strip()
            if not script or not Path(script).exists():
                self._log('错误：请选择有效的主脚本文件。')
                self.status_label.setText('错误：主脚本无效。')
                return

            output_dir = self.output_edit.text().strip() or str(Path.cwd() / 'dist')
            icon_path = self.icon_edit.text().strip() or None
            requirements_path = self.requirements_edit.text().strip() or None
            if requirements_path and not Path(requirements_path).exists():
                self._log('警告：依赖文件不存在，将忽略。')
                requirements_path = None

            resources = []
            for i in range(self.resource_list.count()):
                src = self.resource_list.item(i).data(QtCore.Qt.UserRole)
                if src:
                    resources.append((src, Path(src).name))

            self.start_button.setEnabled(False)
            self.status_label.setText('打包中，请稍候...')
            self._log('开始打包进程...')

            def worker():
                try:
                    rc = run_packaging(
                        script=script,
                        output_dir=output_dir,
                        onefile=self.onefile_cb.isChecked(),
                        windowed=self.windowed_cb.isChecked(),
                        icon=icon_path,
                        datas=resources,
                        use_venv=self.venv_cb.isChecked(),
                        requirements=requirements_path,
                        cb=self._log,
                    )
                    if rc == 0:
                        self._log('打包成功，输出目录：' + output_dir)
                        self.status_label.setText('打包成功。')
                    else:
                        self._log(f'打包完成，但返回值为 {rc}。请检查日志。')
                        self.status_label.setText('打包完成，出现问题。')
                except Exception as e:
                    self._log('打包失败：' + str(e))
                    self.status_label.setText('打包失败。')
                finally:
                    self.start_button.setEnabled(True)

            threading.Thread(target=worker, daemon=True).start()


def _run_tk():
    import tkinter as tk
    from tkinter import filedialog, scrolledtext, messagebox

    root = tk.Tk()
    root.title('Python 打包器')
    root.geometry('900x620')

    def choose_file(text_var):
        path = filedialog.askopenfilename(filetypes=[('Python', '*.py'), ('All files', '*.*')])
        if path:
            text_var.set(path)

    def choose_folder(text_var):
        path = filedialog.askdirectory()
        if path:
            text_var.set(path)

    top_frame = tk.Frame(root)
    top_frame.pack(fill='x', padx=10, pady=8)

    script_var = tk.StringVar()
    tk.Label(top_frame, text='主脚本：').grid(row=0, column=0, sticky='w')
    tk.Entry(top_frame, textvariable=script_var, width=76).grid(row=0, column=1, padx=6)
    tk.Button(top_frame, text='浏览', command=lambda: choose_file(script_var)).grid(row=0, column=2)

    output_var = tk.StringVar(value=str(Path.cwd() / 'dist'))
    tk.Label(top_frame, text='输出目录：').grid(row=1, column=0, sticky='w')
    tk.Entry(top_frame, textvariable=output_var, width=76).grid(row=1, column=1, padx=6)
    tk.Button(top_frame, text='浏览', command=lambda: choose_folder(output_var)).grid(row=1, column=2)

    icon_var = tk.StringVar()
    tk.Label(top_frame, text='图标：').grid(row=2, column=0, sticky='w')
    tk.Entry(top_frame, textvariable=icon_var, width=76).grid(row=2, column=1, padx=6)
    tk.Button(top_frame, text='浏览', command=lambda: choose_file(icon_var)).grid(row=2, column=2)

    req_var = tk.StringVar()
    tk.Label(top_frame, text='requirements：').grid(row=3, column=0, sticky='w')
    tk.Entry(top_frame, textvariable=req_var, width=76).grid(row=3, column=1, padx=6)
    tk.Button(top_frame, text='浏览', command=lambda: choose_file(req_var)).grid(row=3, column=2)

    options_frame = tk.Frame(root)
    options_frame.pack(fill='x', padx=10)
    onefile_var = tk.BooleanVar(value=True)
    tk.Checkbutton(options_frame, text='单文件', variable=onefile_var).pack(side='left')
    windowed_var = tk.BooleanVar(value=False)
    tk.Checkbutton(options_frame, text='隐藏控制台', variable=windowed_var).pack(side='left')
    venv_var = tk.BooleanVar(value=True)
    tk.Checkbutton(options_frame, text='使用隔离 venv', variable=venv_var).pack(side='left')

    resource_frame = tk.LabelFrame(root, text='资源 / 附件')
    resource_frame.pack(fill='both', expand=True, padx=10, pady=8)

    resource_list = tk.Listbox(resource_frame, selectmode='extended', height=10)
    resource_list.pack(fill='both', expand=True, padx=6, pady=6)

    def add_resource_file():
        paths = filedialog.askopenfilenames(title='添加资源文件')
        for p in root.tk.splitlist(paths):
            resource_list.insert('end', p)

    def add_resource_folder():
        p = filedialog.askdirectory(title='添加资源文件夹')
        if p:
            resource_list.insert('end', p)

    def remove_resource():
        selection = list(resource_list.curselection())
        for idx in reversed(selection):
            resource_list.delete(idx)

    resource_buttons = tk.Frame(resource_frame)
    resource_buttons.pack(fill='x', padx=6, pady=4)
    tk.Button(resource_buttons, text='添加文件', command=add_resource_file).pack(side='left')
    tk.Button(resource_buttons, text='添加文件夹', command=add_resource_folder).pack(side='left', padx=6)
    tk.Button(resource_buttons, text='移除选中项', command=remove_resource).pack(side='left')

    log_text = scrolledtext.ScrolledText(root, height=12)
    log_text.pack(fill='both', expand=True, padx=10, pady=8)

    def append_log(msg):
        log_text.insert('end', msg + '\n')
        log_text.see('end')

    def start_pack():
        script = script_var.get().strip()
        if not script or not Path(script).exists():
            messagebox.showwarning('错误', '请选择有效的主脚本')
            return
        output_dir = output_var.get().strip() or str(Path.cwd() / 'dist')
        icon = icon_var.get().strip() or None
        requirements = req_var.get().strip() or None
        resources = []
        for i in range(resource_list.size()):
            src = resource_list.get(i)
            resources.append((src, Path(src).name))

        def worker():
            try:
                run_packaging(
                    script=script,
                    output_dir=output_dir,
                    onefile=onefile_var.get(),
                    windowed=windowed_var.get(),
                    icon=icon,
                    datas=resources,
                    use_venv=venv_var.get(),
                    requirements=requirements,
                    cb=append_log,
                )
                append_log('打包完成')
            except Exception as e:
                append_log('打包失败：' + str(e))

        threading.Thread(target=worker, daemon=True).start()

    start_button = tk.Button(root, text='开始打包', command=start_pack)
    start_button.pack(fill='x', padx=10, pady=8)
    root.mainloop()
