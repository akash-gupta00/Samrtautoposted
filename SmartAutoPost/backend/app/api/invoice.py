from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.organization import Organization
from app.models.user import User
from app.schemas.invoice import InvoiceResponse
from app.services.invoice_pdf_service import InvoicePDFService
from app.services.invoice_service import InvoiceService


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)

invoice_service = InvoiceService()
invoice_pdf_service = InvoicePDFService()


@router.post(
    "/from-payment/{payment_id}",
    response_model=InvoiceResponse,
)
def create_invoice_from_payment(
    payment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return invoice_service.create_invoice_from_payment(
        db=db,
        payment_id=payment_id,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/",
    response_model=list[InvoiceResponse],
)
def list_invoices(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return invoice_service.list_invoices(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get("/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = invoice_service.get_invoice(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
    )

    organization = (
        db.query(Organization)
        .filter(
            Organization.id == invoice.organization_id
        )
        .first()
    )

    if not organization:
        return {
            "detail": "Organization not found"
        }

    pdf_buffer = invoice_pdf_service.generate_invoice_pdf(
        invoice=invoice,
        organization=organization,
    )

    filename = f"{invoice.invoice_number}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
        },
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return invoice_service.get_invoice(
        db=db,
        invoice_id=invoice_id,
        current_user=current_user,
    )