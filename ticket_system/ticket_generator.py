"""
ticket_generator.py  –  QR code + PDF ticket builder
"""

import qrcode
import io
from fpdf import FPDF
from PIL import Image


def generate_qr_image(data: str, size: int = 200) -> Image.Image:
    """Return a PIL Image of the QR code."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    img = img.resize((size, size), Image.LANCZOS)
    return img.convert("RGB")


def generate_ticket_pdf(ticket: dict, output_path: str) -> str:
    """Build a styled PDF ticket and save to output_path. Returns the path."""
    pdf = FPDF(orientation="L", unit="mm", format=(100, 200))
    pdf.add_page()
    pdf.set_auto_page_break(False)

    # Background
    pdf.set_fill_color(26, 26, 46)
    pdf.rect(0, 0, 200, 100, "F")
    pdf.set_fill_color(22, 33, 62)
    pdf.rect(0, 60, 200, 40, "F")

    # Left accent bar
    pdf.set_fill_color(233, 69, 96)
    pdf.rect(0, 0, 6, 100, "F")

    # Header label
    pdf.set_text_color(233, 69, 96)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_xy(10, 6)
    pdf.cell(0, 5, "EVENT TICKET", ln=True)

    # Event title
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(10, 12)
    pdf.cell(0, 8, str(ticket.get("title", ""))[:36], ln=True)

    # Divider
    pdf.set_draw_color(233, 69, 96)
    pdf.set_line_width(0.4)
    pdf.line(10, 24, 145, 24)

    # Field helper
    def field(label, value, x, y):
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(180, 180, 200)
        pdf.set_xy(x, y)
        pdf.cell(0, 4, label.upper())
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x, y + 4)
        pdf.cell(0, 5, str(value)[:30])

    field("Attendee",  ticket.get("buyer_name", ""),  10, 26)
    field("Email",     ticket.get("buyer_email", ""), 10, 37)
    field("Date",      str(ticket.get("event_date", "")), 10, 48)
    field("Time",      str(ticket.get("event_time", "")), 70, 48)
    field("Venue",     ticket.get("location", ""),    10, 59)
    field("Ticket ID", f"#{ticket.get('id', '')}",    10, 70)
    field("Status",    ticket.get("status", "active").upper(), 70, 70)

    # Tear line
    pdf.set_draw_color(100, 100, 140)
    pdf.set_line_width(0.2)
    pdf.set_dash_pattern(dash=2, gap=2)
    pdf.line(148, 2, 148, 98)
    pdf.set_dash_pattern()

    # QR label
    pdf.set_text_color(180, 180, 200)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_xy(150, 6)
    pdf.cell(0, 4, "SCAN TO VERIFY")

    # QR image
    qr_img = generate_qr_image(ticket.get("qr_token", "INVALID"), size=200)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    pdf.image(buf, x=152, y=12, w=40, h=40)

    # Token snippet
    pdf.set_text_color(100, 100, 140)
    pdf.set_font("Helvetica", "", 5)
    pdf.set_xy(150, 54)
    pdf.cell(0, 4, (ticket.get("qr_token", "")[:20] + "…"))

    pdf.output(output_path)
    return output_path


def generate_qr_photoimage(qr_token: str, size: int = 180):
    """Return a tkinter-compatible PhotoImage for live preview."""
    import tkinter as tk
    img = generate_qr_image(qr_token, size=size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return tk.PhotoImage(data=buf.getvalue())