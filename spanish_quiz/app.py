"""Modern Tkinter Spanish quiz."""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass

import tkinter as tk
from tkinter import ttk

from .data import (
    MOOD_TENSES,
    PERSONS,
    VOCAB_LABELS,
    load_conjugations,
    load_favorites,
    load_vocabulary,
    parse_vocab_id,
    save_favorites,
    vocab_id,
)
from .theme import COLORS, FONT, apply_theme


def fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.strip().lower())
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", without_marks)


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", fold(text)).strip()


def english_matches(answer: str, definition: str) -> bool:
    guess = compact(answer)
    if not guess:
        return False
    target = compact(definition)
    if guess == target:
        return True
    pieces = re.split(r"[;/]| - ", definition)
    for piece in pieces:
        piece_norm = compact(piece)
        if not piece_norm:
            continue
        if guess == piece_norm or guess in piece_norm or piece_norm in guess:
            return True
    return guess in target


def spanish_matches(answer: str, expected: str) -> bool:
    guess = compact(answer)
    expected_norm = compact(expected)
    if not guess:
        return False
    if guess == expected_norm:
        return True
    options = re.split(r"[;/]", expected)
    return any(guess == compact(option) for option in options if compact(option))


@dataclass
class VocabCard:
    category: str
    spanish: str
    english: str

    @property
    def fav_id(self) -> str:
        return vocab_id(self.category, self.spanish)


@dataclass
class ConjPrompt:
    verb: str
    definition: str
    mood: str
    tense: str
    persons: list[str]
    forms: dict[str, str]

    @property
    def mood_label(self) -> str:
        return self.mood.replace("_", " ").title()

    @property
    def tense_label(self) -> str:
        return self.tense.replace("_", " ").title()


class SpanishQuizApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Spanish Practice")
        self.root.geometry("1180x780")
        self.root.minsize(980, 680)
        apply_theme(root)

        self.vocabulary = load_vocabulary()
        self.conjugations = load_conjugations()
        self.favorites = load_favorites()
        self.page = "home"

        self.vocab_type_vars: dict[str, tk.BooleanVar] = {}
        self.mood_vars: dict[str, tk.BooleanVar] = {}
        self.tense_vars: dict[tuple[str, str], tk.BooleanVar] = {}
        self.favorites_only = tk.BooleanVar(value=False)
        self.shuffle_conjugations = tk.BooleanVar(value=False)
        self._syncing_mood = False

        self._bind_keys()
        self._build_shell()
        self.show_home()

    def _bind_keys(self) -> None:
        self.root.bind("<Return>", self._on_enter)
        self.root.bind("<space>", self._on_space)
        self.root.bind("<Left>", lambda _e: self._nav_card(-1))
        self.root.bind("<Right>", lambda _e: self._nav_card(1))
        self.root.bind("<Control-f>", lambda _e: self.toggle_favorite())
        self.root.bind("<Control-F>", lambda _e: self.toggle_favorite())

    def _build_shell(self) -> None:
        shell = tk.Frame(self.root, bg=COLORS["bg"])
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(shell, bg=COLORS["sidebar"], width=232)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Label(
            self.sidebar,
            text="Spanish Practice",
            bg=COLORS["sidebar"],
            fg="#F7F1E8",
            font=(FONT, 15, "bold"),
            anchor="w",
            padx=22,
            pady=22,
        )
        brand.pack(fill="x")
        tk.Label(
            self.sidebar,
            text="Study vocabulary and verbs",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_muted"],
            font=(FONT, 9),
            anchor="w",
            padx=22,
        ).pack(fill="x", pady=(0, 18))

        self.nav_buttons: dict[str, tk.Button] = {}
        for key, label in (
            ("home", "Home"),
            ("vocab", "Vocabulary"),
            ("verbs", "Conjugations"),
            ("favorites", "Favorites"),
        ):
            button = tk.Button(
                self.sidebar,
                text=label,
                command=lambda k=key: self._goto(k),
                bg=COLORS["sidebar"],
                fg="#E8E4DC",
                activebackground=COLORS["sidebar_active"],
                activeforeground="#FFFFFF",
                relief="flat",
                anchor="w",
                padx=22,
                pady=11,
                font=(FONT, 11),
                cursor="hand2",
                bd=0,
                highlightthickness=0,
            )
            button.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = button

        self.fav_count = tk.Label(
            self.sidebar,
            text="",
            bg=COLORS["sidebar"],
            fg=COLORS["sidebar_muted"],
            font=(FONT, 9),
            anchor="w",
            padx=22,
            pady=16,
        )
        self.fav_count.pack(side="bottom", fill="x")

        self.content = tk.Frame(shell, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)
        self._refresh_fav_count()

    def _goto(self, key: str) -> None:
        mapping = {
            "home": self.show_home,
            "vocab": self.show_vocab_setup,
            "verbs": self.show_conj_setup,
            "favorites": self.show_favorites,
        }
        mapping[key]()

    def _set_nav(self, key: str) -> None:
        self.page = key
        for name, button in self.nav_buttons.items():
            if name == key:
                button.configure(bg=COLORS["sidebar_active"], fg="#FFFFFF", font=(FONT, 11, "bold"))
            else:
                button.configure(bg=COLORS["sidebar"], fg="#E8E4DC", font=(FONT, 11))

    def _clear(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _refresh_fav_count(self) -> None:
        total = len(self.favorites["vocab"]) + len(self.favorites["verbs"])
        self.fav_count.configure(text=f"{total} saved favorite{'s' if total != 1 else ''}")

    def persist_favorites(self) -> None:
        save_favorites(self.favorites)
        self._refresh_fav_count()

    def padded(self) -> tk.Frame:
        wrap = tk.Frame(self.content, bg=COLORS["bg"])
        wrap.pack(fill="both", expand=True)
        inner = tk.Frame(wrap, bg=COLORS["bg"])
        inner.pack(fill="both", expand=True, padx=36, pady=28)
        return inner

    def card(self, parent, **kwargs) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["surface"], bd=0, highlightthickness=1, highlightbackground=COLORS["line"], **kwargs)
        return frame

    def accent_button(self, parent, text, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["accent"],
            fg="#FFFFFF",
            activebackground=COLORS["accent_hover"],
            activeforeground="#FFFFFF",
            font=(FONT, 11, "bold"),
            relief="flat",
            padx=18,
            pady=10,
            cursor="hand2",
            bd=0,
        )

    def ghost_button(self, parent, text, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["surface_alt"],
            fg=COLORS["ink"],
            activebackground=COLORS["line"],
            font=(FONT, 11),
            relief="flat",
            padx=16,
            pady=9,
            cursor="hand2",
            bd=0,
        )

    def heading(self, parent, title: str, subtitle: str) -> None:
        tk.Label(parent, text=title, bg=COLORS["bg"], fg=COLORS["ink"], font=(FONT, 26, "bold"), anchor="w").pack(fill="x")
        tk.Label(parent, text=subtitle, bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT, 11), anchor="w").pack(fill="x", pady=(4, 22))

    def show_home(self) -> None:
        self._set_nav("home")
        self._clear()
        page = self.padded()
        self.heading(page, "Choose a study mode", "Pick vocabulary, conjugations, or jump into your favorites.")

        grid = tk.Frame(page, bg=COLORS["bg"])
        grid.pack(fill="x")
        cards = [
            ("Vocabulary", f"{sum(len(v) for v in self.vocabulary.values())} terms across {len(self.vocabulary)} types", "Build a deck by category, then flip flashcards or type English definitions.", self.show_vocab_setup),
            ("Conjugations", f"{len(self.conjugations)} verbs in the deck", "Select moods and tenses, then study the full person table for each verb.", self.show_conj_setup),
            ("Favorites", f"{len(self.favorites['vocab'])} words · {len(self.favorites['verbs'])} verbs", "Star anything during a session, then study only the items you marked.", self.show_favorites),
        ]
        for index, (title, meta, body, command) in enumerate(cards):
            tile = self.card(grid)
            tile.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            grid.columnconfigure(index, weight=1)
            inner = tk.Frame(tile, bg=COLORS["surface"])
            inner.pack(fill="both", expand=True, padx=22, pady=22)
            tk.Label(inner, text=title, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 18, "bold"), anchor="w").pack(fill="x")
            tk.Label(inner, text=meta, bg=COLORS["surface"], fg=COLORS["accent"], font=(FONT, 10), anchor="w").pack(fill="x", pady=(6, 10))
            tk.Label(inner, text=body, bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 11), wraplength=260, justify="left", anchor="w").pack(fill="x")
            self.accent_button(inner, "Open", command).pack(anchor="w", pady=(18, 0))

        tips = self.card(page)
        tips.pack(fill="x", pady=(22, 0))
        tip_inner = tk.Frame(tips, bg=COLORS["surface"])
        tip_inner.pack(fill="x", padx=22, pady=16)
        tk.Label(tip_inner, text="Shortcuts", bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 12, "bold")).pack(anchor="w")
        tk.Label(
            tip_inner,
            text="Enter checks an answer · Space flips a card · ← → moves · Ctrl+F favorites the current item",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT, 10),
        ).pack(anchor="w", pady=(4, 0))

    def show_vocab_setup(self, from_favorites: bool = False) -> None:
        self._set_nav("favorites" if from_favorites else "vocab")
        self._clear()
        page = self.padded()
        self.heading(page, "Vocabulary", "Select the types you want, then choose flashcards or typed recall.")

        types_card = self.card(page)
        types_card.pack(fill="x")
        inner = tk.Frame(types_card, bg=COLORS["surface"])
        inner.pack(fill="x", padx=20, pady=18)
        header = tk.Frame(inner, bg=COLORS["surface"])
        header.pack(fill="x")
        tk.Label(header, text="Term types", bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 13, "bold")).pack(side="left")
        tk.Button(header, text="All", command=lambda: self._set_vocab_types(True), bg=COLORS["surface_alt"], fg=COLORS["ink"], relief="flat", bd=0, padx=10, pady=4, cursor="hand2").pack(side="right")
        tk.Button(header, text="None", command=lambda: self._set_vocab_types(False), bg=COLORS["surface_alt"], fg=COLORS["ink"], relief="flat", bd=0, padx=10, pady=4, cursor="hand2").pack(side="right", padx=(0, 6))

        grid = tk.Frame(inner, bg=COLORS["surface"])
        grid.pack(fill="x", pady=(12, 0))
        self.vocab_type_vars = {}
        for index, category in enumerate(self.vocabulary):
            count = len(self.vocabulary[category])
            default_on = True
            if from_favorites:
                default_on = any(
                    vocab_id(category, term) in self.favorites["vocab"]
                    for term in self.vocabulary[category]
                )
            var = tk.BooleanVar(value=default_on)
            self.vocab_type_vars[category] = var
            box = ttk.Checkbutton(
                grid,
                text=f"{VOCAB_LABELS.get(category, category.title())}  ({count})",
                variable=var,
                style="Chip.TCheckbutton",
            )
            box.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 18), pady=4)

        options = self.card(page)
        options.pack(fill="x", pady=16)
        opt_inner = tk.Frame(options, bg=COLORS["surface"])
        opt_inner.pack(fill="x", padx=20, pady=16)
        self.favorites_only = tk.BooleanVar(value=from_favorites)
        ttk.Checkbutton(opt_inner, text="Study favorites only", variable=self.favorites_only, style="Surface.TCheckbutton").pack(anchor="w")
        tk.Label(opt_inner, text="Favorites are stored separately and never change your JSON files.", bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 9)).pack(anchor="w", pady=(4, 0))

        actions = tk.Frame(page, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(8, 0))
        self.accent_button(actions, "Start flashcards", lambda: self.start_vocab("flash")).pack(side="left")
        self.ghost_button(actions, "Type English definitions", lambda: self.start_vocab("type")).pack(side="left", padx=10)

        self.setup_status = tk.Label(page, text="", bg=COLORS["bg"], fg=COLORS["bad"], font=(FONT, 10), anchor="w")
        self.setup_status.pack(fill="x", pady=(12, 0))

    def _set_vocab_types(self, value: bool) -> None:
        for var in self.vocab_type_vars.values():
            var.set(value)

    def _vocab_pool(self) -> list[VocabCard]:
        selected = [cat for cat, var in self.vocab_type_vars.items() if var.get()]
        cards: list[VocabCard] = []
        favs = set(self.favorites["vocab"])
        for category in selected:
            for spanish, english in self.vocabulary.get(category, {}).items():
                card = VocabCard(category, spanish, english)
                if self.favorites_only.get() and card.fav_id not in favs:
                    continue
                cards.append(card)
        random.shuffle(cards)
        return cards

    def start_vocab(self, mode: str) -> None:
        if not any(var.get() for var in self.vocab_type_vars.values()):
            self.setup_status.configure(text="Select at least one vocabulary type.")
            return
        deck = self._vocab_pool()
        if not deck:
            self.setup_status.configure(text="No terms match those filters. Select types or add favorites first.")
            return
        self.session = {
            "kind": "vocab",
            "mode": mode,
            "deck": deck,
            "index": 0,
            "flipped": False,
            "checked": False,
            "correct": 0,
            "seen": 0,
        }
        self.show_vocab_session()

    def show_vocab_session(self) -> None:
        self._set_nav("vocab")
        self._clear()
        page = self.padded()
        session = self.session
        card: VocabCard = session["deck"][session["index"]]
        total = len(session["deck"])
        index = session["index"] + 1

        top = tk.Frame(page, bg=COLORS["bg"])
        top.pack(fill="x")
        tk.Label(top, text=f"{VOCAB_LABELS.get(card.category, card.category).upper()}", bg=COLORS["bg"], fg=COLORS["accent"], font=(FONT, 10, "bold")).pack(anchor="w")
        tk.Label(top, text=f"{index} of {total}", bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT, 10)).pack(anchor="w", pady=(2, 8))
        bar = ttk.Progressbar(page, maximum=total, value=index, mode="determinate")
        bar.pack(fill="x", pady=(0, 18))

        quiz = self.card(page)
        quiz.pack(fill="both", expand=True)
        body = tk.Frame(quiz, bg=COLORS["surface"])
        body.pack(fill="both", expand=True, padx=36, pady=28)

        header = tk.Frame(body, bg=COLORS["surface"])
        header.pack(fill="x")
        tk.Label(header, text="Spanish → English" if session["mode"] == "type" else "Flashcard", bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 10)).pack(side="left")
        self.star_button = tk.Button(
            header,
            text=self._star_text(card.fav_id in self.favorites["vocab"]),
            command=self.toggle_favorite,
            bg=COLORS["surface"],
            fg=COLORS["star"],
            relief="flat",
            bd=0,
            font=(FONT, 18),
            cursor="hand2",
        )
        self.star_button.pack(side="right")

        if session["mode"] == "flash":
            shown = card.english if session["flipped"] else card.spanish
            hint = "English" if session["flipped"] else "Spanish"
            tk.Label(body, text=hint, bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 11)).pack(pady=(40, 8))
            tk.Label(body, text=shown, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 32, "bold"), wraplength=720, justify="center").pack()
            tk.Label(body, text="Click the card area or press Space to flip", bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 10)).pack(pady=(24, 0))
            quiz.bind("<Button-1>", lambda _e: self.flip_card())
            body.bind("<Button-1>", lambda _e: self.flip_card())
        else:
            tk.Label(body, text=card.spanish, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 30, "bold"), wraplength=720, justify="center").pack(pady=(28, 18))
            tk.Label(body, text="Type an English meaning", bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 10)).pack()
            self.answer_var = tk.StringVar()
            self.answer_entry = ttk.Entry(body, textvariable=self.answer_var, style="Quiz.TEntry", font=(FONT, 14))
            self.answer_entry.pack(fill="x", pady=12, ipady=8)
            self.feedback = tk.Label(body, text="", bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 12), wraplength=700, justify="left")
            self.feedback.pack(fill="x", pady=(4, 0))
            self.root.after(50, self.answer_entry.focus_set)
            if session["checked"]:
                self._show_vocab_result(card)

        controls = tk.Frame(page, bg=COLORS["bg"])
        controls.pack(fill="x", pady=18)
        self.ghost_button(controls, "Back", self.show_vocab_setup).pack(side="left")
        self.ghost_button(controls, "Previous", lambda: self._nav_card(-1)).pack(side="right")
        if session["mode"] == "flash":
            self.accent_button(controls, "Flip", self.flip_card).pack(side="right", padx=8)
            self.ghost_button(controls, "Next", lambda: self._nav_card(1)).pack(side="right")
        else:
            self.accent_button(controls, "Check", self.check_vocab).pack(side="right", padx=8)
            self.ghost_button(controls, "Next", lambda: self._nav_card(1)).pack(side="right")
        score = f"{session['correct']} correct · {session['seen']} checked"
        tk.Label(controls, text=score, bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT, 10)).pack(side="left", padx=16)

    def _show_vocab_result(self, card: VocabCard) -> None:
        guess = self.answer_var.get()
        ok = english_matches(guess, card.english)
        self.feedback.configure(
            text=("Nice. " if ok else "Not quite. ") + card.english,
            fg=COLORS["good"] if ok else COLORS["bad"],
        )

    def check_vocab(self) -> None:
        session = getattr(self, "session", None)
        if not session or session.get("kind") != "vocab" or session.get("mode") != "type":
            return
        if session["checked"]:
            self._nav_card(1)
            return
        card: VocabCard = session["deck"][session["index"]]
        ok = english_matches(self.answer_var.get(), card.english)
        session["checked"] = True
        session["seen"] += 1
        if ok:
            session["correct"] += 1
        self._show_vocab_result(card)

    def flip_card(self) -> None:
        session = getattr(self, "session", None)
        if not session:
            return
        if session.get("kind") == "vocab" and session.get("mode") == "flash":
            session["flipped"] = not session["flipped"]
            self.show_vocab_session()
        elif session.get("kind") == "conj" and session.get("mode") == "flash":
            session["flipped"] = not session["flipped"]
            self.show_conj_session()

    def show_conj_setup(self, from_favorites: bool = False) -> None:
        self._set_nav("favorites" if from_favorites else "verbs")
        self._clear()
        page = self.padded()
        self.heading(page, "Conjugations", "Each card is one verb in one mood and tense, with every person form together.")

        canvas_host = tk.Frame(page, bg=COLORS["bg"])
        canvas_host.pack(fill="both", expand=True)

        moods_card = self.card(canvas_host)
        moods_card.pack(fill="x")
        inner = tk.Frame(moods_card, bg=COLORS["surface"])
        inner.pack(fill="x", padx=20, pady=18)
        tk.Label(inner, text="Moods and tenses", bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 13, "bold")).pack(anchor="w")

        self.mood_vars = {}
        self.tense_vars = {}
        grid = tk.Frame(inner, bg=COLORS["surface"])
        grid.pack(fill="x", pady=(10, 0))
        for col, (mood, tenses) in enumerate(MOOD_TENSES.items()):
            column = tk.Frame(grid, bg=COLORS["surface"])
            column.grid(row=0, column=col, sticky="nw", padx=(0, 28))
            mood_var = tk.BooleanVar(value=False)
            self.mood_vars[mood] = mood_var
            ttk.Checkbutton(
                column,
                text=mood.title(),
                variable=mood_var,
                style="Chip.TCheckbutton",
                command=lambda m=mood: self._sync_mood(m),
            ).pack(anchor="w", pady=(0, 6))
            for tense in tenses:
                var = tk.BooleanVar(value=False)
                self.tense_vars[(mood, tense)] = var
                ttk.Checkbutton(
                    column,
                    text=tense.title(),
                    variable=var,
                    style="Chip.TCheckbutton",
                    command=lambda m=mood: self._on_tense_changed(m),
                ).pack(anchor="w")

        extras = self.card(page)
        extras.pack(fill="x", pady=14)
        extra_inner = tk.Frame(extras, bg=COLORS["surface"])
        extra_inner.pack(fill="x", padx=20, pady=16)
        self.favorites_only = tk.BooleanVar(value=from_favorites)
        self.shuffle_conjugations = tk.BooleanVar(value=False)
        ttk.Checkbutton(extra_inner, text="Shuffle cards", variable=self.shuffle_conjugations, style="Surface.TCheckbutton").pack(anchor="w")
        ttk.Checkbutton(extra_inner, text="Study favorite verbs only", variable=self.favorites_only, style="Surface.TCheckbutton").pack(anchor="w")
        tk.Label(
            extra_inner,
            text="You will see each verb once for every selected mood and tense, with yo / tú / él / nosotros / ellos together.",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=(FONT, 10),
            wraplength=780,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        actions = tk.Frame(page, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(10, 0))
        self.accent_button(actions, "Type the forms", lambda: self.start_conj("type")).pack(side="left")
        self.ghost_button(actions, "Flashcards", lambda: self.start_conj("flash")).pack(side="left", padx=10)
        self.setup_status = tk.Label(page, text="", bg=COLORS["bg"], fg=COLORS["bad"], font=(FONT, 10), anchor="w")
        self.setup_status.pack(fill="x", pady=(12, 0))

    def _sync_mood(self, mood: str) -> None:
        enabled = self.mood_vars[mood].get()
        self._syncing_mood = True
        try:
            for tense in MOOD_TENSES[mood]:
                self.tense_vars[(mood, tense)].set(enabled)
        finally:
            self._syncing_mood = False

    def _on_tense_changed(self, mood: str) -> None:
        if self._syncing_mood:
            return
        self.mood_vars[mood].set(False)

    def _selected_tenses(self) -> list[tuple[str, str]]:
        return [(mood, tense) for (mood, tense), var in self.tense_vars.items() if var.get()]

    def _build_conj_prompts(self) -> list[ConjPrompt]:
        tenses = self._selected_tenses()
        verbs = list(self.conjugations)
        if self.favorites_only.get():
            verbs = [verb for verb in verbs if verb in set(self.favorites["verbs"])]
        deck: list[ConjPrompt] = []
        seen: set[tuple[str, str, str]] = set()
        for verb in verbs:
            entry = self.conjugations[verb]
            for mood, tense in tenses:
                key = (verb, mood, tense)
                if key in seen:
                    continue
                forms = entry.get(mood, {}).get(tense, {})
                if not isinstance(forms, dict) or not forms:
                    continue
                persons = [person for person in PERSONS if person in forms]
                if not persons:
                    persons = list(forms)
                seen.add(key)
                deck.append(
                    ConjPrompt(
                        verb=verb,
                        definition=entry.get("definition", ""),
                        mood=mood,
                        tense=tense,
                        persons=persons,
                        forms={person: forms[person] for person in persons},
                    )
                )
        if self.shuffle_conjugations.get():
            random.shuffle(deck)
        return deck

    def start_conj(self, mode: str) -> None:
        if not self._selected_tenses():
            self.setup_status.configure(text="Select at least one mood or tense.")
            return
        deck = self._build_conj_prompts()
        if not deck:
            self.setup_status.configure(text="No conjugation prompts match those filters.")
            return
        self.session = {
            "kind": "conj",
            "mode": mode,
            "deck": deck,
            "index": 0,
            "flipped": False,
            "checked": False,
            "correct": 0,
            "seen": 0,
            "guesses": {},
            "locked": [],
            "complete": False,
        }
        self.show_conj_session()

    def show_conj_session(self) -> None:
        self._set_nav("verbs")
        self._clear()
        page = self.padded()
        session = self.session
        prompt: ConjPrompt = session["deck"][session["index"]]
        total = len(session["deck"])
        index = session["index"] + 1

        tk.Label(page, text=f"{index} of {total}", bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT, 10)).pack(anchor="w")
        ttk.Progressbar(page, maximum=total, value=index).pack(fill="x", pady=(6, 18))

        quiz = self.card(page)
        quiz.pack(fill="both", expand=True)
        body = tk.Frame(quiz, bg=COLORS["surface"])
        body.pack(fill="both", expand=True, padx=36, pady=24)

        header = tk.Frame(body, bg=COLORS["surface"])
        header.pack(fill="x")
        self.star_button = tk.Button(
            header,
            text=self._star_text(prompt.verb in self.favorites["verbs"]),
            command=self.toggle_favorite,
            bg=COLORS["surface"],
            fg=COLORS["star"],
            relief="flat",
            bd=0,
            font=(FONT, 18),
            cursor="hand2",
        )
        self.star_button.pack(side="right", anchor="n")

        tk.Label(header, text=prompt.mood_label, bg=COLORS["surface"], fg=COLORS["accent"], font=(FONT, 13, "bold")).pack(anchor="w")
        tk.Label(header, text=prompt.tense_label, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 32, "bold")).pack(anchor="w", pady=(2, 6))
        verb_line = tk.Frame(header, bg=COLORS["surface"])
        verb_line.pack(anchor="w")
        tk.Label(verb_line, text=prompt.verb, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 20, "bold")).pack(side="left")
        if prompt.definition:
            tk.Label(verb_line, text=f"  ·  {prompt.definition}", bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 12)).pack(side="left")

        table = tk.Frame(body, bg=COLORS["surface"])
        table.pack(fill="both", expand=True, pady=(18, 0))
        show_answers = session["mode"] == "flash" and session["flipped"]
        self.answer_vars = {}
        self.form_entries: dict[str, tk.Entry] = {}
        self.form_rows: dict[str, tk.Frame] = {}
        self.form_labels: dict[str, tk.Label] = {}
        self.form_status: dict[str, tk.Label] = {}
        guesses = session.get("guesses") or {}
        locked = set(session.get("locked") or [])

        first_unlocked = None
        for row_index, person in enumerate(prompt.persons):
            is_locked = person in locked
            row_bg = COLORS["locked_row"] if is_locked else (COLORS["surface_alt"] if row_index % 2 else COLORS["surface"])
            row = tk.Frame(table, bg=row_bg)
            row.pack(fill="x", pady=2)
            self.form_rows[person] = row
            person_label = tk.Label(
                row,
                text=person,
                bg=row_bg,
                fg=COLORS["muted"],
                font=(FONT, 12),
                width=18,
                anchor="w",
            )
            person_label.pack(side="left", padx=(14, 12), pady=10)
            self.form_labels[person] = person_label
            if session["mode"] == "flash":
                form_text = prompt.forms[person] if show_answers else "—"
                tk.Label(row, text=form_text, bg=row_bg, fg=COLORS["ink"], font=(FONT, 16, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
            else:
                var = tk.StringVar(value=guesses.get(person, ""))
                self.answer_vars[person] = var
                entry = tk.Entry(
                    row,
                    textvariable=var,
                    font=(FONT, 13),
                    bg=COLORS["locked_bg"] if is_locked else "#FFFFFF",
                    fg=COLORS["ink"],
                    disabledbackground=COLORS["locked_bg"],
                    disabledforeground=COLORS["ink"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=COLORS["line"],
                    insertbackground=COLORS["ink"],
                )
                entry.pack(side="left", fill="x", expand=True, padx=(0, 12), ipady=6)
                if is_locked:
                    entry.configure(state="disabled")
                else:
                    first_unlocked = first_unlocked or entry
                self.form_entries[person] = entry
                status = tk.Label(row, text="Locked" if is_locked else "", bg=row_bg, fg=COLORS["good"] if is_locked else COLORS["muted"], font=(FONT, 11), width=12, anchor="w")
                status.pack(side="left", padx=(0, 12))
                self.form_status[person] = status

        if session["mode"] == "flash":
            hint = "All person forms" if show_answers else "Flip to see every person form"
            tk.Label(body, text=hint, bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 10)).pack(pady=(16, 0))
            quiz.bind("<Button-1>", lambda _e: self.flip_card())
            body.bind("<Button-1>", lambda _e: self.flip_card())
        else:
            self.feedback = tk.Label(body, text="", bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 11), anchor="w")
            self.feedback.pack(fill="x", pady=(14, 0))
            if locked:
                self._apply_conj_lock_state(prompt)
            if first_unlocked is not None:
                self.answer_entry = first_unlocked
                self.root.after(50, first_unlocked.focus_set)

        controls = tk.Frame(page, bg=COLORS["bg"])
        controls.pack(fill="x", pady=18)
        self.ghost_button(controls, "Back", self.show_conj_setup).pack(side="left")
        if session["mode"] == "type":
            clear_btn = tk.Button(
                controls,
                text="Clear responses",
                command=self.clear_conj_incorrect,
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                activebackground=COLORS["surface_alt"],
                font=(FONT, 9),
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                bd=0,
            )
            clear_btn.pack(side="left", padx=(8, 0))
            self.clear_conj_button = clear_btn
        self.ghost_button(controls, "Previous", lambda: self._nav_card(-1)).pack(side="right")
        if session["mode"] == "flash":
            self.accent_button(controls, "Flip", self.flip_card).pack(side="right", padx=8)
            self.ghost_button(controls, "Next", lambda: self._nav_card(1)).pack(side="right")
        else:
            self.accent_button(controls, "Check", self.check_conj).pack(side="right", padx=8)
            self.next_button = self.ghost_button(controls, "Next", lambda: self._nav_card(1))
            self.next_button.pack(side="right")
            self._set_conj_next_enabled(bool(session.get("complete")))
        tk.Label(controls, text=f"{session['correct']} correct · {session['seen']} forms checked", bg=COLORS["bg"], fg=COLORS["muted"], font=(FONT, 10)).pack(side="left", padx=16)

    def _show_conj_result(self, prompt: ConjPrompt) -> None:
        results = self.session.get("results") or {}
        right = 0
        for person in prompt.persons:
            ok = results.get(person, False)
            expected = prompt.forms[person]
            if ok:
                right += 1
                text, color = "Correct", COLORS["good"]
            else:
                text, color = expected, COLORS["bad"]
            if person in self.form_status:
                self.form_status[person].configure(text=text, fg=color)
        total = len(prompt.persons)
        self.feedback.configure(
            text=f"{right} of {total} forms correct",
            fg=COLORS["good"] if right == total else COLORS["bad"],
        )

    def check_conj(self) -> None:
        session = getattr(self, "session", None)
        if not session or session.get("kind") != "conj" or session.get("mode") != "type":
            return
        if session["checked"]:
            self._nav_card(1)
            return
        prompt: ConjPrompt = session["deck"][session["index"]]
        guesses = {person: var.get() for person, var in self.answer_vars.items()}
        results = {
            person: spanish_matches(guesses.get(person, ""), prompt.forms[person])
            for person in prompt.persons
        }
        session["guesses"] = guesses
        session["results"] = results
        session["checked"] = True
        session["seen"] += len(prompt.persons)
        session["correct"] += sum(1 for ok in results.values() if ok)
        self._show_conj_result(prompt)

    def show_favorites(self) -> None:
        self._set_nav("favorites")
        self._clear()
        page = self.padded()
        self.heading(page, "Favorites", "Star items while you study. This list lives in user_favorites.json, not in the source data.")

        columns = tk.Frame(page, bg=COLORS["bg"])
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=1)
        columns.columnconfigure(1, weight=1)

        vocab_card = self.card(columns)
        vocab_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._favorites_column(
            vocab_card,
            f"Vocabulary ({len(self.favorites['vocab'])})",
            [
                (parse_vocab_id(item_id)[1], self.vocabulary.get(parse_vocab_id(item_id)[0], {}).get(parse_vocab_id(item_id)[1], ""))
                for item_id in self.favorites["vocab"]
            ],
            empty="No favorite words yet.",
        )

        verb_card = self.card(columns)
        verb_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._favorites_column(
            verb_card,
            f"Verbs ({len(self.favorites['verbs'])})",
            [(verb, self.conjugations.get(verb, {}).get("definition", "")) for verb in self.favorites["verbs"]],
            empty="No favorite verbs yet.",
        )

        actions = tk.Frame(page, bg=COLORS["bg"])
        actions.pack(fill="x", pady=18)
        self.accent_button(actions, "Quiz favorite vocabulary", lambda: self.show_vocab_setup(True)).pack(side="left")
        self.ghost_button(actions, "Quiz favorite verbs", lambda: self.show_conj_setup(True)).pack(side="left", padx=10)

    def _favorites_column(self, parent, title: str, rows: list[tuple[str, str]], empty: str) -> None:
        inner = tk.Frame(parent, bg=COLORS["surface"])
        inner.pack(fill="both", expand=True, padx=18, pady=16)
        tk.Label(inner, text=title, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 14, "bold")).pack(anchor="w")
        if not rows:
            tk.Label(inner, text=empty, bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w", pady=8)
            return
        holder = tk.Frame(inner, bg=COLORS["surface"])
        holder.pack(fill="both", expand=True, pady=(8, 0))
        canvas = tk.Canvas(holder, bg=COLORS["surface"], highlightthickness=0, height=360)
        scroll = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        list_frame = tk.Frame(canvas, bg=COLORS["surface"])
        list_frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for left, right in rows:
            row = tk.Frame(list_frame, bg=COLORS["surface"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=left, bg=COLORS["surface"], fg=COLORS["ink"], font=(FONT, 11, "bold"), anchor="w").pack(side="left")
            tk.Label(row, text=right, bg=COLORS["surface"], fg=COLORS["muted"], font=(FONT, 9), wraplength=220, justify="right", anchor="e").pack(side="right")

    def toggle_favorite(self) -> None:
        session = getattr(self, "session", None)
        if not session:
            return
        if session["kind"] == "vocab":
            card: VocabCard = session["deck"][session["index"]]
            item_id = card.fav_id
            if item_id in self.favorites["vocab"]:
                self.favorites["vocab"].remove(item_id)
                starred = False
            else:
                self.favorites["vocab"].append(item_id)
                starred = True
        else:
            prompt: ConjPrompt = session["deck"][session["index"]]
            if prompt.verb in self.favorites["verbs"]:
                self.favorites["verbs"].remove(prompt.verb)
                starred = False
            else:
                self.favorites["verbs"].append(prompt.verb)
                starred = True
        self.persist_favorites()
        if hasattr(self, "star_button") and self.star_button.winfo_exists():
            self.star_button.configure(text=self._star_text(starred))

    def _star_text(self, starred: bool) -> str:
        return "★" if starred else "☆"

    def _nav_card(self, delta: int) -> None:
        session = getattr(self, "session", None)
        if not session or "deck" not in session:
            return
        new_index = session["index"] + delta
        if new_index < 0 or new_index >= len(session["deck"]):
            return
        session["index"] = new_index
        session["flipped"] = False
        session["checked"] = False
        session["guesses"] = {}
        session["results"] = {}
        if session["kind"] == "vocab":
            self.show_vocab_session()
        else:
            self.show_conj_session()

    def _on_enter(self, _event=None) -> str | None:
        session = getattr(self, "session", None)
        if not session:
            return None
        if session.get("mode") == "type":
            if session["kind"] == "vocab":
                self.check_vocab()
            else:
                self.check_conj()
            return "break"
        return None

    def _on_space(self, event=None) -> str | None:
        widget = self.root.focus_get()
        if isinstance(widget, ttk.Entry) or isinstance(widget, tk.Entry):
            return None
        session = getattr(self, "session", None)
        if session and session.get("mode") == "flash":
            self.flip_card()
            return "break"
        return None


def run() -> None:
    root = tk.Tk()
    SpanishQuizApp(root)
    root.mainloop()
