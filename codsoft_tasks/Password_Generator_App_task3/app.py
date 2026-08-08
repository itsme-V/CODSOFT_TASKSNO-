

import argparse
import math
import os
import secrets
import string
import sys

try:  # Optional: only needed for copy-to-clipboard
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    pyperclip = None
    HAS_CLIPBOARD = False

# --------------------------------------------------------------------------
# Character sets and constants
# --------------------------------------------------------------------------

CHAR_SETS = {
    "upper": ("Uppercase letters (A-Z)", string.ascii_uppercase),
    "lower": ("Lowercase letters (a-z)", string.ascii_lowercase),
    "digits": ("Digits (0-9)", string.digits),
    "symbols": ("Symbols (!@#$%^&*)", string.punctuation),
}

# Easily confused when reading/typing: 0/O, 1/l/I, |, !, i, L
AMBIGUOUS_CHARS = set("0O1lI|!iL")

MIN_LENGTH, MAX_LENGTH = 1, 128
MIN_COUNT, MAX_COUNT = 1, 10
DEFAULT_LENGTH = 16

# --------------------------------------------------------------------------
# Terminal colours (auto-disabled for non-TTY or NO_COLOR)
# --------------------------------------------------------------------------

_STYLES = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "cyan": "\033[36m", "magenta": "\033[35m",
}


def _colour_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty() and sys.stderr.isatty()


_COLOUR = _colour_enabled()


def paint(text, *styles):
    """Wrap text in ANSI colour codes (no-op when colours are disabled)."""
    if not _COLOUR or not styles:
        return text
    codes = "".join(_STYLES[s] for s in styles if s in _STYLES)
    return f"{codes}{text}{_STYLES['reset']}"


# --------------------------------------------------------------------------
# Core password logic (reusable outside the app)
# --------------------------------------------------------------------------

def build_pools(use_upper=True, use_lower=True, use_digits=True,
                use_symbols=True, exclude_ambiguous=False):
    """
    Return the list of character pools selected, honouring the
    exclude-ambiguous option. Raises ValueError if nothing is selected.
    """
    pools = []
    for key, (_, chars) in CHAR_SETS.items():
        if not {"upper": use_upper, "lower": use_lower,
                "digits": use_digits, "symbols": use_symbols}[key]:
            continue
        if exclude_ambiguous:
            chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
        if chars:
            pools.append(chars)

    if not pools:
        raise ValueError("At least one character set must be enabled.")
    return pools


def generate_password(length=DEFAULT_LENGTH, use_upper=True, use_lower=True,
                      use_digits=True, use_symbols=True,
                      exclude_ambiguous=False):
    """
    Generate a random password of the given length using secrets.

    Guarantees at least one character from every enabled set (as long as
    the length allows), fills the remainder from the combined pool, then
    shuffles so the guaranteed characters aren't at predictable positions.
    """
    pools = build_pools(use_upper, use_lower, use_digits, use_symbols,
                        exclude_ambiguous)

    # One guaranteed character per pool, capped at the requested length
    characters = [secrets.choice(pools[i]) for i in range(min(length, len(pools)))]

    # Fill the rest from everything combined
    if length > len(pools):
        combined = "".join(pools)
        characters += [secrets.choice(combined) for _ in range(length - len(pools))]

    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)


def estimate_entropy(length, pools):
    """Entropy estimate in bits: length * log2(combined pool size)."""
    pool_size = sum(len(p) for p in pools)
    if pool_size <= 0:
        return 0.0
    return round(length * math.log2(pool_size), 1)


def strength_info(bits):
    """Return (label, colour, description) for an entropy value in bits."""
    if bits < 40:
        return "WEAK", "red", "Very weak — fine for nothing sensitive"
    if bits < 60:
        return "FAIR", "yellow", "Fair — OK for low-risk accounts"
    if bits < 80:
        return "STRONG", "green", "Strong — good for most accounts"
    if bits < 110:
        return "VERY STRONG", "cyan", "Very strong — suitable for sensitive accounts"
    return "EXCELLENT", "magenta", "Excellent — overkill for almost everything"


def copy_to_clipboard(text):
    """Copy text to the clipboard. Returns True on success."""
    if not HAS_CLIPBOARD:
        return False
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
# Interactive app
# --------------------------------------------------------------------------

class PasswordGeneratorApp:
    """Menu-driven interactive password generator."""

    def __init__(self):
        self.length = DEFAULT_LENGTH
        self.enabled = {"upper": True, "lower": True,
                        "digits": True, "symbols": True}
        self.exclude_ambiguous = False

    # ----- helpers --------------------------------------------------------

    @staticmethod
    def _ask(prompt, default=None):
        suffix = f" [{default}]" if default is not None else ""
        try:
            raw = input(f"{prompt}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not raw and default is not None:
            return default
        return raw

    @staticmethod
    def _ask_int(prompt, low, high, default=None):
        while True:
            raw = PasswordGeneratorApp._ask(prompt, default)
            try:
                value = int(raw)
            except ValueError:
                print(paint("  ✗ Please enter a number.", "red"))
                continue
            if low <= value <= high:
                return value
            print(paint(f"  ✗ Please enter a number between {low} and {high}.", "red"))

    def _current_pools(self):
        return build_pools(
            use_upper=self.enabled["upper"],
            use_lower=self.enabled["lower"],
            use_digits=self.enabled["digits"],
            use_symbols=self.enabled["symbols"],
            exclude_ambiguous=self.exclude_ambiguous,
        )

    # ----- screens ---------------------------------------------------------

    def show_banner(self):
        line = paint("═" * 54, "cyan")
        print("\n" + line)
        print(paint("   🔐  PASSWORD GENERATOR  —  pure Python, no dependencies", "bold", "cyan"))
        print(line)

    def run(self):
        """Main menu loop."""
        self.show_banner()
        while True:
            print(paint("\n  [1] Generate passwords", "bold"))
            print("  [2] Settings (length & complexity)")
            print("  [3] About")
            print("  [4] Quit")
            choice = self._ask("\n  Your choice", "1")

            if choice == "1":
                self.generate_screen()
            elif choice == "2":
                self.settings_screen()
            elif choice == "3":
                self.about_screen()
            elif choice == "4" or choice.lower() in ("q", "quit", "exit"):
                print(paint("\n  Goodbye! 👋\n", "green"))
                return
            else:
                print(paint("  ✗ Invalid choice. Pick 1-4.", "red"))

    def generate_screen(self):
        """Generate and display passwords."""
        print(paint("\n" + "─" * 54, "cyan"))
        print(paint("  GENERATE PASSWORDS", "bold", "cyan"))
        print(paint("─" * 54, "cyan"))

        count = self._ask_int("  How many passwords", MIN_COUNT, MAX_COUNT, 1)

        try:
            pools = self._current_pools()
        except ValueError as error:
            print(paint(f"  ✗ {error}", "red"))
            print(paint("    Enable at least one character set in Settings first.", "yellow"))
            return

        passwords = [generate_password(
            self.length,
            use_upper=self.enabled["upper"],
            use_lower=self.enabled["lower"],
            use_digits=self.enabled["digits"],
            use_symbols=self.enabled["symbols"],
            exclude_ambiguous=self.exclude_ambiguous,
        ) for _ in range(count)]

        print()
        for i, password in enumerate(passwords, 1):
            print(paint(f"  {i}) ", "bold", "cyan") + paint(password, "bold"))

        # Strength summary
        bits = estimate_entropy(self.length, pools)
        label, colour, desc = strength_info(bits)
        pool_size = sum(len(p) for p in pools)

        bar_filled = int(24 * min(bits, 128) / 128)
        bar = ("█" * bar_filled) + ("░" * (24 - bar_filled))
        print(paint(f"\n  {bar}  {paint(label, colour)}", "bold"))
        print(paint(f"  {desc}", "dim"))
        print(f"  {self.length} chars × pool of {pool_size} = "
              f"{paint(str(bits) + ' bits of entropy', colour)}")

        # Optional copy
        if HAS_CLIPBOARD:
            choice = self._ask("\n  Copy one to clipboard? Enter its number "
                               "(or press Enter to continue)", "")
            if choice.strip():
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(passwords):
                        ok = copy_to_clipboard(passwords[idx])
                        if ok:
                            print(paint(f"  ✓ Password {idx + 1} copied to clipboard.", "green"))
                        else:
                            print(paint("  ✗ Clipboard unavailable on this system.", "red"))
                    else:
                        print(paint("  ✗ No such password number.", "red"))
                except ValueError:
                    print(paint("  ✗ Not a number; nothing copied.", "red"))
        else:
            print(paint("\n  Tip: install pyperclip (pip install pyperclip) to get "
                        "copy-to-clipboard.", "dim"))

    def settings_screen(self):
        """View and edit length / complexity settings."""
        while True:
            print(paint("\n" + "─" * 54, "cyan"))
            print(paint("  SETTINGS", "bold", "cyan"))
            print(paint("─" * 54, "cyan"))

            print(paint(f"  [1] Length                : {self.length}", "bold"))
            for i, key in enumerate(("upper", "lower", "digits", "symbols"), start=2):
                state = paint("ON", "green", "bold") if self.enabled[key] \
                    else paint("OFF", "red", "bold")
                label = CHAR_SETS[key][0]
                print(f"  [{i}] {label:<26}: {state}")
            ambi = paint("ON", "green", "bold") if self.exclude_ambiguous \
                else paint("OFF", "red", "bold")
            print(f"  [6] Exclude ambiguous chars  : {ambi}")
            print("  [0] Back to main menu")

            choice = self._ask("\n  Your choice", "0")

            if choice == "1":
                new_len = self._ask_int("    New length", MIN_LENGTH, MAX_LENGTH,
                                        self.length)
                if new_len < 8:
                    print(paint("    ⚠  Below 8 characters is easy to crack. "
                                "Recommended: 12–16.", "yellow"))
                self.length = new_len
                print(paint(f"    ✓ Length set to {self.length}.", "green"))
            elif choice in ("2", "3", "4", "5"):
                key = ("upper", "lower", "digits", "symbols")[int(choice) - 2]
                self.enabled[key] = not self.enabled[key]
                if not any(self.enabled.values()):
                    print(paint("    ⚠  All sets are OFF — you must keep at least "
                                "one on to generate.", "yellow"))
            elif choice == "6":
                self.exclude_ambiguous = not self.exclude_ambiguous
                state = "ON" if self.exclude_ambiguous else "OFF"
                print(paint(f"    ✓ Exclude ambiguous characters: {state}", "green"))
            elif choice == "0":
                return
            else:
                print(paint("  ✗ Invalid choice.", "red"))

    @staticmethod
    def about_screen():
        print(paint("\n" + "─" * 54, "cyan"))
        print(paint("  ABOUT", "bold", "cyan"))
        print(paint("─" * 54, "cyan"))
        print("""
  • Generates strong, random passwords using Python's `secrets` module
    (cryptographically secure — NOT the `random` module).
  • Guarantees at least one character from every enabled set.
  • Entropy = length × log2(pool size) — higher is harder to crack.
  • No passwords are stored, logged, or sent anywhere.
  • Pure standard library; optional pyperclip adds clipboard support.
""")


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------

def run_quick(length, count, no_upper, no_lower, no_digits, no_symbols,
              no_ambiguous):
    """One-shot generation for the command line, then exit."""
    try:
        pools = build_pools(use_upper=not no_upper, use_lower=not no_lower,
                            use_digits=not no_digits, use_symbols=not no_symbols,
                            exclude_ambiguous=no_ambiguous)
    except ValueError as error:
        print(paint(f"✗ {error}", "red"))
        sys.exit(1)

    print(paint("PASSWORD GENERATOR", "bold", "cyan"))
    print(paint("-" * 40, "cyan"))
    for _ in range(count):
        print(paint(generate_password(
            length, use_upper=not no_upper, use_lower=not no_lower,
            use_digits=not no_digits, use_symbols=not no_symbols,
            exclude_ambiguous=no_ambiguous), "bold"))

    bits = estimate_entropy(length, pools)
    label, colour, desc = strength_info(bits)
    print(paint("-" * 40, "cyan"))
    print(paint(f"Strength: {label} ({bits} bits) — {desc}", colour))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="password_generator_app",
        description="Generate strong, random passwords with pure Python.",
    )
    parser.add_argument("length", nargs="?", type=int,
                        help="password length (default 16; interactive mode "
                             "if omitted)")
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="number of passwords (1–10)")
    parser.add_argument("--no-upper", action="store_true", help="no A–Z")
    parser.add_argument("--no-lower", action="store_true", help="no a–z")
    parser.add_argument("--no-digits", action="store_true", help="no 0–9")
    parser.add_argument("--no-symbols", action="store_true", help="no symbols")
    parser.add_argument("--no-ambiguous", action="store_true",
                        help="exclude 0/O, 1/l/I, |, !, ...")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="force the interactive menu")
    args = parser.parse_args(argv)

    quick_mode = (args.interactive is False and
                  (args.length is not None or args.count != 1 or
                   args.no_upper or args.no_lower or args.no_digits or
                   args.no_symbols or args.no_ambiguous))

    if quick_mode:
        length = min(max(args.length if args.length else DEFAULT_LENGTH,
                         MIN_LENGTH), MAX_LENGTH)
        count = min(max(args.count, MIN_COUNT), MAX_COUNT)
        run_quick(length, count, args.no_upper, args.no_lower, args.no_digits,
                  args.no_symbols, args.no_ambiguous)
        return

    PasswordGeneratorApp().run()


if __name__ == "__main__":
    main()
