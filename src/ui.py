"""Helpers for drawing a colorful text UI inside the Windows CMD window.

Only the Python standard library is used. Colors use ANSI escape codes,
which work in cmd.exe, PowerShell and Windows Terminal on Windows 10+.
"""

import os
import re
import shutil
import sys
import textwrap
import threading
import time

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------

if os.name == "nt":
    # An empty system() call switches cmd.exe into "ANSI colors" mode.
    os.system("")

# Make sure box-drawing characters never crash the program.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ

ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


class Color:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    RED = "\x1b[91m"
    GREEN = "\x1b[92m"
    YELLOW = "\x1b[93m"
    BLUE = "\x1b[94m"
    MAGENTA = "\x1b[95m"
    CYAN = "\x1b[96m"
    WHITE = "\x1b[97m"
    GRAY = "\x1b[90m"


def paint(text, *styles):
    """Wrap text in color codes (does nothing when colors are off)."""
    if not USE_COLOR or not styles:
        return str(text)
    return "".join(styles) + str(text) + Color.RESET


def visible_len(text):
    """Length of text as it appears on screen (color codes removed)."""
    return len(ANSI_PATTERN.sub("", text))


def terminal_columns():
    return max(1, shutil.get_terminal_size((80, 25)).columns)


def screen_width():
    """Width used for boxes: the window width, but never more than 78."""
    return max(40, min(terminal_columns() - 2, 78))


def clear():
    # Fixed command with no user input, so using the shell here is safe.
    os.system("cls" if os.name == "nt" else "clear")


def set_title(title):
    """Change the CMD window title using an escape code (no shell needed)."""
    if sys.stdout.isatty():
        sys.stdout.write(f"\x1b]0;{title}\x07")
        sys.stdout.flush()


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------

BANNER = r"""
 _   _  ___   ____  _   _   ____  _   _ __   __      _     ___
| | | ||_ _| / ___|| | | | / ___|| | | |\ \ / /     / \   |_ _|
| |_| | | | | |  _ | |_| || |  _ | | | | \ V /     / _ \   | |
|  _  | | | | |_| ||  _  || |_| || |_| |  | |     / ___ \  | |
|_| |_||___| \____||_| |_| \____| \___/   |_|    /_/   \_\|___|
"""


def banner(subtitle=""):
    width = screen_width()
    lines = BANNER.strip("\n").splitlines()
    art_width = max(len(line) for line in lines)
    if width >= art_width:
        left = " " * ((width - art_width) // 2)
        for line in lines:
            print(paint(left + line, Color.CYAN, Color.BOLD))
    else:
        print(paint("HIGHGUY AI".center(width), Color.CYAN, Color.BOLD))
    if subtitle:
        print(paint(subtitle.center(width), Color.GRAY))


def wrap(text, width):
    """Wrap text to a width, keeping the line breaks that are already there."""
    result = []
    for paragraph in str(text).splitlines() or [""]:
        if visible_len(paragraph) <= width:
            result.append(paragraph)
        else:
            indent = " " * (len(paragraph) - len(paragraph.lstrip()))
            result.extend(
                textwrap.wrap(paragraph, width, subsequent_indent=indent + "  ")
                or [""]
            )
    return result


def box(lines, title="", color=Color.CYAN):
    """Draw text inside a rounded box."""
    width = screen_width()
    inner = width - 4

    if isinstance(lines, str):
        lines = [lines]
    content = []
    for line in lines:
        content.extend(wrap(line, inner))

    if title:
        label = f" {title} "
        top = "╭─" + label + "─" * (width - 3 - len(label)) + "╮"
    else:
        top = "╭" + "─" * (width - 2) + "╮"

    print(paint(top, color))
    for line in content:
        padding = " " * (inner - visible_len(line))
        print(paint("│ ", color) + line + padding + paint(" │", color))
    print(paint("╰" + "─" * (width - 2) + "╯", color))


def rule(label=""):
    width = screen_width()
    if label:
        side = (width - len(label) - 2) // 2
        line = "─" * side + f" {label} " + "─" * (width - side - len(label) - 2)
    else:
        line = "─" * width
    print(paint(line, Color.GRAY))


def status_bar(items):
    """One line of 'key: value' pairs, e.g. language and voice status."""
    parts = [(paint(key + ": ", Color.GRAY) if key else "")
             + paint(value, Color.WHITE, Color.BOLD)
             for key, value in items]
    print("  " + paint("  │  ", Color.GRAY).join(parts))


def menu(options, title="MAIN MENU"):
    """Show numbered options. `options` is a list of (key, label) pairs."""
    lines = []
    for key, label in options:
        if key is None:
            lines.append("")
            continue
        lines.append(f"  {paint('[' + key + ']', Color.YELLOW, Color.BOLD)}  {label}")
    box(lines, title)


def table(headers, rows):
    """Print a simple table that fits the screen."""
    width = screen_width()
    columns = len(headers)
    sizes = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            sizes[i] = max(sizes[i], len(str(cell)))

    # Shrink the widest column until the table fits.
    while sum(sizes) + 3 * columns + 1 > width and max(sizes) > 6:
        widest = sizes.index(max(sizes))
        sizes[widest] -= 1

    def fit(text, size):
        text = str(text).replace("\n", " ")
        return text if len(text) <= size else text[: size - 1] + "…"

    def line(left, middle, right):
        return paint(left + middle.join("─" * (s + 2) for s in sizes) + right, Color.GRAY)

    bar = paint("│", Color.GRAY)
    print(line("┌", "┬", "┐"))
    print(bar + bar.join(" " + paint(fit(h, s).ljust(s), Color.CYAN, Color.BOLD) + " "
                         for h, s in zip(headers, sizes)) + bar)
    print(line("├", "┼", "┤"))
    for row in rows:
        print(bar + bar.join(" " + fit(c, s).ljust(s) + " " for c, s in zip(row, sizes)) + bar)
    print(line("└", "┴", "┘"))


# --------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------

def success(text):
    print(paint("  ✔ ", Color.GREEN, Color.BOLD) + paint(text, Color.GREEN))


def error(text):
    print(paint("  ✘ ", Color.RED, Color.BOLD) + paint(text, Color.RED))


def warning(text):
    print(paint("  ! ", Color.YELLOW, Color.BOLD) + paint(text, Color.YELLOW))


def info(text):
    print(paint("  • ", Color.CYAN) + text)


def hint(text):
    print(paint("  " + text, Color.GRAY))


# --------------------------------------------------------------------------
# Chat bubbles: your words on the right, Highguy on the left
# --------------------------------------------------------------------------

def bubble_width():
    return max(30, screen_width() * 2 // 3)


def erase_lines(count):
    """Remove the last `count` lines from the screen (real console only)."""
    if USE_COLOR and count > 0:
        sys.stdout.write(f"\x1b[{count}F\x1b[J")
        sys.stdout.flush()


def status_line(text):
    """Draw a one-line status that the next call overwrites (console only)."""
    if USE_COLOR:
        sys.stdout.write("\r\x1b[2K" + text)
        sys.stdout.flush()


def clear_status_line():
    status_line("")


def sound_meter(level, size=10):
    """A bar like ██████░░░░ for how loud the microphone is (0.0 - 1.0)."""
    filled = max(0, min(size, round(level * size)))
    return "█" * filled + "░" * (size - filled)


def user_bubble(text, name="You"):
    """Your message, in a box on the right side of the window."""
    lines = wrap(text, bubble_width() - 4)
    label = f" {name} "
    inner = max([visible_len(line) for line in lines] + [len(label)])
    left = " " * max(0, screen_width() - inner - 4)

    print(left + paint("╭" + "─" * (inner + 1 - len(label)) + label + "─╮", Color.CYAN))
    for line in lines:
        padding = " " * (inner - visible_len(line))
        print(left + paint("│ ", Color.CYAN) + paint(line, Color.WHITE, Color.BOLD)
              + padding + paint(" │", Color.CYAN))
    print(left + paint("╰" + "─" * (inner + 2) + "╯", Color.CYAN))


class AssistantBubble:
    """Highguy's reply on the left side.

    Text may arrive in small pieces (streaming); it is wrapped word by word.
    While Highguy waits for the AI brain, an animated "thinking" line shows,
    and each tool the brain uses appears as a step.
    """

    FRAMES = ("●∙∙", "∙●∙", "∙∙●", "∙●∙")

    def __init__(self, name="Highguy"):
        self.width = bubble_width() - 4
        self.prefix = paint("  │ ", Color.MAGENTA)
        self.column = 0
        self.line_open = False
        self.word = ""
        self.space = False
        self.breaks = 0
        self.has_text = False
        self.started = time.monotonic()
        self._spinner = None
        self._stop = threading.Event()
        print(paint(f"  ╭─ {name}", Color.MAGENTA, Color.BOLD))

    # -- thinking animation --------------------------------------------

    def thinking(self, label="thinking"):
        """Show an animated line until the next text or step arrives."""
        if not USE_COLOR or self._spinner:
            return
        self._flush_word()
        self._end_line()
        self._stop.clear()
        self._spinner = threading.Thread(target=self._spin, args=(label,), daemon=True)
        self._spinner.start()

    def _spin(self, label):
        frame = 0
        while True:
            seconds = time.monotonic() - self.started
            status_line(self.prefix + paint(self.FRAMES[frame % len(self.FRAMES)], Color.MAGENTA, Color.BOLD)
                        + paint(f" {label}  {seconds:.1f}s", Color.GRAY))
            frame += 1
            if self._stop.wait(0.15):
                return

    def _stop_thinking(self):
        if self._spinner:
            self._stop.set()
            self._spinner.join()
            self._spinner = None
            clear_status_line()

    # -- content -------------------------------------------------------

    def step(self, text):
        """One thing the brain did, e.g. '⚙ get weather: Dar es Salaam'."""
        self._stop_thinking()
        self._flush_word()
        self._end_line()
        print(self.prefix + paint(f"⚙ {text}", Color.GRAY))
        self.breaks = 0

    def problem(self, text):
        """A warning inside the bubble, e.g. when the AI brain is unreachable."""
        self._stop_thinking()
        self._flush_word()
        self._end_line()
        print(self.prefix + paint(f"! {text}", Color.YELLOW))

    def write(self, chunk):
        self._stop_thinking()
        for char in str(chunk):
            if char == "\n":
                self._flush_word()
                self.breaks += 1
            elif char in (" ", "\t"):
                self._flush_word()
                self.space = True
            else:
                self.word += char
        sys.stdout.flush()

    def close(self, footer=""):
        """Finish the bubble, with an optional note such as the time taken."""
        self._stop_thinking()
        self._flush_word()
        self._end_line()
        print(paint("  ╰─", Color.MAGENTA) + (" " + paint(footer, Color.GRAY) if footer else ""))
        print()

    # -- word wrapping -------------------------------------------------

    def _flush_word(self):
        if not self.word:
            return
        if self.breaks and self.has_text:
            self._end_line()
            if self.breaks > 1:
                print(self.prefix)  # keep one empty line between paragraphs
        elif self.column and self.column + 1 + len(self.word) > self.width:
            self._end_line()
        elif self.column and self.space:
            sys.stdout.write(" ")
            self.column += 1
        self.breaks = 0
        self.space = False
        if not self.line_open:
            sys.stdout.write(self.prefix)
            self.line_open = True
        sys.stdout.write(self.word)
        self.column += len(self.word)
        self.word = ""
        self.has_text = True

    def _end_line(self):
        if self.line_open:
            sys.stdout.write("\n")
            self.line_open = False
            self.column = 0


def assistant_says(text, name="Highguy", footer=""):
    """Print a complete reply from Highguy on the left."""
    bubble = AssistantBubble(name)
    bubble.write(text)
    bubble.close(footer)


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------

def ask(label, default=None):
    """Ask for text. Returns the default (or "") when nothing is typed.

    Raises KeyboardInterrupt when the input stream is closed (Ctrl+Z / Ctrl+C),
    so callers can go back to the menu.
    """
    suffix = paint(f" [{default}]", Color.GRAY) if default else ""
    try:
        answer = input(paint(f"  {label}", Color.CYAN, Color.BOLD) + suffix
                       + paint(" › ", Color.CYAN)).strip()
    except EOFError:
        raise KeyboardInterrupt from None
    if not answer and default is not None:
        return default
    return answer


def confirm(question):
    """Ask a yes/no question. Accepts English and Swahili answers."""
    answer = ask(f"{question} (y/n)").lower()
    return answer in {"y", "yes", "ndio", "ndiyo", "n'dio", "sawa"}


def pause(text="Press Enter to continue..."):
    try:
        input(paint(f"\n  {text}", Color.GRAY))
    except EOFError:
        pass
