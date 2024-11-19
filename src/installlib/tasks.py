import os
import sys
import subprocess
import venv
import winreg
import shutil

from .utils import start_command
from .flow import Resource


class PipInstallPackage:
    """Use pip install a package from PyPI.

    Parameters
    ----------
    package_name : str
        The name of the package to install.
    version : str, optional
        The version of the package to install.
    python : str, optional
        The path to the python interpreter to use. Default is sys.executable.
    args : tuple
        Additional arguments to pass to pip install.

    """

    def __init__(self, package_name, *args, version=None, python=sys.executable, name=None) -> None:
        self.name = name or PipInstallPackage.__name__
        self.package_name = package_name
        self.version = version
        self.python = python
        self.args = args

    def __repr__(self) -> str:
        return f"PipInstallPackage(`{self.package_name}`, `{self.version}`, `{self.python}`, {self.args})"

    def execute(self):
        package_id = self.package_name + (f"=={self.version}" if self.version else "")
        try:
            cmd = [self.python, "-m", "pip", "install", package_id]
            if self.args:
                cmd.extend(self.args)
            start_command(cmd)
        except subprocess.CalledProcessError as ex:
            return False, f"pip install failed for package: {self.package_name} with error: {ex}"
        return True, None


class PythonEnvironment:
    def __init__(self, path) -> None:
        self.path = path

    @property
    def python(self):
        return os.path.join(self.path, "Scripts", "python.exe")

    @property
    def activate(self):
        return os.path.join(self.path, "Scripts", "activate.bat")

    def __repr__(self) -> str:
        return f"PythonEnvironment(`{self.path}`)"


class CreatePythonEnvironment:
    def __init__(self, path, env_resource, interpreter=None, name=None) -> None:
        self.name = name or CreatePythonEnvironment.__name__
        self.path = path
        self.env_resource = env_resource
        self.interpreter = interpreter or "python"

    def execute(self):
        try:
            path = self.path() if callable(self.path) else self.path
            env = PythonEnvironment(path)
            venv.create(env.path, with_pip=True)
            Resource(self.env_resource).set(env)
        except Exception as ex:
            return False, f"Failed to create python environment: {ex}"
        return True, None


class InstallToVirtualEnvironment:
    def __init__(self, package_names, virtual_env, name=None) -> None:
        self.name = name or InstallToVirtualEnvironment.__name__
        self.package_names = package_names
        self.virtual_env = virtual_env

    def execute(self):
        try:
            env = self.virtual_env() if callable(self.virtual_env) else self.virtual_env
            activate_cmd = env.activate
            # --quiet is important: if PIPE gets full the process will hang
            install_cmd = ["python", "-m", "pip", "install", "--quiet", "--force-reinstall", *self.package_names]
            start_command([activate_cmd, "&&", *install_cmd])
        except Exception as ex:
            return False, f"Failed to install package: {self.package_names} to virtual environment: {ex}"
        return True, None


class InstallOfflineWheel:
    def __init__(self, path, virtual_env, name=None) -> None:
        self.name = name or InstallOfflineWheel.__name__
        self.path = path
        self.virtual_env = virtual_env

    def execute(self):
        try:
            env = self.virtual_env() if callable(self.virtual_env) else self.virtual_env
            activate_cmd = env.activate
            # --quiet is important: if PIPE gets full the process will hang
            install_cmd = ["python", "-m", "pip", "install", "--quiet", self.path]
            start_command([activate_cmd, "&&", *install_cmd])
        except Exception as ex:
            return False, f"Failed to install wheel: {self.path} to virtual environment: {ex}"
        return True, None


class ReadValueFromRegistry:
    HIVES = {
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_USERS": winreg.HKEY_USERS,
        "HKEY_PERFORMANCE_DATA": winreg.HKEY_PERFORMANCE_DATA,
        "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        "HKEY_DYN_DATA": winreg.HKEY_DYN_DATA,
    }

    def __init__(self, path, store_in, name=None) -> None:
        self.name = name or ReadValueFromRegistry.__name__
        split_path = path.split("\\")
        self.path = "\\".join(split_path[1:-1])
        self.hive = self.HIVES[split_path[0]]
        self.value_name = split_path[-1]
        self.store_in = store_in

    def execute(self):
        try:
            with winreg.ConnectRegistry(None, self.hive) as hive:
                with winreg.OpenKey(hive, self.path, 0, winreg.KEY_READ) as key:
                    value, _ = winreg.QueryValueEx(key, self.value_name)
                    Resource(self.store_in).set(value)
        except Exception as ex:
            return False, f"Failed to read value from registry: {ex}"
        return True, None


class ModifyResource:
    def __init__(self, resouce, resource_name, modifier: callable, in_place=False, name=None) -> None:
        self.name = name or ModifyResource.__name__
        self.resource = resouce
        self.resource_name = resource_name
        self.modifier = modifier
        self.in_place = in_place

    def execute(self):
        try:
            resource = self.resource()
            if self.in_place:
                self.modifier(resource)
            else:
                new_value = self.modifier(resource)
                Resource(self.resource_name).set(new_value)
        except Exception as ex:
            return False, f"Failed to modify resource: {ex}"
        return True, None


class CopyFiles:
    def __init__(self, sources, target_dir, name=None) -> None:
        self.name = name or CopyFiles.__name__
        self.sources = sources
        self.target_dir = target_dir

    def execute(self):
        try:
            source_files = self.sources() if callable(self.sources) else self.sources
            target_dir = self.target_dir() if callable(self.target_dir) else self.target_dir
            for source_file in source_files:
                shutil.copy2(source_file, target_dir)
        except Exception as ex:
            return False, f"Failed to copy files: {ex}"
        return True, None


class DeleteFiles:
    def __init__(self, filepaths, fail_on_doesnt_exist=True, name=None) -> None:
        self.name = name or DeleteFiles.__name__
        self.filepaths = filepaths
        self._fail_on_doesnt_exist = fail_on_doesnt_exist

    def execute(self):
        try:
            files = self.filepaths() if callable(self.filepaths) else self.filepaths

            if not isinstance(files, list):
                files = [files]

            for file in files:
                try:
                    os.remove(file)
                except FileNotFoundError:
                    if self._fail_on_doesnt_exist:
                        return False, f"File not found: {file}"
        except Exception as ex:
            return False, f"Failed to delete files: {ex}"
        return True, None
