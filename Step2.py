import argparse
import shlex
import tkinter as tk
from tkinter import scrolledtext, END
import os

PROMPT = "vfs> "

class VFSReplGUI(tk.Tk):
    def __init__(self, vfs_path=None, startup_script=None):
        super().__init__()
        self.title("VFS")
        self.geometry("820x480")
        self.vfs_path = vfs_path
        self.startup_script = startup_script

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
        self.write_prompt()

        if self.startup_script:
            self.after(100, self.run_startup_script)

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

        cmd, *args = tokens

        if cmd == "exit":
            self.write_output("exit\n")
            self.quit()
            return
        elif cmd == "ls":
            self.write_output(f"ls: args={args}\n")
        elif cmd == "cd":
            if len(args) > 1:
                self.write_output("cd: неверные аргументы: ожидается не более одного пути\n")
            else:
                self.write_output(f"cd: args={args}\n")
        else:
            self.write_output(f"Ошибка: неизвестная команда '{cmd}'\n")

        self.write_prompt()

    def run_startup_script(self):
        path = self.startup_script
        if not os.path.isfile(path):
            self.write_output(f"Ошибка стартового скрипта: файл не найден: {path}\n")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            self.write_output(f"Ошибка при чтении стартового скрипта: {e}\n")
            return

        self.write_output(f"# Выполнение стартового скрипта: {path}\n")
        for idx, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")
            self.write_output(line + "\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            try:
                self.execute_command_line(line)
            except Exception as e:
                self.write_output(f"Ошибка при выполнении строки {idx}: {e}\n")
                continue
        self.write_output(f"# Конец выполнения скрипта: {path}\n")
        self.write_prompt()

def parse_args():
    p = argparse.ArgumentParser(description="VFS REPL")
    p.add_argument("--vfs-path", dest="vfs_path", help="Path to physical VFS location", default=None)
    p.add_argument("--startup-script", dest="startup_script", help="Path to startup script", default=None)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    app = VFSReplGUI(vfs_path=args.vfs_path, startup_script=args.startup_script)
    app.mainloop()
