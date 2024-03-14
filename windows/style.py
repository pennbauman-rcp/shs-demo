import tkinter
from tkinter import ttk


TEXT_C = "#eeeeee"
BRIGHT_C = "#FFC300"
BG_C1 = "#000000"
BG_C2 = "#333333"

ENTRY_LAYOUT = [(
        'Entry.plain.field',
        {'children': [(
                'Entry.background', {'children': [(
                        'Entry.padding', {'children': [(
                                'Entry.textarea', {'sticky': 'nswe'}
                            )],
                            'sticky': 'nswe'}
                    )], 'sticky': 'nswe'}
            )],
            'border':'0', 'sticky': 'nswe'}
    )]


def get_style():
    style = ttk.Style()

    # Text
    style.configure("WinTitle.TLabel",
            font=("Terminal", 24),
            foreground=TEXT_C,
            background=BG_C1,
            padding=5
        )
    style.configure("SubTitle.TLabel",
            font=("Terminal", 16),
            foreground=BRIGHT_C,
            background=BG_C2,
            padding=5
        )
    style.configure("SubTitleOff.TLabel",
            font=("Terminal", 16),
            foreground=TEXT_C,
            background=BG_C2,
            padding=5,
        )
    style.configure("InBox.TLabel",
            font=("Terminal", 12),
            foreground=TEXT_C,
            background=BG_C2,
            padding=(10, 5),
        )
    style.configure("BrightInBox.TLabel",
            font=("Terminal", 12),
            foreground=BRIGHT_C,
            background=BG_C2,
            padding=(10, 5),
        )
    style.configure("OutBox.TLabel",
            font=("Terminal", 12),
            foreground=TEXT_C,
            background=BG_C1,
            padding=(10, 5),
        )

    # Frames
    style.configure("Box.TFrame",
            # outline=TEXT_C,
            # background="green",
            background=BG_C2,
            padding=10,
            # padx=15,
            # pady=15,
        )
    style.configure("InBox.TFrame",
            background=BG_C2,
            padding=(10, 0),
        )
    style.configure("OutBox.TFrame",
            background=BG_C1,
        )

    # Buttons
    style.configure("Button.TButton",
            font=("Terminal", 12),
            borderwidth=0,
            relief="flat",
            padding=5
        )
    style.map("Button.TButton",
            foreground=[("!active", BG_C1), ("active", TEXT_C)],
            background=[("!active", TEXT_C), ("active", BG_C1)],
        )
    style.configure("BigButton.TButton",
            font=("Terminal", 16),
            borderwidth=0,
            relief="flat",
            padding=10
        )
    style.map("BigButton.TButton",
            foreground=[("!active", BG_C1), ("active", BRIGHT_C)],
            background=[("!active", BRIGHT_C), ("active", BG_C2)],
        )

    # Entry
    style.element_create("plain.field", "from", "clam")
    style.layout("Num.TEntry", ENTRY_LAYOUT)
    style.configure("Num.TEntry",
            font=("Terminal", 12),
            borderwidth=5,
            relief="flat",
            border=BRIGHT_C,
            foreground=TEXT_C,
            background=BG_C1,
            fieldbackground=BG_C1,
            padding=(10, 5)
        )
    style.layout("NumError.TEntry", ENTRY_LAYOUT)
    style.configure("NumError.TEntry",
            font=("Terminal", 12),
            borderwidth=5,
            relief="flat",
            border=BRIGHT_C,
            foreground=BG_C1,
            background="red",
            fieldbackground="red",
            padding=(10, 5)
        )
    # style.layout("Text.TEntry", ENTRY_LAYOUT)
    style.configure("Text.TEntry",
            font=("Terminal", 12),
            borderwidth=0,
            relief="flat",
            border=BRIGHT_C,
            foreground=BG_C1,
            padding=(10, 5)
        )

    return style
