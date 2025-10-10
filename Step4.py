import shlex
import argparse
import tkinter as tk
from tkinter import scrolledtext, END
import os

PROMPT = "vfs> "

class VirtualFileSystem:
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.tree = self._build_tree(self.root_path)
        self.cwd = []

    def _build_tree(self, path):
        tree = {}
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                tree[entry] = self._build_tree(full)
            else:
                try:
                    with open(full, "r", encoding="utf-8") as f:
                        lines = f.read().splitlines()
                except Exception:
                    lines = ["[Ошибка чтения файла]"]
                tree[entry] = lines
        return tree

    def _get_dir_ref(self):
        ref = self.tree
        for part in self.cwd:
            ref = ref.get(part)
            if ref is None:
                raise FileNotFoundError("Путь не найден в VFS")
        return ref

    def ls(self):
        ref = self._get_dir_ref()
        if not isinstance(ref, dict):
            raise NotADirectoryError("Текущий путь не директория")
        return sorted(ref.keys())

    def cd(self, path):
        if not path or path == ".":
            return
        if path == "..":
            if self.cwd:
                self.cwd.pop()
            return
        ref = self._get_dir_ref()
        if path not in ref:
            raise FileNotFoundError(f"Папка '{path}' не найдена")
        if not isinstance(ref[path], dict):
            raise NotADirectoryError(f"'{path}' — не директория")
        self.cwd.append(path)

    def pwd(self):
        return "/" + "/".join(self.cwd)

    def read_file(self, name):
        ref = self._get_dir_ref()
        if name not in ref:
            raise FileNotFoundError(f"Файл '{name}' не найден")
        if isinstance(ref[name], dict):
            raise IsADirectoryError(f"'{name}' — это директория")
        return ref[name]


class VFSReplGUI(tk.Tk):
    def __init__(self, vfs_path=None, startup_script=None):
        super().__init__()
        self.title("VFS Emulator (Stage 4)")
        self.geometry("820x480")

        self.vfs_path = vfs_path
        self.startup_script = startup_script
        self.vfs = None

        self.output = scrolledtext.ScrolledText(self, wrap=tk.WORD, state="disabled", font=("Consolas", 11))
        self.output.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6,0))

        frame = tk.Frame(self)
        frame.pack(fill=tk.X, padx=6, pady=6)
        self.entry = tk.Entry(frame, font=("Consolas", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.on_enter)
        tk.Button(frame, text="Enter", command=self.on_enter).pack(side=tk.LEFT, padx=(6,0))

        self.write_output("VFS\n")
        self.write_output(f"vfs_path = {self.vfs_path}\nstartup_script = {self.startup_script}\n")
        if self.vfs_path and os.path.isdir(self.vfs_path):
            self.vfs = VirtualFileSystem(self.vfs_path)
            self.write_output(f"VFS загружена из {self.vfs_path}\n")
        else:
            self.write_output("Ошибка: некорректный путь VFS\n")

        self.write_prompt()
        if self.startup_script:
            self.after(300, self.run_startup_script)

    def write_output(self, text):
        self.output.configure(state="normal")
        self.output.insert(END, text)
        self.output.see(END)
        self.output.configure(state="disabled")

    def write_prompt(self):
        self.write_output(PROMPT)
        self.entry.focus_set()

    def on_enter(self, event=None):
        raw = self.entry.get().rstrip("\n")
        self.write_output(raw + "\n")
        self.entry.delete(0, END)
        self.execute_command_line(raw)

    def execute_command_line(self, raw_line):
        try:
            tokens = shlex.split(raw_line, posix=True)
        except ValueError as e:
            self.write_output(f"Ошибка парсера: {e}\n")
            self.write_prompt()
            return
        if not tokens:
            self.write_prompt()
            return

        cmd = tokens[0]
        args = tokens[1:]

        try:
            if cmd == "exit":
                self.quit(); return
            elif cmd == "ls": self.cmd_ls()
            elif cmd == "cd": self.cmd_cd(args)
            elif cmd == "pwd": self.cmd_pwd()
            elif cmd == "cat": self.cmd_cat(args)
            elif cmd == "head": self.cmd_head(args)
            elif cmd == "uniq": self.cmd_uniq(args)
            else:
                self.write_output(f"Ошибка: неизвестная команда '{cmd}'\n")
        except Exception as e:
            self.write_output(f"[Ошибка] {e}\n")

        self.write_prompt()

    def cmd_ls(self):
        for name in self.vfs.ls():
            self.write_output(name + "\n")

    def cmd_cd(self, args):
        if not args:
            self.write_output("cd: нужен аргумент\n"); return
        self.vfs.cd(args[0])

    def cmd_pwd(self):
        self.write_output(self.vfs.pwd() + "\n")

    def cmd_cat(self, args):
        if not args:
            self.write_output("cat: нужен файл\n"); return
        lines = self.vfs.read_file(args[0])
        for line in lines:
            self.write_output(line + "\n")

    def cmd_head(self, args):
        if not args:
            self.write_output("head: нужен файл\n"); return
        name = args[0]
        n = int(args[1]) if len(args) > 1 else 10
        lines = self.vfs.read_file(name)
        for line in lines[:n]:
            self.write_output(line + "\n")

    def cmd_uniq(self, args):
        if not args:
            self.write_output("uniq: нужен файл\n"); return
        lines = self.vfs.read_file(args[0])
        seen = set()
        for line in lines:
            if line not in seen:
                seen.add(line)
                self.write_output(line + "\n")

    def run_startup_script(self):
        path = self.startup_script
        if not os.path.isfile(path):
            self.write_output(f"Ошибка: скрипт не найден ({path})\n"); return
        self.write_output(f"# Выполнение: {path}\n")
        with open(path, "r", encoding="utf-8") as f:
            for i, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                self.write_output(line + "\n")
                try:
                    self.execute_command_line(line)
                except Exception as e:
                    self.write_output(f"Ошибка в строке {i}: {e}\n")
        self.write_output(f"# Конец скрипта {path}\n")
        self.write_prompt()


def parse_args():
    parser = argparse.ArgumentParser(description="VFS")
    parser.add_argument("--vfs-path", help="путь к виртуальной файловой системе")
    parser.add_argument("--startup-script", help="путь к стартовому скрипту")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    app = VFSReplGUI(vfs_path=args.vfs_path, startup_script=args.startup_script)
    app.mainloop()