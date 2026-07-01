"""
app.py  –  Ticket Generating System
Tkinter GUI  ·  MySQL backend  ·  QR + PDF export
Modern redesign: soft neutrals, visible buttons, clean typography
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import database as db
import ticket_generator as tg

# ── Palette ────────────────────────────────────────────────────────────────
BG        = "#F5F4F0"   # warm off-white page
SIDEBAR   = "#1E1E2E"   # deep navy sidebar
CARD      = "#FFFFFF"   # pure white cards
CARD2     = "#9397E3"   # soft lavender card accent

ACCENT    = "#5B4EE8"   # purple primary
ACCENT_H  = "#4A3DD6"   # purple hover
ACCENT_FG = "#FFFFFF"   # text on accent

BTN_SEC   = "#FFFFFF"   # secondary button bg
BTN_SEC_B = "#C5C1E0"   # secondary button border
BTN_SEC_H = "#EAE8F8"   # secondary button hover

DANGER    = "#E05252"   # red
SUCCESS   = "#2E9E6B"   # green
WARNING   = "#D97706"   # amber

TEXT1     = "#1A1A2E"   # primary text
TEXT2     = "#5C5C7A"   # secondary text
TEXT3     = "#9090A8"   # muted text
BORDER    = "#E2E0F0"   # hairline border
SIDEBAR_FG = "#C8C6E0"  # sidebar text
SIDEBAR_A  = "#FFFFFF"  # sidebar active text
SIDEBAR_AB = "#3A2F7A"  # sidebar active bg

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

def entry(parent, textvariable=None, show=None, width=30):
    e = tk.Entry(
        parent, textvariable=textvariable, show=show, width=width,
        bg=CARD, fg=TEXT1, insertbackground=ACCENT,
        relief="solid", bd=1, font=FONT_BODY,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
    )
    return e

def primary_btn(parent, text, command, width=None):
    b = tk.Button(
        parent, text=text, command=command,
        bg=ACCENT, fg=ACCENT_FG,
        activebackground=ACCENT_H, activeforeground=ACCENT_FG,
        relief="flat", font=FONT_BODY, cursor="hand2",
        bd=0, padx=16, pady=8,
    )
    if width: b.config(width=width)
    return b

def secondary_btn(parent, text, command, width=None):
    b = tk.Button(
        parent, text=text, command=command,
        bg=BTN_SEC, fg=TEXT1,
        activebackground=BTN_SEC_H, activeforeground=TEXT1,
        relief="solid", bd=1, font=FONT_BODY, cursor="hand2",
        highlightbackground=BTN_SEC_B,
        padx=14, pady=7,
    )
    if width: b.config(width=width)
    return b

def danger_btn(parent, text, command):
    return tk.Button(
        parent, text=text, command=command,
        bg="#FEF2F2", fg=DANGER,
        activebackground="#FEE2E2", activeforeground=DANGER,
        relief="solid", bd=1, font=FONT_BODY, cursor="hand2",
        highlightbackground="#FECACA",
        padx=14, pady=7,
    )

def success_btn(parent, text, command):
    return tk.Button(
        parent, text=text, command=command,
        bg="#F0FDF4", fg=SUCCESS,
        activebackground="#DCFCE7", activeforeground=SUCCESS,
        relief="solid", bd=1, font=FONT_BODY, cursor="hand2",
        highlightbackground="#BBF7D0",
        padx=14, pady=7,
    )

def field_row(parent, label_text, row, textvariable=None, show=None):
    lbl(parent, label_text, font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
        row=row*2, column=0, sticky="w", padx=20, pady=(14, 2))
    e = entry(parent, textvariable=textvariable, show=show)
    e.grid(row=row*2+1, column=0, sticky="ew", padx=20, pady=(0, 2))
    return e

def section_card(parent, **kw):
    f = tk.Frame(parent, bg=CARD, relief="solid", bd=1,
                 highlightbackground=BORDER, highlightthickness=1, **kw)
    return f

def badge(parent, text, color=ACCENT, bg_color=None):
    if bg_color is None:
        bg_color = "#EDE9FF"
    return tk.Label(parent, text=text, font=FONT_LABEL,
                    fg=color, bg=bg_color,
                    padx=8, pady=3, relief="flat")


# ══════════════════════════════════════════════════════════════════════════════
# Login Window
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
        # Top brand strip
        top = frm(self, bg=SIDEBAR)
        top.pack(fill="x")
        tk.Label(top, text="  Ticket System", font=("Helvetica Neue", 13, "bold"),
                 fg=SIDEBAR_A, bg=SIDEBAR, pady=16).pack(side="left", padx=8)

        # Card
        card = section_card(self)
        card.pack(fill="both", expand=True, padx=32, pady=28)
        card.columnconfigure(0, weight=1)

        lbl(card, "Welcome back", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 2))
        lbl(card, "Sign in to manage your events and tickets.",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        # Divider
        tk.Frame(card, bg=BORDER, height=1).grid(
            row=2, column=0, sticky="ew", padx=0)

        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()
        field_row(card, "Username", 1, self.var_user)
        field_row(card, "Password", 2, self.var_pass, show="•")

        self.err = lbl(card, "", font=FONT_SMALL, fg=DANGER, bg=CARD)
        self.err.grid(row=7, column=0, padx=20, pady=(6, 0), sticky="w")

        primary_btn(card, "Sign in", self._login, width=28).grid(
            row=8, column=0, padx=20, pady=(14, 20), sticky="w")

        self.bind("<Return>", lambda e: self._login())

    def _login(self):
        user = self.var_user.get().strip()
        pwd  = self.var_pass.get()
        if not user or not pwd:
            self.err.config(text="Please fill in both fields.")
            return
        try:
            result = db.verify_user(user, pwd)
        except Exception as ex:
            self.err.config(text=f"Database error: {ex}")
            return
        if result:
            self.destroy()
            self.on_success(result)
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
                f"Could not connect to MySQL.\n\n{ex}\n\n"
                "Edit DB_CONFIG in database.py and try again.")
            self.destroy()
            return

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

        # Brand
        brand = frm(sb, bg="#16162A")
        brand.pack(fill="x")
        tk.Label(brand, text="Ticket System", font=("Helvetica Neue", 13, "bold"),
                 fg=SIDEBAR_A, bg="#16162A", pady=18).pack(padx=20, anchor="w")

        # User chip
        user_row = frm(sb, bg=SIDEBAR)
        user_row.pack(fill="x", padx=12, pady=(8, 12))
        initials = self.current_user["username"][:2].upper()
        tk.Label(user_row, text=initials, font=("Helvetica Neue", 10, "bold"),
                 fg=ACCENT_FG, bg=ACCENT, width=3, pady=4,
                 relief="flat").pack(side="left", padx=(0, 8))
        tk.Label(user_row, text=self.current_user["username"],
                 font=FONT_SMALL, fg=SIDEBAR_FG, bg=SIDEBAR).pack(side="left")

        tk.Frame(sb, bg="#2E2E45", height=1).pack(fill="x", padx=16, pady=4)

        # Nav items
        pages = [
            ("Issue ticket",     "issue",    "🎟"),
            ("Events",           "events",   "📅"),
            ("All tickets",      "tickets",  "📋"),
            ("Change password",  "password", "🔒"),
        ]
        self.nav_btns = {}
        for label, key, icon in pages:
            btn = tk.Button(
                sb, text=f"  {icon}  {label}", anchor="w",
                font=FONT_BODY, bg=SIDEBAR, fg=SIDEBAR_FG,
                activebackground=SIDEBAR_AB, activeforeground=SIDEBAR_A,
                relief="flat", bd=0, padx=12, pady=10,
                cursor="hand2",
                command=lambda k=key: self._show(k),
            )
            btn.pack(fill="x", padx=8)
            self.nav_btns[key] = btn

        # Spacer + logout
        frm(sb, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(sb, bg="#2E2E45", height=1).pack(fill="x", padx=16, pady=4)
        tk.Button(
            sb, text="  ⏻  Sign out", anchor="w",
            font=FONT_SMALL, bg=SIDEBAR, fg=TEXT3,
            activebackground="#2E2E45", activeforeground=SIDEBAR_FG,
            relief="flat", bd=0, padx=20, pady=12,
            cursor="hand2", command=self._logout,
        ).pack(fill="x")

    def _show(self, key):
        for w in self.content.winfo_children():
            w.destroy()
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.config(bg=SIDEBAR_AB, fg=SIDEBAR_A)
            else:
                btn.config(bg=SIDEBAR, fg=SIDEBAR_FG)
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
        # Page header
        hdr = frm(self, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(24, 16))
        lbl(hdr, "Issue ticket", font=FONT_H1, bg=BG).pack(side="left")

        body = frm(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Left: form card ───────────────────────────────────────────
        form = section_card(body)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        form.columnconfigure(0, weight=1)

        lbl(form, "Attendee details", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 0))
        lbl(form, "Enter attendee info and select an event.",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky="w", padx=20, pady=(2, 0))

        tk.Frame(form, bg=BORDER, height=1).grid(
            row=2, column=0, sticky="ew", pady=(12, 0))

        self.var_name  = tk.StringVar()
        self.var_email = tk.StringVar()
        field_row(form, "Full name", 1, self.var_name)
        field_row(form, "Email address", 2, self.var_email)

        lbl(form, "Event", font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
            row=7, column=0, sticky="w", padx=20, pady=(14, 2))

        self._style_combo()
        self.combo = ttk.Combobox(form, state="readonly",
                                  font=FONT_BODY, style="Modern.TCombobox")
        self.combo.grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 4))
        self._load_events()

        tk.Frame(form, bg=BORDER, height=1).grid(
            row=9, column=0, sticky="ew", pady=(16, 0))

        btn_row = frm(form, bg=CARD)
        btn_row.grid(row=10, column=0, padx=20, pady=20, sticky="w")
        primary_btn(btn_row, "Issue ticket", self._issue).pack(side="left", padx=(0, 10))
        secondary_btn(btn_row, "Clear", self._clear).pack(side="left")

        self.status = lbl(form, "", font=FONT_SMALL, fg=SUCCESS, bg=CARD)
        self.status.grid(row=11, column=0, padx=20, sticky="w", pady=(0, 16))

        # ── Right: preview card ───────────────────────────────────────
        preview = section_card(body)
        preview.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        lbl(preview, "Preview", font=FONT_H2, bg=CARD).pack(
            anchor="w", padx=20, pady=(20, 4))
        lbl(preview, "QR code and ticket info appear here.",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).pack(anchor="w", padx=20)

        tk.Frame(preview, bg=BORDER, height=1).pack(fill="x", pady=(12, 0))

        self.qr_lbl = lbl(preview, "No ticket issued yet.",
                           fg=TEXT3, bg=CARD, font=FONT_SMALL)
        self.qr_lbl.pack(pady=32)

        self.info_lbl = lbl(preview, "", fg=TEXT2, bg=CARD,
                            font=FONT_MONO, justify="left")
        self.info_lbl.pack(padx=20, anchor="w")

        tk.Frame(preview, bg=BORDER, height=1).pack(fill="x", pady=(16, 0))

        self.btn_pdf = secondary_btn(preview, "Export PDF", self._export_pdf)
        self.btn_pdf.pack(padx=20, pady=16, anchor="w")
        self.btn_pdf.config(state="disabled", fg=TEXT3)

    def _style_combo(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Modern.TCombobox",
                    fieldbackground=CARD, background=CARD,
                    foreground=TEXT1, bordercolor=BORDER,
                    arrowcolor=TEXT2, relief="solid")

    def _load_events(self):
        events = db.get_events()
        self._events = {f"{e['title']} — {e['event_date']}": e for e in events}
        self.combo["values"] = list(self._events.keys())
        if self._events:
            self.combo.current(0)

    def _issue(self):
        name  = self.var_name.get().strip()
        email = self.var_email.get().strip()
        key   = self.combo.get()
        if not name or not email or not key:
            self.status.config(text="Fill in all fields.", fg=DANGER); return
        if "@" not in email:
            self.status.config(text="Invalid email address.", fg=DANGER); return

        event = self._events[key]
        tid, result = db.issue_ticket(event["id"], name, email)
        if tid is None:
            self.status.config(text=result, fg=DANGER); return

        ticket = db.get_ticket(tid)
        self.last_ticket = ticket
        self.status.config(text=f"Ticket #{tid} issued.", fg=SUCCESS)

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
        self.btn_pdf.config(state="normal", fg=TEXT1)

    def _clear(self):
        self.var_name.set(""); self.var_email.set("")
        self.last_ticket = None
        self.qr_lbl.config(image="", text="No ticket issued yet.")
        self.info_lbl.config(text="")
        self.status.config(text="")
        self.btn_pdf.config(state="disabled", fg=TEXT3)

    def _export_pdf(self):
        if not self.last_ticket: return
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
        lbl(hdr, "Events", font=FONT_H1, bg=BG).pack(side="left")
        primary_btn(hdr, "+ Add event", self._add).pack(side="right")

        card = section_card(self)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 28))

        self._style_tree()
        cols = ("ID", "Title", "Date", "Time", "Location", "Capacity", "Sold")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                  height=16, style="Modern.Treeview")
        for col, w in zip(cols, [44, 210, 96, 72, 170, 84, 60]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="center" if col in ("ID","Capacity","Sold") else "w")

        sb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        sb.pack(side="right", fill="y")

        actions = frm(self, bg=BG)
        actions.pack(fill="x", padx=28, pady=(0, 16))
        danger_btn(actions, "Delete selected", self._delete).pack(side="left")

        self._reload()

    def _style_tree(self):
        s = ttk.Style()
        s.configure("Modern.Treeview",
                    background=CARD, foreground=TEXT1,
                    fieldbackground=CARD, rowheight=32,
                    font=FONT_BODY, borderwidth=0)
        s.configure("Modern.Treeview.Heading",
                    background=BG, foreground=TEXT2,
                    font=FONT_LABEL, relief="flat", borderwidth=0)
        s.map("Modern.Treeview", background=[("selected", "#EDE9FF")],
              foreground=[("selected", TEXT1)])

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
        dlg.columnconfigure(0, weight=1)

        card = section_card(dlg)
        card.pack(padx=24, pady=24, fill="both")
        card.columnconfigure(0, weight=1)

        lbl(card, "New event", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 4))
        tk.Frame(card, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew")

        labels = ["Title", "Date (YYYY-MM-DD)", "Time (HH:MM)", "Location", "Capacity"]
        keys   = ["title", "date", "time", "location", "capacity"]
        fields = {}
        for i, (lb, key) in enumerate(zip(labels, keys)):
            lbl(card, lb, font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
                row=2+i*2, column=0, sticky="w", padx=20, pady=(12, 2))
            var = tk.StringVar()
            entry(card, textvariable=var).grid(
                row=3+i*2, column=0, sticky="ew", padx=20)
            fields[key] = var

        err = lbl(card, "", font=FONT_SMALL, fg=DANGER, bg=CARD)
        err.grid(row=14, column=0, padx=20, sticky="w")

        tk.Frame(card, bg=BORDER, height=1).grid(row=15, column=0, sticky="ew", pady=(12,0))
        btn_row = frm(card, bg=CARD)
        btn_row.grid(row=16, column=0, padx=20, pady=16, sticky="w")

        def save():
            vals = {k: v.get().strip() for k, v in fields.items()}
            if not all(vals.values()):
                err.config(text="All fields required."); return
            try:
                cap = int(vals["capacity"])
                if cap <= 0: raise ValueError
            except ValueError:
                err.config(text="Capacity must be a positive number."); return
            db.add_event(vals["title"], vals["date"], vals["time"],
                         vals["location"], cap)
            dlg.destroy()
            self._reload()

        primary_btn(btn_row, "Save event", save).pack(side="left", padx=(0, 10))
        secondary_btn(btn_row, "Cancel", dlg.destroy).pack(side="left")

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        row = self.tree.item(sel[0])["values"]
        if messagebox.askyesno("Delete event",
                f"Delete '{row[1]}'?\nAll its tickets will also be removed."):
            db.delete_event(row[0])
            self._reload()


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
        lbl(hdr, "All tickets", font=FONT_H1, bg=BG).pack(side="left")

        # Search bar
        search_row = frm(self, bg=BG)
        search_row.pack(fill="x", padx=28, pady=(0, 12))
        self.var_search = tk.StringVar()
        entry(search_row, textvariable=self.var_search, width=34).pack(side="left", padx=(0,8))
        primary_btn(search_row, "Search", self._reload).pack(side="left", padx=(0, 8))
        secondary_btn(search_row, "Show all",
                      lambda: (self.var_search.set(""), self._reload())).pack(side="left")

        card = section_card(self)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        cols = ("ID", "Event", "Attendee", "Email", "Issued", "Status")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                  height=15, style="Modern.Treeview")
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
        actions.pack(fill="x", padx=28, pady=(0, 20))
        danger_btn(actions, "Cancel ticket",  self._cancel).pack(side="left", padx=(0, 8))
        success_btn(actions, "Reactivate",    self._reactivate).pack(side="left", padx=(0, 8))
        secondary_btn(actions, "Export PDF",  self._export_pdf).pack(side="left")

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
        if tid and messagebox.askyesno("Cancel ticket", f"Cancel ticket #{tid}?"):
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

        card = section_card(outer)
        card.pack(ipadx=0, ipady=0)
        card.columnconfigure(0, weight=1)

        lbl(card, "Change password", font=FONT_H2, bg=CARD).grid(
            row=0, column=0, sticky="w", padx=24, pady=(24, 2))
        lbl(card, f"Signed in as  {self.user['username']}",
            font=FONT_SMALL, fg=TEXT2, bg=CARD).grid(
            row=1, column=0, sticky="w", padx=24)

        tk.Frame(card, bg=BORDER, height=1).grid(
            row=2, column=0, sticky="ew", pady=(16, 0))

        self.var_cur  = tk.StringVar()
        self.var_new  = tk.StringVar()
        self.var_conf = tk.StringVar()

        for i, (lb, var) in enumerate([
            ("Current password", self.var_cur),
            ("New password",     self.var_new),
            ("Confirm new",      self.var_conf),
        ]):
            lbl(card, lb, font=FONT_LABEL, fg=TEXT2, bg=CARD).grid(
                row=3+i*2, column=0, sticky="w", padx=24, pady=(14, 2))
            entry(card, textvariable=var, show="•", width=32).grid(
                row=4+i*2, column=0, sticky="ew", padx=24)

        self.msg = lbl(card, "", font=FONT_SMALL, fg=SUCCESS, bg=CARD)
        self.msg.grid(row=10, column=0, padx=24, sticky="w", pady=(10, 0))

        tk.Frame(card, bg=BORDER, height=1).grid(
            row=11, column=0, sticky="ew", pady=(16, 0))
        primary_btn(card, "Update password", self._change).grid(
            row=12, column=0, padx=24, pady=20, sticky="w")

    def _change(self):
        cur, new, conf = self.var_cur.get(), self.var_new.get(), self.var_conf.get()
        if not cur or not new or not conf:
            self.msg.config(text="All fields are required.", fg=DANGER); return
        if len(new) < 6:
            self.msg.config(text="New password must be at least 6 characters.", fg=DANGER); return
        if new != conf:
            self.msg.config(text="Passwords don't match.", fg=DANGER); return
        if not db.verify_user(self.user["username"], cur):
            self.msg.config(text="Current password is incorrect.", fg=DANGER); return
        db.change_password(self.user["username"], new)
        self.msg.config(text="Password updated.", fg=SUCCESS)
        self.var_cur.set(""); self.var_new.set(""); self.var_conf.set("")


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().mainloop()