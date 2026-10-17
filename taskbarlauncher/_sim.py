#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
TaskBar Launcher - One-click app launcher for Windows.

How it works:
  * This program reads a simple text file (apps.txt) that lists the apps you want to open.
  * When launched with no arguments, it opens every app in the list and exits immediately.
  * When launched with "--edit", it opens a friendly editor window where you can
    add / remove / reorder your apps and choose an icon.

Pinning to the taskbar:
  Run "Create Taskbar Shortcut.bat" (or use the button inside the editor).
  It creates a normal Windows shortcut (.lnk) which you can pin to the taskbar.
  Clicking that taskbar icon opens all your chosen apps in one click.

The apps.txt file is plain text, so it is also super easy to change by hand:
  [Section Name]      -> optional label, groups apps together
  Path\to\App.exe     -> a program to launch
  Any URL             -> a website to open (https://...)
  # comment           -> ignored line
"""

import os
import sys
import subprocess
import shlex

IS_WINDOWS = sys.platform.startswith("win")

# When run as a frozen (PyInstaller) build, files live next to the .exe.
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "apps.txt")
ICON_FILE = os.path.join(APP_DIR, "launcher.ico")
EDITOR_ICON_FILE = os.path.join(APP_DIR, "editor.ico")

# A few handy presets users can pick from in the editor.
COMMON_APPS = {
    "Chrome": r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    "Chrome (x86)": r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    "Edge": r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    "Firefox": r"%ProgramFiles%\Mozilla Firefox\firefox.exe",
    "Notepad": r"%SystemRoot%\system32\notepad.exe",
    "Calculator": r"%SystemRoot%\system32\calc.exe",
    "File Explorer": r"%SystemRoot%\explorer.exe",
    "Paint": r"%SystemRoot%\System32\mspaint.exe",
    "Snipping Tool": r"%LocalAppData%\Microsoft\WindowsApps\snippingtool.exe",
    "Command Prompt": r"%SystemRoot%\system32\cmd.exe",
    "PowerShell": r"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe",
    "VS Code": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "Spotify": r"%APPDATA%\Spotify\Spotify.exe",
    "Discord": r"%LOCALAPPDATA%\Discord\Discord.exe",
    "Word": r"%ProgramFiles%\Microsoft Office\root\Office16\WINWORD.EXE",
    "Excel": r"%ProgramFiles%\Microsoft Office\root\Office16\EXCEL.EXE",
    "Outlook": r"%ProgramFiles%\Microsoft Office\root\Office16\OUTLOOK.EXE",
}


# --------------------------------------------------------------------------- #
#  Config helpers
# --------------------------------------------------------------------------- #
def expand(path):
    """Expand environment variables like %ProgramFiles% and ~ ."""
    if not path:
        return path
    p = os.path.expandvars(path.strip())
    p = os.path.expanduser(p)
    return p


def read_entries():
    """Read apps.txt into a list of dicts: {'kind': 'app'|'section', ...}."""
    entries = []
    if not os.path.exists(CONFIG_FILE):
        return entries
    with open(CONFIG_FILE, "r", encoding="utf-8-sig") as fh:
        for raw in fh:
            line = raw.rstrip("\n").rstrip("\r")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                entries.append({"kind": "section", "name": stripped[1:-1].strip()})
            else:
                entries.append({"kind": "app", "path": stripped})
    return entries


def write_entries(entries):
    """Write the entry list back to apps.txt."""
    lines = ["# TaskBar Launcher - list of apps to open with ONE click.",
             "# Each line below is a program path, a folder, or a website URL.",
             "# Lines starting with # are comments and are ignored.",
             "# Edit this file by hand, or use:  launcher.pyw --edit",
             ""]
    for e in entries:
        if e["kind"] == "section":
            lines.append("[%s]" % e.get("name", ""))
        else:
            lines.append(e.get("path", ""))
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    os.replace(tmp, CONFIG_FILE)


def default_config():
    """Create a starter apps.txt if none exists yet."""
    write_entries([
        {"kind": "section", "name": "My Work Setup"},
        {"kind": "app", "path": "https://www.google.com"},
        {"kind": "app", "path": COMMON_APPS["File Explorer"]},
    ])


# --------------------------------------------------------------------------- #
#  Launching
#  Returns (ok: bool, message: str)
# --------------------------------------------------------------------------- #
def launch_target(target):
    target = expand(target)
    if not target:
        return False, "Empty entry"
    try:
        if IS_WINDOWS:
            return _launch_windows(target)
        # Fallbacks so the code can be tested on other OSes too.
        return _launch_posix(target)
    except Exception as exc:  # pragma: no cover
        return False, str(exc)


def _split_command(text):
    """Split 'C:\\path\\app.exe arg1 arg2' into (exe, args)."""
    text = text.strip()
    try:
        parts = shlex.split(text, posix=False)
    except ValueError:
        parts = text.split()
    if not parts:
        return "", []
    exe = parts[0].strip('"')
    args = [p.strip('"') for p in parts[1:]]
    return exe, args


def _launch_windows(target):
    DETACHED = 0x00000008 | 0x00000010 | 0x00000200  # DETACHED_PROCESS etc.
    raw_exe, args = _split_command(target)   # BEFORE expanding variables
    exe, args = raw_exe, args                # may be replaced below

    lower = target.lower()
    # Website URLs -> let the default browser handle them.
    if lower.startswith(("http://", "https://", "www.")):
        url = target if lower.startswith(("http://", "https://")) else "https://" + target
        os.startfile(url)
        return True, "Opened in browser"

    # ms-settings: / shell: / other URI schemes (no backslash early on)
    head = target[:24]
    if ":" in head and "\\" not in head and "/" not in head and             not target.strip('"').lower().endswith((".exe", ".bat", ".cmd", ".lnk")):
        subprocess.Popen(["cmd", "/c", "start", "", target],
                         creationflags=DETACHED, close_fds=True)
        return True, "Opened"

    full = expand(raw_exe)                   # expand vars only for existence checks
    # If expanding produced a real file, pass it as the executable.
    if full != raw_exe and os.path.isfile(full):
        exe = full
    if os.path.isdir(full):
        subprocess.Popen(["explorer", full], creationflags=DETACHED, close_fds=True)
        return True, "Opened folder"

    if os.path.isfile(exe):
        subprocess.Popen([exe] + args, cwd=os.path.dirname(exe),
                         creationflags=DETACHED, close_fds=True)
        return True, "Started"

    # Maybe it's on PATH (e.g. "notepad")
    found = _which(exe)
    if found:
        subprocess.Popen([found] + args, creationflags=DETACHED, close_fds=True)
        return True, "Started"

    # Last resort: ShellExecute via startfile (handles .lnk, documents, ...)
    if os.path.exists(full):
        os.startfile(full)
        return True, "Opened"

    return False, "Not found: %s" % target


def _which(name):
    import shutil
    return shutil.which(name)


def _launch_posix(target):  # pragma: no cover
    exe, args = _split_command(target)
    if target.lower().startswith(("http://", "https://", "www.")):
        url = target if "://" in target else "https://" + target
        subprocess.Popen(["xdg-open", url])
        return True, "Opened in browser"
    if os.path.isdir(expand(exe)):
        subprocess.Popen(["xdg-open", expand(exe)])
        return True, "Opened folder"
    cmd = [expand(exe)] + args
    if not os.path.isfile(cmd[0]):
        w = _which(cmd[0])
        if not w:
            return False, "Not found: %s" % target
        cmd[0] = w
    subprocess.Popen(cmd)
    return True, "Started"


def launch_all(show_errors=True):
    """Open everything in apps.txt. Returns list of (entry, ok, msg)."""
    entries = [e for e in read_entries() if e["kind"] == "app"]
    results = []
    for e in entries:
        ok, msg = launch_target(e["path"])
        results.append((e["path"], ok, msg))
    if show_errors and IS_WINDOWS:
        failed = [(p, m) for p, ok, m in results if not ok]
        if failed:
            try:
                import ctypes
                msg = "Could not open:\n\n" + "\n".join(
                    "%s\n   (%s)" % (p, m) for p, m in failed)
                ctypes.windll.user32.MessageBoxW(
                    0, msg, "TaskBar Launcher", 0x30)
            except Exception:
                pass
    return results


# --------------------------------------------------------------------------- #
#  Icon handling
# --------------------------------------------------------------------------- #
# A ready-made multi-size icon (bolt on a rounded square) is embedded below as
# base64, so the launcher always has a crisp taskbar icon even without Pillow.
LAUNCHER_ICON_B64 = (
    "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"
)

EDITOR_ICON_B64 = (
    "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"
    "Or4G46WdMusAAAAABJRU5ErkJggg=="
)


def ensure_default_icon():
    """Write the built-in icons next to the app if they are missing."""
    for path, b64 in ((ICON_FILE, LAUNCHER_ICON_B64),
                      (EDITOR_ICON_FILE, EDITOR_ICON_B64)):
        if not os.path.exists(path):
            try:
                import base64
                with open(path, "wb") as fh:
                    fh.write(base64.b64decode(b64))
            except Exception:
                pass


def make_icon(dest_path, source_image_path=None):
    """Create a proper multi-size .ico at dest_path (requires Pillow).

    If source_image_path is given, the picture is used as the icon.
    Otherwise the built-in bolt icon is written.
    """
    if not source_image_path:
        import base64
        with open(dest_path, "wb") as fh:
            fh.write(base64.b64decode(LAUNCHER_ICON_B64))
        return dest_path

    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("pillow-not-installed")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    base = Image.open(source_image_path).convert("RGBA")
    base.thumbnail((256, 256))
    for s in sizes:
        im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        ratio = min(s / base.width, s / base.height) * 0.92
        nw, nh = max(1, int(base.width * ratio)), max(1, int(base.height * ratio))
        resized = base.resize((nw, nh), Image.LANCZOS)
        im.paste(resized, ((s - nw) // 2, (s - nh) // 2), resized)
        images.append(im)

    images[0].save(dest_path, format="ICO",
                   sizes=[(i.width, i.height) for i in images],
                   append_images=images[1:])
    return dest_path


# --------------------------------------------------------------------------- #
#  Windows shortcut creation (for taskbar pinning)
# --------------------------------------------------------------------------- #
def create_shortcut(link_path, target, arguments="", icon_location=None,
                    description="", working_dir=None):
    """Create a .lnk using WScript.Shell COM object (no extra pip packages)."""
    ps = r'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('%s')
$sc.TargetPath = '%s'
$sc.Arguments = '%s'
$sc.IconLocation = '%s'
$sc.Description = '%s'
$sc.WorkingDirectory = '%s'
$sc.Save()
''' % (_psq(link_path), _psq(target), _psq(arguments),
       _psq(icon_location or target), _psq(description),
       _psq(working_dir or os.path.dirname(target)))
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   check=True, capture_output=True)


def _psq(s):
    return str(s).replace("'", "''")


def desktop_dir():
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    return d if os.path.isdir(d) else os.path.expanduser("~")


def create_pinnable_shortcuts():
    """Create launcher shortcuts on Desktop + Start Menu. Returns list of paths."""
    if getattr(sys, "frozen", False):
        # Built as a standalone .exe: the exe itself is the shortcut target.
        target = os.path.abspath(sys.executable)
        arguments = ""
    else:
        target = os.path.abspath(sys.executable)
        script = os.path.abspath(__file__)
        arguments = '"%s"' % script
    created = []
    targets = [
        ("TaskBar Launcher.lnk", desktop_dir()),
        ("TaskBar Launcher.lnk", _start_menu_dir()),
    ]
    for name, folder in targets:
        link = os.path.join(folder, name)
        try:
            create_shortcut(link,
                            target=target,
                            arguments=arguments,
                            icon_location=ICON_FILE if os.path.exists(ICON_FILE) else None,
                            description="Opens all my favorite apps in one click",
                            working_dir=APP_DIR)
            created.append(link)
        except Exception:
            pass
    return created


def _start_menu_dir():
    d = os.path.join(os.environ.get("APPDATA", ""),
                     "Microsoft", "Windows", "Start Menu", "Programs")
    return d if os.path.isdir(d) else desktop_dir()


# --------------------------------------------------------------------------- #
#  The editor GUI (Tkinter)
# --------------------------------------------------------------------------- #
def run_editor():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("TaskBar Launcher - Editor")
    root.geometry("880x600")
    root.minsize(720, 480)

    if os.path.exists(EDITOR_ICON_FILE):
        try:
            root.iconbitmap(EDITOR_ICON_FILE)
        except Exception:
            pass

    entries = read_entries()

    style = ttk.Style(root)
    for pref in ("vista", "clam", "default"):
        if pref in style.theme_names():
            style.theme_use(pref)
            break
    style.configure("Big.TButton", font=("Segoe UI", 10))
    style.configure("Title.TLabel", font=("Segoe UI", 15, "bold"))
    style.configure("Hint.TLabel", font=("Segoe UI", 9), foreground="#555")

    main = ttk.Frame(root, padding=10)
    main.pack(fill="both", expand=True)

    header = ttk.Label(main, text="Pick the apps you want to open with ONE click",
                       style="Title.TLabel")
    header.pack(anchor="w")
    hint = ttk.Label(main,
                     style="Hint.TLabel",
                     text="Add your apps below, then press ‘Create My Taskbar Button’. "
                          "Pin the shortcut it puts on your Desktop to the taskbar.")
    hint.pack(anchor="w", pady=(0, 8))

    body = ttk.Panedwindow(main, orient="horizontal")
    body.pack(fill="both", expand=True)

    left = ttk.Labelframe(body, text="  Your app list  ", padding=8)
    right = ttk.Labelframe(body, text="  Add an app  ", padding=8)
    body.add(left, weight=3)
    body.add(right, weight=2)

    # ---------------- listbox with scrollbar -------------------------------
    lb_frame = ttk.Frame(left)
    lb_frame.pack(fill="both", expand=True)
    lst = tk.Listbox(lb_frame, activestyle="dotbox", font=("Segoe UI", 11),
                     selectmode="extended", exportselection=False)
    sb = ttk.Scrollbar(lb_frame, orient="vertical", command=lst.yview)
    lst.configure(yscrollcommand=sb.set)
    lst.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def display_name(e):
        if e["kind"] == "section":
            return "── %s ──" % e["name"]
        p = e["path"]
        if p.lower().startswith(("http://", "https://", "www.")):
            return "🌐  " + p
        name = os.path.basename(expand(p.split()[0])) or p
        return "▸  " + name + ("   [" + " ".join(p.split()[1:]) + "]"
                               if len(p.split()) > 1 else "")

    def refresh_list(keep_selection=True):
        sel = set(lst.curselection()) if keep_selection else set()
        lst.delete(0, "end")
        for e in entries:
            lst.insert("end", display_name(e))
        for i in sorted(sel):
            if i < len(entries):
                lst.selection_set(i)

    refresh_list(False)

    btn_row = ttk.Frame(left)
    btn_row.pack(fill="x", pady=(8, 0))
    row2 = ttk.Frame(left)
    row2.pack(fill="x", pady=(6, 0))

    def idx():
        s = lst.curselection()
        return s[0] if s else None

    def need_select():
        i = idx()
        if i is None:
            messagebox.showinfo("TaskBar Launcher",
                                "Please click an item in the list first.",
                                parent=root)
        return i

    def move(delta):
        i = need_select()
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(entries):
            entries[i], entries[j] = entries[j], entries[i]
            refresh_list(False)
            lst.selection_set(j)

    def remove_selected():
        sel = lst.curselection()
        if not sel:
            messagebox.showinfo("TaskBar Launcher",
                                "Select what you want to remove.", parent=root)
            return
        for i in reversed(list(sel)):
            del entries[i]
        refresh_list(False)

    def rename_section():
        i = need_select()
        if i is None:
            return
        if entries[i]["kind"] != "section":
            messagebox.showinfo("TaskBar Launcher",
                                "Only group headers can be renamed.\n"
                                "Use ‘New Group’ to add one.", parent=root)
            return
        new = simple_prompt("Rename group", "Group name:", entries[i]["name"])
        if new:
            entries[i]["name"] = new
            refresh_list()

    def add_section():
        name = simple_prompt("New group", "Group name (e.g. Work, Gaming):",
                             "My Apps")
        if name:
            entries.append({"kind": "section", "name": name})
            refresh_list(False)
            lst.selection_set(len(entries) - 1)

    # small modal prompt because simpledialog can be flaky with themes
    def simple_prompt(title, label, initial=""):
        top = tk.Toplevel(root)
        top.title(title)
        top.resizable(False, False)
        top.transient(root)
        top.grab_set()
        ttk.Label(top, text=label, padding=(12, 12, 12, 4)).pack(anchor="w")
        var = tk.StringVar(value=initial)
        ent = ttk.Entry(top, textvariable=var, width=46, font=("Segoe UI", 11))
        ent.pack(fill="x", padx=12, pady=(0, 10))
        ent.select_range(0, "end")
        ent.focus_set()
        result = {}

        def ok(_=None):
            v = var.get().strip()
            if v:
                result["v"] = v
                top.destroy()

        def cancel(_=None):
            top.destroy()

        fr = ttk.Frame(top)
        fr.pack(pady=(0, 12), anchor="e")
        ttk.Button(fr, text="OK", command=ok, width=8).pack(side="right", padx=(6, 0))
        ttk.Button(fr, text="Cancel", command=cancel, width=8).pack(side="right")
        top.bind("<Return>", ok)
        top.bind("<Escape>", cancel)
        top.wait_window()
        return result.get("v")

    ttk.Button(btn_row, text="▲ Move up", command=lambda: move(-1),
               style="Big.TButton").pack(side="left")
    ttk.Button(btn_row, text="▼ Move down", command=lambda: move(1),
               style="Big.TButton").pack(side="left", padx=6)
    ttk.Button(btn_row, text="✕ Remove", command=remove_selected,
               style="Big.TButton").pack(side="left")
    ttk.Button(row2, text="New Group", command=add_section,
               style="Big.TButton").pack(side="left")
    ttk.Button(row2, text="Rename Group", command=rename_section,
               style="Big.TButton").pack(side="left", padx=6)
    ttk.Button(row2, text="Edit path…",
               command=lambda: edit_path_dialog(),
               style="Big.TButton").pack(side="left")

    # ---------------- right panel: add app ---------------------------------
    ttk.Label(right, text="Choose a popular app:", padding=(0, 2)).pack(anchor="w")
    names = sorted(COMMON_APPS.keys())
    combo_var = tk.StringVar()
    combo = ttk.Combobox(right, textvariable=combo_var, values=names,
                         state="readonly", font=("Segoe UI", 10))
    combo.pack(fill="x", pady=(2, 8))

    ttk.Label(right, text="…or browse for any program on your PC:",
              padding=(0, 6, 0, 2)).pack(anchor="w")

    path_var = tk.StringVar()
    path_entry = ttk.Entry(right, textvariable=path_var, font=("Segoe UI", 10))
    path_entry.pack(fill="x", pady=(0, 6))

    def browse():
        f = filedialog.askopenfilename(
            title="Choose a program",
            filetypes=[("Programs", "*.exe *.lnk *.bat *.cmd"),
                       ("All files", "*.*")])
        if f:
            path_var.set(os.path.abspath(f))

    def browse_folder():
        d = filedialog.askdirectory(title="Choose a folder to open")
        if d:
            path_var.set(os.path.abspath(d))

    def browse_url():
        v = simple_prompt("Open a website",
                          "Website address (e.g. https://youtube.com):",
                          "https://")
        if v:
            path_var.set(v)

    brow = ttk.Frame(right)
    brow.pack(fill="x", pady=(0, 8))
    ttk.Button(brow, text="Browse file…", command=browse).pack(side="left")
    ttk.Button(brow, text="Folder…", command=browse_folder).pack(side="left", padx=6)
    ttk.Button(brow, text="Website…", command=browse_url).pack(side="left")

    ttk.Label(right, text="Extra startup options (optional):",
              padding=(0, 6, 0, 2)).pack(anchor="w")
    args_var = tk.StringVar()
    ttk.Entry(right, textvariable=args_var, font=("Segoe UI", 10)).pack(fill="x")

    def add_from_combo(_evt=None):
        nm = combo_var.get()
        if nm in COMMON_APPS:
            path_var.set(COMMON_APPS[nm])
    combo.bind("<<ComboboxSelected>>", add_from_combo)

    def do_add():
        p = path_var.get().strip()
        if not p:
            messagebox.showinfo("TaskBar Launcher",
                                "First pick an app from the list above,\n"
                                "or browse for a program.", parent=root)
            return
        extra = args_var.get().strip()
        full = p + ((" " + extra) if extra else "")
        entries.append({"kind": "app", "path": full})
        refresh_list(False)
        lst.selection_set(len(entries) - 1)
        lst.see("end")
        path_var.set("")
        args_var.set("")
        combo_var.set("")

    ttk.Button(right, text="＋  Add to my list", command=do_add)\
        .pack(fill="x", pady=(10, 4))

    test_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(right, variable=test_var,
                    text="Test it right away (opens the app now)").pack(anchor="w")

    def edit_path_dialog():
        i = need_select()
        if i is None or entries[i]["kind"] != "app":
            return
        new = simple_prompt("Edit this entry",
                            "Program path, folder or website:",
                            entries[i]["path"])
        if new:
            entries[i]["path"] = new
            refresh_list()

    # ---------------- bottom action bar ------------------------------------
    bottom = ttk.Frame(main)
    bottom.pack(fill="x", pady=(12, 0))

    status_var = tk.StringVar(value="Ready.")
    ttk.Label(bottom, textvariable=status_var, style="Hint.TLabel")\
        .pack(side="bottom", anchor="w", pady=(4, 0))

    def save_only():
        write_entries(entries)
        status_var.set("Saved ✓  (%s)" % CONFIG_FILE)

    def open_folder():
        try:
            if IS_WINDOWS:
                subprocess.Popen(["explorer", "/select,", CONFIG_FILE])
            else:
                subprocess.Popen(["xdg-open", APP_DIR])
        except Exception:
            pass

    def pick_icon():
        f = filedialog.askopenfilename(
            title="Pick a picture for your taskbar button",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.ico"),
                       ("Icon files", "*.ico"), ("All files", "*.*")])
        if not f:
            return
        try:
            if f.lower().endswith(".ico"):
                import shutil
                shutil.copyfile(f, ICON_FILE)
            else:
                make_icon(ICON_FILE, f)
            status_var.set("Icon updated ✓")
        except Exception as exc:
            messagebox.showwarning(
                "TaskBar Launcher",
                "Could not use that picture:\n%s\n\n"
                "Tip: install the 'pillow' library (pip install pillow)\n"
                "or choose an existing .ico file instead." % exc, parent=root)

    def reset_icon():
        try:
            os.remove(ICON_FILE)
        except OSError:
            pass
        ensure_default_icon()
        status_var.set("Icon reset to default ✓")

    def create_button():
        write_entries(entries)
        if not [e for e in entries if e["kind"] == "app"]:
            messagebox.showinfo("TaskBar Launcher",
                                "Your list is empty — add at least one app first :)",
                                parent=root)
            return
        ensure_default_icon()
        try:
            links = create_pinnable_shortcuts()
        except Exception as exc:
            links = []
            detail = str(exc)
        else:
            detail = ""
        if links:
            status_var.set("Done! Now pin it:  " + " ·  ".join(links))
            top = tk.Toplevel(root)
            top.title("Almost there!")
            top.transient(root)
            msg = ("Your launcher shortcut is ready!\n\n"
                   "① Go to your Desktop (a folder will open).\n"
                   "② Right-click  ‘TaskBar Launcher’  →  Show more options  →  Pin to taskbar.\n"
                   "③ Done! From now on, one click on that taskbar button "
                   "opens all your apps.\n\n"
                   "You can change your apps any time by reopening this editor.")
            ttk.Label(top, text=msg, padding=16, justify="left",
                      wraplength=440).pack()
            fr = ttk.Frame(top, padding=(16, 0, 16, 16))
            fr.pack()

            def finish():
                top.destroy()

            def go_folder():
                try:
                    subprocess.Popen(["explorer", "/select,", links[0]])
                except Exception:
                    pass

            ttk.Button(fr, text="Open the folder", command=go_folder)\
                .pack(side="left")
            ttk.Button(fr, text="OK", command=finish, width=10).pack(side="right")
        else:
            messagebox.showerror(
                "TaskBar Launcher",
                "Could not create the shortcut.\n\n%s\n\n"
                "You can still run 'Create Taskbar Shortcut.bat' in the app folder."
                % detail, parent=root)

    big = ttk.Button(bottom, text="📌  Create My Taskbar Button",
                     command=create_button)
    big.pack(side="top", pady=(0, 8))

    row = ttk.Frame(bottom)
    row.pack(fill="x")
    ttk.Button(row, text="Save", command=save_only).pack(side="left")
    ttk.Button(row, text="Test ▶", command=lambda: test_launch()).pack(side="left", padx=6)
    ttk.Button(row, text="Change Icon", command=pick_icon).pack(side="left")
    ttk.Button(row, text="Reset Icon", command=reset_icon).pack(side="left", padx=6)
    ttk.Button(row, text="Open config folder", command=open_folder).pack(side="left")

    def test_launch():
        write_entries(entries)
        i = idx()
        subset = [entries[i]] if (i is not None and entries[i]["kind"] == "app") \
            else [e for e in entries if e["kind"] == "app"]
        for e in subset:
            ok, msg = launch_target(e["path"])
            if not ok:
                messagebox.showwarning("TaskBar Launcher",
                                       "Couldn't open:\n%s\n\nReason: %s"
                                       % (e["path"], msg), parent=root)

    # double-click a list item to test just that app
    def on_double(_evt):
        i = idx()
        if i is not None and entries[i]["kind"] == "app":
            ok, msg = launch_target(entries[i]["path"])
            if not ok:
                messagebox.showwarning("TaskBar Launcher", msg, parent=root)
    lst.bind("<Double-Button-1>", on_double)

    # keyboard shortcuts
    def on_key(evt):
        if evt.state & 0x4 and evt.char.lower() == "s":   # Ctrl+S
            save_only()
            return "break"
        if evt.keysym == "Delete":
            remove_selected()
    root.bind("<Key>", on_key)

    if not entries:
        entries.extend([{"kind": "section", "name": "My Apps"}])
        refresh_list(False)

    root.protocol("WM_DELETE_WINDOW", lambda: (write_entries(entries), root.destroy()))
    root.mainloop()


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #
def main():
    args = sys.argv[1:]
    if "--edit" in args or "-e" in args:
        run_editor()
        return
    if "--help" in args or "-h" in args:
        print(__doc__)
        return
    # Default behaviour: launch everything and exit quietly.
    if not os.path.exists(CONFIG_FILE):
        default_config()
    launch_all(show_errors=True)


if __name__ == "__main__":
    main()
