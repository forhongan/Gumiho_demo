import os
import subprocess
import sys
import zipfile
import hashlib
import urllib.request
import shutil
import time
import logging
import socket
from pathlib import Path

# 配置日志 - 修复编码问题
def setup_logging(log_path="launcher.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 控制台处理器 (使用UTF-8编码)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 文件处理器 (使用UTF-8编码)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

# 配置信息
EMBEDDED_PYTHON_VERSION = "3.10.11"
EMBEDDED_PYTHON_URL = f"https://www.python.org/ftp/python/{EMBEDDED_PYTHON_VERSION}/python-{EMBEDDED_PYTHON_VERSION}-embed-amd64.zip"
EMBEDDED_DIR = Path("backend") / "python_embed"
REQUIREMENTS = Path("backend") / "requirements.txt"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

def download_file_with_retry(url, target_path, max_retries=3, retry_delay=5):
    """下载文件到指定路径，支持重试机制"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"下载尝试 #{attempt}: {url}")
            with urllib.request.urlopen(url) as response, open(target_path, 'wb') as out_file:
                # 获取文件大小用于进度显示
                file_size = int(response.getheader('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    
                    # 显示下载进度
                    if file_size > 0:
                        percent = min(100, int(downloaded * 100 / file_size))
                        logger.debug(f"下载进度: {percent}% ({downloaded}/{file_size} bytes)")
                
                logger.info(f"下载成功: {target_path}")
                return True
                
        except Exception as e:
            logger.error(f"下载失败: {str(e)}")
            if attempt < max_retries:
                logger.info(f"{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                logger.error(f"下载失败，已达最大重试次数 ({max_retries})")
                return False

def extract_zip(zip_path, target_dir):
    """解压ZIP文件到目标目录"""
    logger.info(f"解压: {zip_path} -> {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 记录解压过程
            file_count = len(zip_ref.infolist())
            logger.debug(f"发现 {file_count} 个文件待解压")
            
            for i, file_info in enumerate(zip_ref.infolist(), 1):
                zip_ref.extract(file_info, target_dir)
                if i % 50 == 0 or i == file_count:  # 每50个文件或最后文件记录一次
                    logger.debug(f"解压进度: {i}/{file_count} 文件")
        
        logger.info("解压成功")
        return True
    except Exception as e:
        logger.error(f"解压失败: {str(e)}")
        # 清理可能部分解压的文件
        if target_dir.exists():
            logger.warning("清理部分解压的文件...")
            shutil.rmtree(target_dir)
        return False

def find_pth_file(embed_dir):
    """查找pth文件 - 支持多种命名格式"""
    logger.debug(f"在目录中查找pth文件: {embed_dir}")
    
    # 尝试常见命名格式
    patterns = [
        "python*._pth",     # Python 3.10+ 标准格式
        "python*.pth",      # 某些版本格式
        "*.pth",            # 通用格式
        "python*._pth.txt"  # 备用格式
    ]
    
    for pattern in patterns:
        files = list(embed_dir.glob(pattern))
        if files:
            logger.info(f"找到pth文件: {files[0]}")
            return files[0]
    
    # 列出目录内容帮助调试
    logger.error(f"在 {embed_dir} 中找不到pth文件")
    logger.debug(f"目录内容: {[f.name for f in embed_dir.iterdir()]}")
    raise FileNotFoundError(f"在 {embed_dir} 中找不到pth文件")

def reinstall_pip(python_exe):
    """重新安装pip以解决模块缺失问题"""
    logger.warning("检测到pip模块缺失，尝试重新安装pip...")
    get_pip = EMBEDDED_DIR / "get-pip.py"
    
    # 确保pth文件正确配置
    pth_file = find_pth_file(EMBEDDED_DIR)
    with open(pth_file, "r+") as f:
        content = f.read()
        # 确保包含import site
        if "import site" not in content:
            logger.info(f"修复pth文件: {pth_file}")
            f.write("\nimport site\n")
        # 确保取消注释import site行
        if "#import site" in content:
            logger.info(f"取消注释import site: {pth_file}")
            content = content.replace("#import site", "import site")
            f.seek(0)
            f.write(content)
            f.truncate()
    
    # 下载并运行get-pip
    if not download_file_with_retry(GET_PIP_URL, get_pip):
        raise RuntimeError("下载get-pip失败")
    
    # 使用python直接运行get-pip.py
    logger.info("重新安装pip...")
    try:
        result = subprocess.run(
            [str(python_exe), str(get_pip)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info("pip重新安装成功")
            logger.debug(f"pip安装输出:\n{result.stdout}")
        else:
            logger.error(f"pip安装失败:\n{result.stderr or result.stdout}")
            raise RuntimeError("pip安装失败")
    finally:
        get_pip.unlink(missing_ok=True)

def install_embedded_python():
    """安装内嵌式Python环境"""
    # 1. 下载嵌入式Python
    temp_zip = Path("python_embed_temp.zip")
    
    if not EMBEDDED_DIR.exists():
        logger.info("开始安装嵌入式Python环境")
        
        # 下载并重试
        if not download_file_with_retry(EMBEDDED_PYTHON_URL, temp_zip):
            raise RuntimeError("下载嵌入式Python失败")
        
        # 解压并重试
        if not extract_zip(temp_zip, EMBEDDED_DIR):
            raise RuntimeError("解压嵌入式Python失败")
        
        temp_zip.unlink(missing_ok=True)
        logger.info("内嵌式Python安装完成")
    else:
        logger.info("嵌入式Python已存在，跳过安装")

    # 检查是否安装成功
    python_exe = EMBEDDED_DIR / "python.exe"
    if not python_exe.exists():
        logger.error(f"未找到Python解释器: {python_exe}")
        logger.debug(f"Python目录内容: {[f.name for f in EMBEDDED_DIR.iterdir()]}")
        raise FileNotFoundError(f"未找到Python解释器: {python_exe}")

    # 2. 安装pip
    pip_exe = EMBEDDED_DIR / "Scripts" / "pip.exe"
    if not pip_exe.exists():
        logger.info("开始安装pip")
        reinstall_pip(python_exe)
    else:
        # 验证pip是否可用
        logger.info("验证pip可用性...")
        try:
            result = subprocess.run(
                [str(pip_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("pip存在但无法运行，尝试重新安装")
                reinstall_pip(python_exe)
            else:
                logger.info(f"pip验证成功: {result.stdout.strip()}")
        except Exception as e:
            logger.warning(f"pip验证失败: {str(e)}，尝试重新安装")
            reinstall_pip(python_exe)

    return python_exe

def install_dependencies(python_exe):
    """安装Python依赖"""
    logger.info("检查依赖安装状态...")
    pip_exe = EMBEDDED_DIR / "Scripts" / "pip.exe"
    if not pip_exe.exists():
        logger.warning("pip.exe不存在，使用python -m pip方式")
        pip_cmd = [str(python_exe), "-m", "pip"]
    else:
        pip_cmd = [str(pip_exe)]

    # 检查依赖是否需要更新
    hash_file = EMBEDDED_DIR / "requirements.md5"
    current_hash = hashlib.md5(REQUIREMENTS.read_bytes()).hexdigest()
    
    if hash_file.exists() and hash_file.read_text() == current_hash:
        logger.info("依赖已是最新，跳过安装")
        return
    
    logger.info("开始安装依赖包...")
    try:
        install_cmd = pip_cmd + ["install", "-r", str(REQUIREMENTS)]
        logger.debug(f"执行命令: {' '.join(install_cmd)}")
        
        result = subprocess.run(
            install_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 延长超时时间
        )
        
        if result.returncode == 0:
            logger.info("依赖安装成功")
            logger.debug(f"安装输出:\n{result.stdout}")
            # 保存新的hash
            hash_file.write_text(current_hash)
        else:
            # 详细错误诊断
            logger.error(f"依赖安装失败 (返回码: {result.returncode})")
            logger.error(f"错误输出:\n{result.stderr or result.stdout}")
            
            # 检查常见问题
            if "No module named" in result.stderr:
                logger.error("检测到模块缺失问题，尝试修复pip安装")
                reinstall_pip(python_exe)
                logger.info("重新尝试安装依赖...")
                result_retry = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                if result_retry.returncode == 0:
                    logger.info("依赖安装成功 (修复后)")
                    hash_file.write_text(current_hash)
                    return
            
            raise RuntimeError("依赖安装失败")
            
    except Exception as e:
        logger.error(f"依赖安装过程中出错: {str(e)}")
        raise

def wait_for_backend(port=5000, timeout=60):  # 延长超时时间
    """等待后端服务启动"""
    logger.info(f"等待后端服务启动(端口: {port})...")
    start_time = time.time()
    attempts = 0
    
    while time.time() - start_time < timeout:
        attempts += 1
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                logger.info(f"后端服务已启动 (尝试次数: {attempts})")
                return True
        except ConnectionRefusedError:
            if attempts % 10 == 0:  # 每10次尝试记录一次
                logger.debug(f"等待后端启动... (已尝试 {attempts} 次)")
            time.sleep(0.5)
        except Exception as e:
            logger.debug(f"连接测试失败: {str(e)}")
            time.sleep(1)
    
    logger.warning(f"⚠️ 后端服务启动超时 ({timeout}秒)，前端可能无法正常工作")
    return False

def main():
    # 修复基础路径检测
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent.resolve()
    else:
        base_dir = Path(__file__).parent.resolve()
    os.chdir(base_dir)
    
    # 动态路径函数
    def get_path(rel_path: str) -> Path:
        return base_dir / rel_path
        
    # 重设全局路径
    global EMBEDDED_DIR, REQUIREMENTS
    EMBEDDED_DIR = get_path("backend/python_embed")
    REQUIREMENTS = get_path("backend/requirements.txt")
    
    # 初始化日志（需放在路径修复后）
    global logger
    logger = setup_logging(get_path("launcher.log"))
    
    logger.info("启动器初始化...")
    logger.info(f"正确的工作目录: {base_dir}")
    logger.info(f"Python版本: {sys.version}")
    
    backend_process = None
    
    try:
        # 安装内嵌Python环境
        python_exe = install_embedded_python()
        logger.info(f"使用的Python解释器: {python_exe}")
        
        # 安装依赖
        install_dependencies(python_exe)
        
        # 启动后端 - 设置工作目录和编码环境变量
        backend_dir = base_dir / "backend"
        logger.info(f"启动后端服务，工作目录: {backend_dir}")
        
        backend_script = backend_dir / "api.py"
        if not backend_script.exists():
            raise FileNotFoundError(f"未找到后端入口文件: {backend_script}")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = str(backend_dir)
        # 添加编码设置
        env["PYTHONIOENCODING"] = "utf-8"  # 确保Python IO使用UTF-8
        
        backend_process = subprocess.Popen(
            [str(python_exe), "-u", str(backend_script)],  # 添加-u参数以确保不缓冲输出
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=str(backend_dir),  # 设置工作目录为backend文件夹
            env=env
        )
        
        # 记录后端输出
        def log_backend_output():
            logger.debug("开始监控后端输出...")
            while True:
                if backend_process.poll() is not None:
                    break
                output = backend_process.stdout.readline()
                if output:
                    logger.info(f"[后端] {output.strip()}")
                else:
                    time.sleep(0.1)
        
        import threading
        output_thread = threading.Thread(target=log_backend_output, daemon=True)
        output_thread.start()
        
        # 等待后端启动
        if not wait_for_backend():
            logger.error("后端服务启动失败，检查日志以获取详细信息")
            return
        
        # 启动前端
        logger.info("启动前端应用...")
        frontend_exe = base_dir / "frontend_flutter" / "build" / "windows" / "x64" / "runner" / "Release" / "frontend_flutter.exe"
        
        if frontend_exe.exists():
            logger.info(f"找到前端可执行文件: {frontend_exe}")
            frontend_process = subprocess.Popen([str(frontend_exe)])
            frontend_process.wait()
            logger.info("前端应用已关闭")
        else:
            logger.error(f"未找到前端可执行文件: {frontend_exe}")
            logger.info("请先构建Flutter前端应用: flutter build windows")
    
    except Exception as e:
        logger.critical(f"启动失败: {str(e)}", exc_info=True)
    
    finally:
        # 确保后端进程被终止
        if backend_process and backend_process.poll() is None:
            logger.info("终止后端进程...")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("后端进程未正常退出，强制终止")
                backend_process.kill()
        
        logger.info("启动器退出")

if __name__ == "__main__":
    main()

