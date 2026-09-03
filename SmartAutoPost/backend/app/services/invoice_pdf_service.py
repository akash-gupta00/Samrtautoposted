from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class InvoicePDFService:

    def generate_invoice_pdf(
        self,
        invoice,
        organization,
    ) -> BytesIO:

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=22,
            spaceAfter=20,
        )

        right_style = ParagraphStyle(
            "RightText",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
        )

        normal_style = styles["Normal"]

        elements = []

        elements.append(
            Paragraph(
                "SmartAutoPost Invoice",
                title_style,
            )
        )

        invoice_info = [
            [
                Paragraph(
                    f"<b>Invoice Number:</b> {invoice.invoice_number}",
                    normal_style,
                ),
                Paragraph(
                    f"<b>Status:</b> {invoice.status.upper()}",
                    right_style,
                ),
            ],
            [
                Paragraph(
                    f"<b>Issued At:</b> {invoice.issued_at.strftime('%d-%m-%Y %I:%M %p')}",
                    normal_style,
                ),
                "",
            ],
        ]

        invoice_info_table = Table(
            invoice_info,
            colWidths=[85 * mm, 85 * mm],
        )

        invoice_info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(invoice_info_table)
        elements.append(Spacer(1, 15))

        organization_name = getattr(
            organization,
            "name",
            "Organization",
        )

        organization_details = [
            ["Billed To", organization_name],
            ["Organization ID", str(invoice.organization_id)],
            ["Plan", invoice.plan_name],
        ]

        organization_table = Table(
            organization_details,
            colWidths=[50 * mm, 120 * mm],
        )

        organization_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(organization_table)
        elements.append(Spacer(1, 20))

        amount_data = [
            [
                "Description",
                "Amount",
            ],
            [
                f"{invoice.plan_name} Plan",
                f"{invoice.currency} {invoice.amount}",
            ],
            [
                "Tax",
                f"{invoice.currency} {invoice.tax_amount}",
            ],
            [
                "Total",
                f"{invoice.currency} {invoice.total_amount}",
            ],
        ]

        amount_table = Table(
            amount_data,
            colWidths=[110 * mm, 60 * mm],
        )

        amount_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF2FF")),
                    ("PADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        elements.append(amount_table)
        elements.append(Spacer(1, 30))

        elements.append(
            Paragraph(
                "Thank you for using SmartAutoPost.",
                ParagraphStyle(
                    "Footer",
                    parent=normal_style,
                    alignment=TA_CENTER,
                    textColor=colors.grey,
                ),
            )
        )

        document.build(elements)

        buffer.seek(0)

        return buffer