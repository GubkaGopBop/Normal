import shlex
import argparse
import tkinter as tk
from tkinter import scrolledtext, END
import os

PROMPT = "vfs> "

class VirtualFileSystem:
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.root = self._build_tree(self.root_path)
        self.cwd = []

    def _build_tree(self, path):
        node = {}
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.isdir(full):
                node[name] = self._build_tree(full)
            else:
                node[name] = None
        return node

    def _split_components(self, path):
        if path.startswith("/"):
            comps = [c for c in path.strip("/").split("/") if c]
            return True, comps
        comps = [c for c in path.split("/") if c and c != "."]
        return False, comps

    def _resolve(self, path):
        if path == "" or path == ".":
            return self.root, []
        abs_flag, comps = self._split_components(path)
        node = self.root
        cur = [] if abs_flag else list(self.cwd)
        for comp in comps:
            if comp == "..":
                if cur:
                    cur.pop()
                continue
            if not isinstance(node, dict):
                return None, comps
            node = node.get(comp)
            if node is None:
                return None, comps
            cur.append(comp)
        return node, []

    def ls(self, path=""):
        node, rem = self._resolve(path)
        if node is None:
            raise FileNotFoundError("путь не найден")
        if not isinstance(node, dict):
            return [None]
        return sorted(node.keys())

    def cd(self, path):
        if not path or path == ".":
            return
        node, rem = self._resolve(path)
        if node is None:
            raise FileNotFoundError("путь не найден")
        if not isinstance(node, dict):
            raise NotADirectoryError("не директория")
        abs_flag, comps = self._split_components(path)
        self.cwd = comps if abs_flag else self.cwd + comps

    def pwd(self):
        return "/" + "/".join(self.cwd)

class VFSReplGUI(tk.Tk):
    def __init__(self, vfs_path=None, startup_script=None):
        super().__init__()
        self.title("VFS")
        self.geometry("800x520")
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

        self.write_output("VFS REPL\n")
        self.write_output("Debug: startup parameters:\n")
        self.write_output(f"  vfs_path = {repr(self.vfs_path)}\n")
        self.write_output(f"  startup_script = {repr(self.startup_script)}\n")

        if self.vfs_path and os.path.isdir(self.vfs_path):
            self.vfs = VirtualFileSystem(self.vfs_path)
            self.write_output(f"VFS загружена из: {self.vfs_path}\n")
        else:
            self.write_output("Ошибка: VFS не найдена или путь некорректен\n")

        self.write_prompt()
        if self.startup_script:
            self.after(200, self.run_startup_script)

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

        if cmd == "exit":
            self.write_output("exit\n")
            self.quit()
            return
        elif cmd == "ls":
            try:
                items = self.vfs.ls(args[0] if args else "")
                if items == [None]:
                    self.write_output("(файл)\n")
                else:
                    for n in items:
                        self.write_output(n + "\n")
            except Exception as e:
                self.write_output(f"ls: {e}\n")
        elif cmd == "cd":
            try:
                self.vfs.cd(args[0] if args else "")
                self.write_output(f"(cwd) {self.vfs.pwd()}\n")
            except Exception as e:
                self.write_output(f"cd: {e}\n")
        elif cmd == "pwd":
            self.write_output(self.vfs.pwd() + "\n")
        else:
            self.write_output(f"Ошибка: неизвестная команда '{cmd}'\n")

        self.write_prompt()

    def run_startup_script(self):
        path = self.startup_script
        if not os.path.isfile(path):
            self.write_output(f"Ошибка: файл не найден: {path}\n")
            return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("#"):
                    continue
                self.write_output(l + "\n")
                self.execute_command_line(l)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--vfs-path", dest="vfs_path", help="Path to VFS directory", default=None)
    p.add_argument("--startup-script", dest="startup_script", help="Path to startup script", default=None)
    return p.parse_args()

def main():
    args = parse_args()
    app = VFSReplGUI(vfs_path=args.vfs_path, startup_script=args.startup_script)
    app.mainloop()

if __name__ == "__main__":
    main()