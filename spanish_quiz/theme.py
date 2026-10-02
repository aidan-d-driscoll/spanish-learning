"""Visual language for the quiz app."""

from tkinter import ttk

FONT = "Segoe UI"

COLORS = {
    "bg": "#F3EEE6",
    "surface": "#FFFBF6",
    "surface_alt": "#EDE6DA",
    "ink": "#1B2430",
    "muted": "#6B645C",
    "line": "#E2D8CB",
    "sidebar": "#17202B",
    "sidebar_muted": "#9AA3B2",
    "sidebar_active": "#243244",
    "accent": "#C2410C",
    "accent_hover": "#9A3412",
    "accent_soft": "#FBE8DC",
    "good": "#166534",
    "good_bg": "#DCFCE7",
    "locked_bg": "#D9D1C4",
    "locked_row": "#E7DFD3",
    "bad": "#991B1B",
    "bad_bg": "#FEE2E2",
    "star": "#D97706",
}


def apply_theme(root) -> ttk.Style:
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".", font=(FONT, 11), background=COLORS["bg"], foreground=COLORS["ink"])
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
    style.configure("Alt.TFrame", background=COLORS["surface_alt"])

    style.configure(
        "Title.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["ink"],
        font=(FONT, 26, "bold"),
    )
    style.configure(
        "Heading.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["ink"],
        font=(FONT, 16, "bold"),
    )
    style.configure(
        "Body.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["ink"],
        font=(FONT, 11),
    )
    style.configure(
        "Muted.TLabel",
        background=COLORS["bg"],
        foreground=COLORS["muted"],
        font=(FONT, 10),
    )
    style.configure(
        "CardTitle.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["ink"],
        font=(FONT, 22, "bold"),
    )
    style.configure(
        "CardBody.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["ink"],
        font=(FONT, 14),
    )
    style.configure(
        "CardMuted.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted"],
        font=(FONT, 10),
    )
    style.configure(
        "SidebarTitle.TLabel",
        background=COLORS["sidebar"],
        foreground="#F5F0E8",
        font=(FONT, 14, "bold"),
    )
    style.configure(
        "Sidebar.TLabel",
        background=COLORS["sidebar"],
        foreground=COLORS["sidebar_muted"],
        font=(FONT, 10),
    )

    style.configure(
        "Chip.TCheckbutton",
        background=COLORS["surface"],
        foreground=COLORS["ink"],
        font=(FONT, 11),
        focuscolor=COLORS["surface"],
        padding=(10, 6),
    )
    style.map(
        "Chip.TCheckbutton",
        background=[("active", COLORS["accent_soft"])],
        foreground=[("active", COLORS["ink"])],
    )
    style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["ink"], font=(FONT, 11))
    style.configure("Surface.TCheckbutton", background=COLORS["surface"], foreground=COLORS["ink"])
    style.configure(
        "Accent.TButton",
        font=(FONT, 11, "bold"),
        background=COLORS["accent"],
        foreground="#FFFFFF",
        padding=(16, 10),
        borderwidth=0,
        focusthickness=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", COLORS["accent_hover"]), ("disabled", "#D6CCC2")],
        foreground=[("disabled", "#8A8178")],
    )
    style.configure(
        "Ghost.TButton",
        font=(FONT, 11),
        background=COLORS["surface_alt"],
        foreground=COLORS["ink"],
        padding=(14, 9),
        borderwidth=0,
    )
    style.map("Ghost.TButton", background=[("active", COLORS["line"])])
    style.configure(
        "Nav.TButton",
        font=(FONT, 11),
        background=COLORS["sidebar"],
        foreground="#E8E4DC",
        padding=(12, 10),
        anchor="w",
        borderwidth=0,
    )
    style.map(
        "Nav.TButton",
        background=[("active", COLORS["sidebar_active"])],
        foreground=[("active", "#FFFFFF")],
    )
    style.configure(
        "NavActive.TButton",
        font=(FONT, 11, "bold"),
        background=COLORS["sidebar_active"],
        foreground="#FFFFFF",
        padding=(12, 10),
        anchor="w",
        borderwidth=0,
    )
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=COLORS["surface_alt"],
        background=COLORS["accent"],
        thickness=8,
        borderwidth=0,
    )
    style.configure(
        "Quiz.TEntry",
        fieldbackground="#FFFFFF",
        foreground=COLORS["ink"],
        padding=10,
        font=(FONT, 13),
    )
    return style
