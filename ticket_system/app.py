"""
app.py  –  Ticket Generating System
Dark theme: charcoal background, vivid colored buttons, clear contrast,to be improved
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import database as db
import ticket_generator as tg

# ── Palette ────────────────────────────────────────────────────────────────
BG        = "#1E1E2E"   # deep blue-grey page
SIDEBAR   = "#13131F"   # darker sidebar
CARD      = "#27273A"   # card background
CARD2     = "#32324A"   # slightly lighter
INPUT_BG  = "#32324A"
BORDER    = "#44445A"

# Buttons - all clearly visible with strong colors
BTN_PRIMARY    = "#7C5CBF"   # purple
BTN_PRIMARY_H  = "#6A4DAD"
BTN_PRIMARY_FG = "#FFFFFF"

BTN_GREEN      = "#2D8A4E"   # green for success actions
BTN_GREEN_H    = "#236E3E"
BTN_GREEN_FG   = "#FFFFFF"

BTN_RED        = "#C0392B"   # red for danger
BTN_RED_H      = "#A93226"
BTN_RED_FG     = "#FFFFFF"

BTN_GREY       = "#44445A"   # secondary
BTN_GREY_H     = "#55556A"
BTN_GREY_FG    = "#FFFFFF"

BTN_BLUE       = "#2471A3"   # blue for export/info
BTN_BLUE_H     = "#1A5276"
BTN_BLUE_FG    = "#FFFFFF"

TEXT1      = "#EEEEF5"
TEXT2      = "#AAAACC"
TEXT3      = "#66667A"
SIDEBAR_FG = "#8888AA"
SIDEBAR_A  = "#FFFFFF"
SIDEBAR_AB = "#32324A"

SUCCESS_FG = "#4CD97B"
DANGER_FG  = "#FF6B6B"
WARNING_FG = "#F0A500"

FONT_H1    = ("Helvetica Neue", 22, "bold")
FONT_H2    = ("Helvetica Neue", 14, "bold")
FONT_BODY  = ("Helvetica Neue", 11)
FONT_SMALL = ("Helvetica Neue", 10)
FONT_LABEL = ("Helvetica Neue", 9)
FONT_MONO  = ("Menlo", 10)


# ══════════════════════════════════════════════════════════════════════════════
# Widget helpers
# ══════════════════════════════════════════════════════════════════════════════

def lbl(parent, text, font=FONT_BODY, fg=TEXT1, bg=CARD, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

def frm(parent, bg=CARD, **kw):
    return tk.Frame(parent, bg=bg, **kw)

def inp(parent, textvariable=None, show=None, width=30):
    return tk.Entry(
        parent, textvariable=textvariable, show=show, width=width,
        bg=INPUT_BG, fg=TEXT1, insertbackground=BTN_PRIMARY,
        relief="flat", bd=0, font=FONT_BODY,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=BTN_PRIMARY,
    )

def btn(parent, text, command, bg=BTN_PRIMARY, fg=BTN_PRIMARY_FG,
        hover=BTN_PRIMARY_H, font=FONT_BODY, width=None, padx=16, pady=9):
    b = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg,
        activebackground=hover, activeforeground=fg,
        relief="flat", font=font,
        cursor="hand2", bd=0,
        padx=padx, pady=pady,
    )
    if width: b.config(width=width)
    return b

def card_frame(parent, **kw):
    return tk.Frame(parent, bg=CARD,
                    highlightthickness=1,
                    highlightbackground=BORDER, **kw)

def divider(parent):
    return tk.Frame(parent, bg=BORDER, height=1)

def field(parent, label_text, row, textvariable=None, show=None):
    lbl(parent, label_text, font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
        row=row*2, column=0, sticky="w", padx=20, pady=(14, 3))
    e = inp(parent, textvariable=textvariable, show=show)
    e.grid(row=row*2+1, column=0, sticky="ew", padx=20)
    return e


# ══════════════════════════════════════════════════════════════════════════════
# Login
# ══════════════════════════════════════════════════════════════════════════════

class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title("Sign in")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._center(400, 480)
        self._build()
        self.protocol("WM_DELETE_WINDOW", master.destroy)

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        # Brand bar
        top = frm(self, bg=SIDEBAR)
        top.pack(fill="x")
        tk.Label(top, text="🎫  Ticket System",
                 font=("Helvetica Neue", 13, "bold"),
                 fg=TEXT1, bg=SIDEBAR, pady=16).pack(padx=20, anchor="w")

        card = card_frame(self)
        card.pack(fill="both", expand=True, padx=28, pady=24)
        card.columnconfigure(0, weight=1)

        lbl(card, "Welcome back", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 2))
        lbl(card, "Sign in to continue.", font=FONT_SMALL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky="w", padx=20, pady=(0, 12))
        divider(card).grid(row=2, column=0, sticky="ew")

        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()
        field(card, "Username", 1, self.var_user)
        field(card, "Password", 2, self.var_pass, show="•")

        self.err = lbl(card, "", font=FONT_SMALL, fg=DANGER_FG, bg=CARD)
        self.err.grid(row=7, column=0, padx=20, pady=(8, 0), sticky="w")

        divider(card).grid(row=8, column=0, sticky="ew", pady=(14, 0))

        # VISIBLE purple Sign in button
        btn(card, "Sign in", self._login,
            bg=BTN_PRIMARY, fg=BTN_PRIMARY_FG,
            hover=BTN_PRIMARY_H, width=26).grid(
            row=9, column=0, padx=20, pady=18, sticky="w")

        self.bind("<Return>", lambda e: self._login())

    def _login(self):
        user = self.var_user.get().strip()
        pwd  = self.var_pass.get()
        if not user or not pwd:
            self.err.config(text="Please fill in both fields."); return
        try:
            result = db.verify_user(user, pwd)
        except Exception as ex:
            self.err.config(text=f"Database error: {ex}"); return
        if result:
            self.destroy(); self.on_success(result)
        else:
            self.err.config(text="Invalid username or password.")
            self.var_pass.set("")


# ══════════════════════════════════════════════════════════════════════════════
# Main App
# ══════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        try:
            db.init_db()
        except Exception as ex:
            self.deiconify()
            messagebox.showerror("Database Error",
                f"Could not connect to MySQL.\n\n{ex}\n\nEdit DB_CONFIG in database.py.")
            self.destroy(); return

        self.current_user = None
        self.title("Ticket System")
        self.configure(bg=BG)
        self.geometry("1120x720")
        self._center()
        self._show_login()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1120x720+{(sw-1120)//2}+{(sh-720)//2}")

    def _show_login(self):
        LoginWindow(self, self._on_login)

    def _on_login(self, user):
        self.current_user = user
        self.deiconify()
        self._build()

    def _build(self):
        self.sidebar = frm(self, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = frm(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._build_sidebar()
        self._show("issue")

    def _build_sidebar(self):
        sb = self.sidebar
        brand = frm(sb, bg="#0A0A14")
        brand.pack(fill="x")
        tk.Label(brand, text="🎫  Ticket System",
                 font=("Helvetica Neue", 12, "bold"),
                 fg=TEXT1, bg="#0A0A14", pady=16).pack(padx=16, anchor="w")

        user_row = frm(sb, bg=SIDEBAR)
        user_row.pack(fill="x", padx=12, pady=(10, 12))
        initials = self.current_user["username"][:2].upper()
        tk.Label(user_row, text=initials,
                 font=("Helvetica Neue", 10, "bold"),
                 fg="#FFFFFF", bg=BTN_PRIMARY,
                 width=3, pady=5).pack(side="left", padx=(0, 10))
        tk.Label(user_row, text=self.current_user["username"],
                 font=FONT_SMALL, fg=TEXT2, bg=SIDEBAR).pack(side="left")

        frm(sb, bg=BORDER, height=1).pack(fill="x", padx=14, pady=6)

        pages = [
            ("🎟  Issue ticket",    "issue"),
            ("📅  Events",          "events"),
            ("📋  All tickets",     "tickets"),
            ("🔒  Change password", "password"),
        ]
        self.nav_btns = {}
        for label, key in pages:
            b = tk.Button(
                sb, text=label, anchor="w",
                font=FONT_BODY, bg=SIDEBAR, fg=SIDEBAR_FG,
                activebackground=SIDEBAR_AB, activeforeground=SIDEBAR_A,
                relief="flat", bd=0, padx=16, pady=11,
                cursor="hand2", command=lambda k=key: self._show(k),
            )
            b.pack(fill="x", padx=6)
            self.nav_btns[key] = b

        frm(sb, bg=SIDEBAR).pack(fill="both", expand=True)
        frm(sb, bg=BORDER, height=1).pack(fill="x", padx=14, pady=4)
        tk.Button(sb, text="  ⏻  Sign out", anchor="w",
                  font=FONT_SMALL, bg=SIDEBAR, fg=TEXT3,
                  activebackground=CARD, activeforeground=TEXT2,
                  relief="flat", bd=0, padx=20, pady=12,
                  cursor="hand2", command=self._logout).pack(fill="x")

    def _show(self, key):
        for w in self.content.winfo_children():
            w.destroy()
        for k, b in self.nav_btns.items():
            b.config(bg=SIDEBAR_AB if k == key else SIDEBAR,
                     fg=SIDEBAR_A  if k == key else SIDEBAR_FG)
        {"issue": IssuePage, "events": EventsPage,
         "tickets": TicketsPage, "password": PasswordPage}[key](
            self.content, self.current_user)

    def _logout(self):
        if messagebox.askyesno("Sign out", "Sign out of your account?"):
            for w in self.winfo_children():
                w.destroy()
            self.withdraw()
            self._show_login()


# ══════════════════════════════════════════════════════════════════════════════
# Issue Ticket Page
# ══════════════════════════════════════════════════════════════════════════════

class IssuePage(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self.last_ticket = None
        self.qr_photo    = None
        self._build()

    def _build(self):
        hdr = frm(self, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(24, 16))
        lbl(hdr, "Issue ticket", font=FONT_H1, fg=TEXT1, bg=BG).pack(side="left")

        body = frm(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Left form ─────────────────────────────────────────────────
        form = card_frame(body)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form.columnconfigure(0, weight=1)

        lbl(form, "Attendee details", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 2))
        lbl(form, "Enter info and select an event.",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky="w", padx=20)
        divider(form).grid(row=2, column=0, sticky="ew", pady=(12, 0))

        self.var_name  = tk.StringVar()
        self.var_email = tk.StringVar()
        field(form, "Full name", 1, self.var_name)
        field(form, "Email address", 2, self.var_email)

        lbl(form, "Event", font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
            row=7, column=0, sticky="w", padx=20, pady=(14, 3))
        self._setup_combo()
        self.combo = ttk.Combobox(form, state="readonly",
                                  font=FONT_BODY, style="Dark.TCombobox")
        self.combo.grid(row=8, column=0, sticky="ew", padx=20)
        self._load_events()

        divider(form).grid(row=9, column=0, sticky="ew", pady=(18, 0))

        btn_row = frm(form, bg=CARD)
        btn_row.grid(row=10, column=0, padx=20, pady=18, sticky="w")

        # VISIBLE purple Issue ticket button
        btn(btn_row, "🎟  Issue ticket", self._issue,
            bg=BTN_PRIMARY, fg=BTN_PRIMARY_FG,
            hover=BTN_PRIMARY_H).pack(side="left", padx=(0, 10))

        # VISIBLE grey Clear button
        btn(btn_row, "Clear", self._clear,
            bg=BTN_GREY, fg=BTN_GREY_FG,
            hover=BTN_GREY_H).pack(side="left")

        self.status = lbl(form, "", font=FONT_SMALL, fg=SUCCESS_FG, bg=CARD)
        self.status.grid(row=11, column=0, padx=20, sticky="w", pady=(0, 16))

        # ── Right preview ─────────────────────────────────────────────
        preview = card_frame(body)
        preview.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        lbl(preview, "Preview", font=FONT_H2, bg=CARD).pack(
            anchor="w", padx=20, pady=(20, 2))
        lbl(preview, "QR code appears after issuing.",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).pack(anchor="w", padx=20)
        divider(preview).pack(fill="x", pady=(12, 0))

        self.qr_lbl = lbl(preview, "No ticket yet.",
                           fg=TEXT3, bg=CARD, font=FONT_SMALL)
        self.qr_lbl.pack(pady=36)

        self.info_lbl = lbl(preview, "", fg=TEXT2, bg=CARD,
                            font=FONT_MONO, justify="left")
        self.info_lbl.pack(padx=20, anchor="w")

        divider(preview).pack(fill="x", pady=(16, 0))

        # VISIBLE blue Export PDF button
        btn(preview, "📄  Export PDF", self._export_pdf,
            bg=BTN_BLUE, fg=BTN_BLUE_FG,
            hover=BTN_BLUE_H).pack(padx=20, pady=16, anchor="w")

    def _setup_combo(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Dark.TCombobox",
                    fieldbackground=INPUT_BG, background=CARD2,
                    foreground=TEXT1, bordercolor=BORDER,
                    arrowcolor=TEXT2, selectbackground=INPUT_BG,
                    selectforeground=TEXT1)
        s.map("Dark.TCombobox",
              fieldbackground=[("readonly", INPUT_BG)],
              foreground=[("readonly", TEXT1)])

    def _load_events(self):
        events = db.get_events()
        self._events = {f"{e['title']} — {e['event_date']}": e for e in events}
        self.combo["values"] = list(self._events.keys())
        if self._events: self.combo.current(0)

    def _issue(self):
        name  = self.var_name.get().strip()
        email = self.var_email.get().strip()
        key   = self.combo.get()
        if not name or not email or not key:
            self.status.config(text="Fill in all fields.", fg=DANGER_FG); return
        if "@" not in email:
            self.status.config(text="Invalid email address.", fg=DANGER_FG); return
        event = self._events[key]
        tid, result = db.issue_ticket(event["id"], name, email)
        if tid is None:
            self.status.config(text=result, fg=DANGER_FG); return
        ticket = db.get_ticket(tid)
        self.last_ticket = ticket
        self.status.config(text=f"✔ Ticket #{tid} issued successfully!", fg=SUCCESS_FG)
        self.qr_photo = tg.generate_qr_photoimage(ticket["qr_token"], size=160)
        self.qr_lbl.config(image=self.qr_photo, text="")
        self.info_lbl.config(text=(
            f"ID      #{ticket['id']}\n"
            f"Name    {ticket['buyer_name']}\n"
            f"Email   {ticket['buyer_email']}\n"
            f"Event   {ticket['title']}\n"
            f"Date    {ticket['event_date']}  {ticket['event_time']}\n"
            f"Venue   {ticket['location']}\n"
            f"Status  {ticket['status'].upper()}"
        ))

    def _clear(self):
        self.var_name.set(""); self.var_email.set("")
        self.last_ticket = None
        self.qr_lbl.config(image="", text="No ticket yet.")
        self.info_lbl.config(text="")
        self.status.config(text="")

    def _export_pdf(self):
        if not self.last_ticket:
            messagebox.showinfo("No ticket", "Issue a ticket first."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"ticket_{self.last_ticket['id']}.pdf")
        if path:
            tg.generate_ticket_pdf(self.last_ticket, path)
            messagebox.showinfo("Saved", f"Ticket saved to:\n{path}")


# ══════════════════════════════════════════════════════════════════════════════
# Events Page
# ══════════════════════════════════════════════════════════════════════════════

class EventsPage(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        hdr = frm(self, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(24, 16))
        lbl(hdr, "Events", font=FONT_H1, fg=TEXT1, bg=BG).pack(side="left")

        # VISIBLE green Add event button
        btn(hdr, "+ Add event", self._add,
            bg=BTN_GREEN, fg=BTN_GREEN_FG,
            hover=BTN_GREEN_H).pack(side="right")

        card = card_frame(self)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        self._style_tree()
        cols = ("ID", "Title", "Date", "Time", "Location", "Capacity", "Sold")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                  height=16, style="Dark.Treeview")
        for col, w in zip(cols, [44, 210, 96, 72, 170, 84, 60]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                anchor="center" if col in ("ID","Capacity","Sold") else "w")
        sb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        actions = frm(self, bg=BG)
        actions.pack(fill="x", padx=28, pady=(6, 20))

        # VISIBLE red Delete button
        btn(actions, "🗑  Delete selected", self._delete,
            bg=BTN_RED, fg=BTN_RED_FG,
            hover=BTN_RED_H).pack(side="left")

        self._reload()

    def _style_tree(self):
        s = ttk.Style()
        s.configure("Dark.Treeview",
                    background=CARD, foreground=TEXT1,
                    fieldbackground=CARD, rowheight=32,
                    font=FONT_BODY, borderwidth=0)
        s.configure("Dark.Treeview.Heading",
                    background=CARD2, foreground=TEXT2,
                    font=FONT_LABEL, relief="flat")
        s.map("Dark.Treeview",
              background=[("selected", BTN_PRIMARY)],
              foreground=[("selected", "#FFFFFF")])

    def _reload(self):
        self.tree.delete(*self.tree.get_children())
        for ev in db.get_events():
            sold = db.tickets_sold(ev["id"])
            self.tree.insert("", "end", values=(
                ev["id"], ev["title"], ev["event_date"],
                ev["event_time"], ev["location"], ev["capacity"], sold))

    def _add(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add event")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        card = card_frame(dlg)
        card.pack(padx=24, pady=24)
        card.columnconfigure(0, weight=1)

        lbl(card, "New event", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 4))
        divider(card).grid(row=1, column=0, sticky="ew")

        labels = ["Title", "Date (YYYY-MM-DD)", "Time (HH:MM)", "Location", "Capacity"]
        keys   = ["title", "date", "time", "location", "capacity"]
        fields_map = {}
        for i, (lb, key) in enumerate(zip(labels, keys)):
            lbl(card, lb, font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
                row=2+i*2, column=0, sticky="w", padx=20, pady=(12, 3))
            var = tk.StringVar()
            inp(card, textvariable=var).grid(row=3+i*2, column=0, sticky="ew", padx=20)
            fields_map[key] = var

        err = lbl(card, "", font=FONT_SMALL, fg=DANGER_FG, bg=CARD)
        err.grid(row=14, column=0, padx=20, sticky="w", pady=(8, 0))
        divider(card).grid(row=15, column=0, sticky="ew", pady=(12, 0))

        btn_row = frm(card, bg=CARD)
        btn_row.grid(row=16, column=0, padx=20, pady=16, sticky="w")

        def save():
            import re
            from datetime import date as dt
            vals = {k: v.get().strip() for k, v in fields_map.items()}
            if not all(vals.values()):
                err.config(text="All fields required."); return
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", vals["date"]):
                err.config(text="Date must be YYYY-MM-DD  e.g. 2026-09-23"); return
            try:
                y, m, d = vals["date"].split("-")
                dt(int(y), int(m), int(d))
            except ValueError:
                err.config(text="Invalid date — check day/month order"); return
            if not re.match(r"^\d{2}:\d{2}$", vals["time"]):
                err.config(text="Time must be HH:MM  e.g. 20:00"); return
            h, mn = int(vals["time"][:2]), int(vals["time"][3:])
            if not (0 <= h <= 23 and 0 <= mn <= 59):
                err.config(text="Invalid time — hours 00-23, minutes 00-59"); return
            try:
                cap = int(vals["capacity"])
                if cap <= 0: raise ValueError
            except ValueError:
                err.config(text="Capacity must be a positive number."); return
            db.add_event(vals["title"], vals["date"], vals["time"],
                         vals["location"], cap)
            dlg.destroy(); self._reload()

        btn(btn_row, "Save event", save,
            bg=BTN_GREEN, fg=BTN_GREEN_FG,
            hover=BTN_GREEN_H).pack(side="left", padx=(0, 10))
        btn(btn_row, "Cancel", dlg.destroy,
            bg=BTN_GREY, fg=BTN_GREY_FG,
            hover=BTN_GREY_H).pack(side="left")

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        row = self.tree.item(sel[0])["values"]
        if messagebox.askyesno("Delete", f"Delete '{row[1]}'?\nAll tickets will be removed."):
            db.delete_event(row[0]); self._reload()


# ══════════════════════════════════════════════════════════════════════════════
# All Tickets Page
# ══════════════════════════════════════════════════════════════════════════════

class TicketsPage(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        hdr = frm(self, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        lbl(hdr, "All tickets", font=FONT_H1, fg=TEXT1, bg=BG).pack(side="left")

        search_row = frm(self, bg=BG)
        search_row.pack(fill="x", padx=28, pady=(0, 12))
        self.var_search = tk.StringVar()
        inp(search_row, textvariable=self.var_search, width=34).pack(side="left", padx=(0, 8))

        btn(search_row, "🔍 Search", self._reload,
            bg=BTN_PRIMARY, fg=BTN_PRIMARY_FG,
            hover=BTN_PRIMARY_H).pack(side="left", padx=(0, 8))
        btn(search_row, "Show all",
            lambda: (self.var_search.set(""), self._reload()),
            bg=BTN_GREY, fg=BTN_GREY_FG,
            hover=BTN_GREY_H).pack(side="left")

        card = card_frame(self)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        cols = ("ID", "Event", "Attendee", "Email", "Issued", "Status")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                  height=15, style="Dark.Treeview")
        for col, w in zip(cols, [44, 190, 160, 190, 140, 88]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                anchor="center" if col in ("ID","Status") else "w")
        self.tree.tag_configure("cancelled", foreground=TEXT3)

        sb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        actions = frm(self, bg=BG)
        actions.pack(fill="x", padx=28, pady=(6, 20))

        btn(actions, "✗  Cancel ticket", self._cancel,
            bg=BTN_RED, fg=BTN_RED_FG,
            hover=BTN_RED_H).pack(side="left", padx=(0, 8))
        btn(actions, "✓  Reactivate", self._reactivate,
            bg=BTN_GREEN, fg=BTN_GREEN_FG,
            hover=BTN_GREEN_H).pack(side="left", padx=(0, 8))
        btn(actions, "📄  Export PDF", self._export_pdf,
            bg=BTN_BLUE, fg=BTN_BLUE_FG,
            hover=BTN_BLUE_H).pack(side="left")

        self._reload()

    def _reload(self):
        self.tree.delete(*self.tree.get_children())
        search = self.var_search.get().strip() or None
        for t in db.get_all_tickets(search):
            tag = "cancelled" if t["status"] == "cancelled" else ""
            self.tree.insert("", "end", iid=str(t["id"]), values=(
                t["id"], t["title"], t["buyer_name"],
                t["buyer_email"], str(t["issued_at"])[:16],
                t["status"].upper()), tags=(tag,))

    def _sel(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select a ticket", "Click a ticket row first.")
            return None
        return int(sel[0])

    def _cancel(self):
        tid = self._sel()
        if tid and messagebox.askyesno("Cancel", f"Cancel ticket #{tid}?"):
            db.cancel_ticket(tid); self._reload()

    def _reactivate(self):
        tid = self._sel()
        if tid: db.reactivate_ticket(tid); self._reload()

    def _export_pdf(self):
        tid = self._sel()
        if not tid: return
        ticket = db.get_ticket(tid)
        if not ticket: return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"ticket_{tid}.pdf")
        if path:
            tg.generate_ticket_pdf(ticket, path)
            messagebox.showinfo("Saved", f"Saved to:\n{path}")


# ══════════════════════════════════════════════════════════════════════════════
# Change Password Page
# ══════════════════════════════════════════════════════════════════════════════

class PasswordPage(tk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self.user = user
        self._build()

    def _build(self):
        outer = frm(self, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = card_frame(outer)
        card.pack()
        card.columnconfigure(0, weight=1)

        lbl(card, "Change password", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=24, pady=(24, 2))
        lbl(card, f"Signed in as  {self.user['username']}",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky="w", padx=24)
        divider(card).grid(row=2, column=0, sticky="ew", pady=(14, 0))

        self.var_cur  = tk.StringVar()
        self.var_new  = tk.StringVar()
        self.var_conf = tk.StringVar()
        for i, (lb, var) in enumerate([
            ("Current password", self.var_cur),
            ("New password",     self.var_new),
            ("Confirm new",      self.var_conf),
        ]):
            lbl(card, lb, font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
                row=3+i*2, column=0, sticky="w", padx=24, pady=(14, 3))
            inp(card, textvariable=var, show="•", width=32).grid(
                row=4+i*2, column=0, sticky="ew", padx=24)

        self.msg = lbl(card, "", font=FONT_SMALL, fg=SUCCESS_FG, bg=CARD)
        self.msg.grid(row=10, column=0, padx=24, sticky="w", pady=(10, 0))
        divider(card).grid(row=11, column=0, sticky="ew", pady=(14, 0))

        btn(card, "Update password", self._change,
            bg=BTN_PRIMARY, fg=BTN_PRIMARY_FG,
            hover=BTN_PRIMARY_H).grid(
            row=12, column=0, padx=24, pady=18, sticky="w")

    def _change(self):
        cur, new, conf = self.var_cur.get(), self.var_new.get(), self.var_conf.get()
        if not cur or not new or not conf:
            self.msg.config(text="All fields are required.", fg=DANGER_FG); return
        if len(new) < 6:
            self.msg.config(text="Minimum 6 characters.", fg=DANGER_FG); return
        if new != conf:
            self.msg.config(text="Passwords don't match.", fg=DANGER_FG); return
        if not db.verify_user(self.user["username"], cur):
            self.msg.config(text="Current password is incorrect.", fg=DANGER_FG); return
        db.change_password(self.user["username"], new)
        self.msg.config(text="✔ Password updated successfully!", fg=SUCCESS_FG)
        self.var_cur.set(""); self.var_new.set(""); self.var_conf.set("")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().mainloop()