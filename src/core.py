import os
import sys
import tempfile
import shutil
import subprocess
import venv
from pathlib import Path

def _write_log(cb, msg):
    if cb:
        cb(msg)

def _run_streamed(cmd, cb, cwd=None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, text=True)
    for line in proc.stdout:
        _write_log(cb, line.rstrip())
    proc.wait()
    return proc.returncode

def create_build_venv(cb=None):
    tmp = Path(tempfile.mkdtemp(prefix='py_packager_'))
    venv_dir = tmp / 'venv'
    venv.create(venv_dir, with_pip=True)
    _write_log(cb, f'Created temporary venv: {venv_dir}')
    if os.name == 'nt':
        python_exe = venv_dir / 'Scripts' / 'python.exe'
    else:
        python_exe = venv_dir / 'bin' / 'python'
    return str(python_exe), tmp

def install_packages(python_exe, packages, cb=None):
    if not packages:
        return 0
    cmd = [python_exe, '-m', 'pip', 'install', '--upgrade'] + packages
    _write_log(cb, 'Installing packages: ' + ' '.join(packages))
    return _run_streamed(cmd, cb)

def run_pyinstaller(python_exe, script_path, output_dir, onefile=True, windowed=False, icon=None, datas=None, cb=None):
    cmd = [python_exe, '-m', 'PyInstaller', '--noconfirm', '--clean', '--distpath', str(output_dir)]
    if onefile:
        cmd.append('--onefile')
    if windowed:
        cmd.append('--windowed')
    if icon:
        cmd.append(f'--icon={icon}')
    if datas:
        for src, dest in datas:
            sep = ';' if os.name == 'nt' else ':'
            cmd += ['--add-data', f'{src}{sep}{dest}']
    cmd.append(str(script_path))
    _write_log(cb, 'Running PyInstaller...')
    return _run_streamed(cmd, cb)

def run_packaging(script, output_dir, onefile=True, windowed=False, icon=None, datas=None, use_venv=False, requirements=None, cb=None):
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if use_venv:
        python_exe, tmpdir = create_build_venv(cb)
        install_packages(python_exe, ['pyinstaller'], cb)
        if requirements:
            install_packages(python_exe, ['-r', str(requirements)], cb)
        try:
            rc = run_pyinstaller(python_exe, script, output_dir, onefile, windowed, icon, datas, cb)
        finally:
            _write_log(cb, f'Cleaning temporary build dir: {tmpdir}')
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        install_packages(sys.executable, ['pyinstaller'], cb)
        if requirements:
            install_packages(sys.executable, ['-r', str(requirements)], cb)
        rc = run_pyinstaller(sys.executable, script, output_dir, onefile, windowed, icon, datas, cb)
    _write_log(cb, f'Packaging finished with return code: {rc}')
    return rc
