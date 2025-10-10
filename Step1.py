import shlex
import tkinter as tk
from tkinter import scrolledtext, END

PROMPT = "vfs> "

class VFSReplGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VFS")
        self.geometry("760x420")

        self.output = scrolledtext.ScrolledText(self, wrap=tk.WORD, state="disabled", font=("Consolas", 11))
        self.output.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6,0))

        frame = tk.Frame(self)
        frame.pack(fill=tk.X, padx=6, pady=6)
        self.entry = tk.Entry(frame, font=("Consolas", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.on_enter)
        tk.Button(frame, text="Enter", command=self.on_enter).pack(side=tk.LEFT, padx=(6,0))

        self.write_output("VFS REPL\n")
        self.write_prompt()

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
        try:
            tokens = shlex.split(raw, posix=True)
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
            # заглушка: выводит своё имя и аргументы
            self.write_output(f"ls: args={args}\n")
        elif cmd == "cd":
            self.write_output(f"cd: args={args}\n")
        else:
            self.write_output(f"Ошибка: неизвестная команда '{cmd}'\n")

        self.write_prompt()

if __name__ == "__main__":
    app = VFSReplGUI()
    app.mainloop()