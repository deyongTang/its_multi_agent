import os
import hashlib
from typing import List, Dict, Any

class FileRepository:
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def remove_duplicate_files(file_paths: List[str]) -> List[str]:
        """
        去除重复文件
        """
        unique_files = {}  # 用于记录 {hash: file_path}
        unique_file_paths = []  # 最终要返回的列表

        for file_path in file_paths:
            try:
                # 尝试计算哈希
                file_hash = FileRepository.get_file_hash(file_path)

                # 只有计算成功了，才判断是否重复
                if file_hash not in unique_files:
                    unique_files[file_hash] = file_path
                    unique_file_paths.append(file_path)
                else:
                    # 这里打印一下，方便知道跳过了谁
                    print(f"发现重复文件，自动跳过: {os.path.basename(file_path)}")

            except Exception as e:
                # 坏文件就不混进去搞崩后面的流程
                print(f"文件读取异常，已跳过: {file_path} (错误: {str(e)})")
                continue

        return unique_file_paths

    @staticmethod
    def read_file_content(file_path: str) -> str:
        """
        读取文件内容
        :return: 成功返回文件内容，失败返回空字符串 ""
        """
        if not file_path or not os.path.exists(file_path):
            print(f"文件不存在或路径为空: {file_path}")
            return ""

        try:
            # 尝试以 UTF-8 读取
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        except UnicodeDecodeError:
            # 常见错误：文件不是 UTF-8 格式（例如是 GBK）
            print(f"文件编码错误(非UTF-8): {file_path}")
            # 可选：这里可以尝试用 'gbk' 重试读取，或者直接返回空
            return ""

        except OSError as e:
            # 捕获权限不足、文件被占用等系统IO错误
            print(f"读取文件IO错误: {file_path}, 原因: {e}")
            return ""

        except Exception as e:
            # 捕获其他未知错误
            print(f"读取未知错误: {file_path}, 原因: {e}")
            return ""

    @staticmethod
    def save_file(content: str, file_path: str):
        """保存内容到文件"""
        try:
            if not content:
                print(f"内容为空，跳过保存: {file_path}")
                return

            directory = os.path.dirname(file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except OSError as e:
            # 专门捕获文件系统错误 (如权限问题)
            print(f"保存文件失败: {file_path},原因：{e}")
        except Exception as e:
            print(f"发生未知错误: {e}")

    @staticmethod
    def list_files(directory: str, extension: str = None) -> List[str]:
        """
        列出目录下的文件
        :param extension: 过滤后缀，例如 '.md' (不区分大小写会更好)
        """
        files = []

        # 1. 基础校验
        if not directory:
            print("目录路径为空")
            return files

        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            return files

        # 2. 确保它真的是个目录，而不是文件
        if not os.path.isdir(directory):
            print(f"路径不是一个有效的目录: {directory}")
            return files

        try:
            # os.listdir 可能会因为权限问题报错
            file_names = os.listdir(directory)

            for filename in file_names:
                # 过滤后缀 (建议转小写比较，更加健壮)
                if extension:
                    if not filename.lower().endswith(extension.lower()):
                        continue

                # 拼接完整路径
                full_path = os.path.join(directory, filename)
                files.append(full_path)

            return files

        except PermissionError:
            print(f"权限不足，无法访问目录: {directory}")
            return files
        except OSError as e:
            print(f"遍历目录出错: {directory}, 原因: {e}")
            return files
        except Exception as e:
            print(f"未知错误: {directory}, 原因: {e}")
            return files
