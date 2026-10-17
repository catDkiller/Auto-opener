# ⚡ TaskBar Launcher (Windows)

Open all your favorite apps with **ONE click** from the taskbar.

Pick the apps you want → press one button → pin it to your taskbar.
From then on, a single click launches everything at once.
Changing your app list takes seconds — no technical knowledge needed.

---

## 🚀 Quick start (3 steps)

1. **Double-click `Edit My Apps.bat`** (or `launcher.pyw --edit`).
   A friendly window opens.

2. **Add your apps.**
   - Pick a popular app from the dropdown (Chrome, Discord, Spotify…), or
   - Click **Browse file…** and choose any program / folder / website.
   - Press **＋ Add to my list**. Repeat as much as you like.
   - Use **▲ Move up / ▼ Move down / ✕ Remove** to organize, and
     **New Group** to make sections like *Work* or *Gaming*.
   - Double-click an item in the list to test that it opens.

3. **Press “📌 Create My Taskbar Button”.**
   A shortcut named **TaskBar Launcher** appears on your Desktop
   (and in the Start Menu). Then:
   - Right-click it → **Show more options** → **Pin to taskbar**. ✅ Done!

Now one click on that taskbar icon opens **all** your chosen apps.

> 💡 Want your own picture as the button? Press **Change Icon** before
> creating the button (needs `pip install pillow` for .png/.jpg files;
> .ico files always work).

---

## ✏️ Changing your apps later

Three easy ways — pick whichever you like:

| Way | How |
|-----|-----|
| **Editor window** (easiest) | Double-click `Edit My Apps.bat` |
| **Plain text file** | Open `apps.txt` in Notepad and edit the lines |
| **Big button** | The “Create My Taskbar Button” step also saves automatically |

`apps.txt` format (one thing per line):

```text
# Lines starting with # are comments
[My Work Setup]                          <- optional group header
C:\Program Files\Google\Chrome\Application\chrome.exe
https://mail.google.com                  <- websites open in your browser
%SystemRoot%\system32\calc.exe           <- %variables% work too
"C:\Program Files\App\app.exe" --flag    <- arguments allowed
```

The taskbar button **always reads the newest apps.txt** — you never have
to re-pin it after changing the list.

---

## 📁 What's in this folder?

| File | Purpose |
|------|---------|
| `launcher.pyw` | The whole app (editor + one-click launcher) |
| `apps.txt` | Your app list – this is what you change |
| `Edit My Apps.bat` | Opens the editor window |
| `My Launcher.bat` | Opens all apps instantly (no Python-GUI needed) |
| `Create Taskbar Shortcut.bat` | Makes the pinnable shortcut for you |
| `Create Shortcut.ps1` | The script behind the shortcut maker |
| `launcher.ico` / `editor.ico` | Icons (also embedded inside `launcher.pyw`) |
| `Build EXE (optional).bat` | Optional: makes a standalone `TaskBarLauncher.exe` |

---

## ❓ Troubleshooting

**“Python was not found”**
Install Python from <https://www.python.org/downloads/> and tick
**“Add Python to PATH”** during setup. (Or run
`Build EXE (optional).bat` once to get a standalone `.exe` that needs
nothing.)

**An app didn't open when I clicked the taskbar button**
A message tells you which entry failed. Usually the path moved or the
app was uninstalled — reopen the editor and fix that one line.

**I changed apps.txt but the button still opens old stuff**
It shouldn’t! The button reads `apps.txt` fresh every click. If you
pinned `TaskBarLauncher.exe` instead, make sure `apps.txt` sits next to
the exe.

**Can I launch apps with arguments?**
Yes — put them on the same line, e.g.
`chrome.exe --new-window https://youtube.com`
(use the “Extra startup options” box in the editor).

**Does it work on Windows 11?**
Yes. On Win11 right-click the shortcut → **Show more options** →
**Pin to taskbar**, or just drag the shortcut onto the taskbar.

---

Made with plain Python + Tkinter — no installs required beyond Python
itself. Enjoy one-click everything! ⚡
