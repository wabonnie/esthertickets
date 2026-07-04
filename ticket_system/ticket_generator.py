"""
ticket_generator.py -- QR code and PDF ticket generation.

Defines the TicketGenerator class, which builds the QR code image shown
in the GUI preview and the printable PDF ticket, both from a ticket
dict as returned by database.Database.get_ticket().
"""

from __future__ import annotations

from typing import Dict, Any

import io

import qrcode
from fpdf import FPDF
from PIL import Image


class TicketGenerator:
    """Generates QR codes and PDF tickets for issued tickets.

    This class has no internal state: every method is a pure function
    of its arguments. It is implemented as a class (rather than plain
    module functions) to group the related QR/PDF generation behaviour
    behind one object, consistent with the rest of the application.
    """

    @staticmethod
    def generate_qr_image(data: str, size: int = 200) -> Image.Image:
        """Build a QR code as a PIL Image.

        Args:
            data: the text to encode in the QR code.
            size: width and height, in pixels, of the returned square
                image.

        Returns:
            A PIL Image in RGB mode containing the QR code.
        """
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

    def generate_ticket_pdf(self, ticket: Dict[str, Any], output_path: str) -> str:
        """Render a styled, printable PDF for a single ticket.

        Args:
            ticket: a ticket dict as returned by
                database.Database.get_ticket() (must include id,
                title, buyer_name, buyer_email, event_date,
                event_time, location, status and qr_token).
            output_path: file path (including ".pdf" extension) to
                save the generated PDF to.

        Returns:
            The same output_path that was passed in, for convenience.
        """
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

        def field(label: str, value: Any, x: float, y: float) -> None:
            """Draw one small label + value pair at the given position."""
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

        # QR image, built from an in-memory buffer (no temp file on disk)
        qr_img = self.generate_qr_image(ticket.get("qr_token", "INVALID"), size=200)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        buf.seek(0)
        pdf.image(buf, x=152, y=12, w=40, h=40)

        pdf.output(output_path)
        return output_path

    def generate_qr_photoimage(self, qr_token: str, size: int = 180):
        """Build a tkinter-compatible PhotoImage of a ticket's QR code.

        Used for the live QR preview inside the IssuePage GUI.

        Args:
            qr_token: the ticket's unique QR token string.
            size: width and height, in pixels, of the preview image.

        Returns:
            A tkinter.PhotoImage ready to assign to a Label's "image"
            option.
        """
        import tkinter as tk
        img = self.generate_qr_image(qr_token, size=size)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return tk.PhotoImage(data=buf.getvalue())