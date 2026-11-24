"""
backend/app/crypto/pdf.py

Generates a clean, professional A4 PDF certificate for SAKSHI verified credentials.
Design Tokens:
- Background: Paper #F6F3EC (RGB: 246, 243, 236)
- Text / Ink: #0A0A0A (RGB: 10, 10, 10)
- Brand Accent: Orange #FF5500 (RGB: 255, 85, 0)
- Muted / Border: #888888 / #D4CEBF
"""
import io
from typing import Any, Dict, Optional
from fpdf import FPDF
import qrcode

TIER_NAMES: Dict[int, str] = {
    0: "Tier 0 (Needs Retry)",
    1: "Tier 1 (Demonstrated)",
    2: "Tier 2 (Witnessed)",
    3: "Tier 3 (Trusted)",
}


def _clean(text: str) -> str:
    """Replaces unicode characters outside latin-1 with ASCII equivalents."""
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class SakshiCertificate(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)

    def cell(self, *args, **kwargs):
        if len(args) >= 3:
            args = list(args)
            args[2] = _clean(str(args[2]))
        elif "text" in kwargs:
            kwargs["text"] = _clean(str(kwargs["text"]))
        elif "txt" in kwargs:
            kwargs["txt"] = _clean(str(kwargs["txt"]))
        return super().cell(*args, **kwargs)


def generate_pdf(
    payload: Dict[str, Any],
    verify_url: Optional[str] = None,
) -> bytes:
    """
    Renders an A4 certificate PDF from credential payload data and returns raw bytes.
    Uses standard core fonts (Helvetica, Times) for zero-dependency reliability on all platforms.
    """
    pdf = SakshiCertificate()
    pdf.add_page()

    # 1. Background fill: #F6F3EC
    pdf.set_fill_color(246, 243, 236)
    pdf.rect(0, 0, 210, 297, "F")

    # 2. Outer decorative borders
    # Outer orange border
    pdf.set_draw_color(255, 85, 0)
    pdf.set_line_width(1.2)
    pdf.rect(10, 10, 190, 277)

    # Inner subtle border
    pdf.set_draw_color(212, 206, 191)
    pdf.set_line_width(0.5)
    pdf.rect(13, 13, 184, 271)

    # Corner decorative marks
    pdf.set_draw_color(255, 85, 0)
    pdf.set_line_width(0.8)
    corner_len = 6
    for cx, cy in [(14, 14), (196, 14), (14, 283), (196, 283)]:
        dx = corner_len if cx == 14 else -corner_len
        dy = corner_len if cy == 14 else -corner_len
        pdf.line(cx, cy, cx + dx, cy)
        pdf.line(cx, cy, cx, cy + dy)

    # 3. Header Branding
    # SAKSHI
    pdf.set_text_color(10, 10, 10)
    pdf.set_font("helvetica", "B", 28)
    pdf.set_xy(15, 24)
    pdf.cell(180, 10, "S A K S H I", align="C")

    # Tagline
    pdf.set_text_color(255, 85, 0)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_xy(15, 35)
    pdf.cell(180, 6, "SKILLS, WITNESSED.", align="C")

    # Category / Document Type
    pdf.set_text_color(110, 110, 110)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_xy(15, 42)
    pdf.cell(180, 5, "OFFICIAL VOCATIONAL SKILL CREDENTIAL", align="C")

    # Divider line
    pdf.set_draw_color(212, 206, 191)
    pdf.set_line_width(0.4)
    pdf.line(40, 50, 170, 50)

    # 4. Certification Statement
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("times", "I", 12)
    pdf.set_xy(15, 58)
    pdf.cell(180, 6, "This is to certify that", align="C")

    # Candidate Name
    worker_name = _clean(str(payload.get("worker_name", "Tradesperson")).strip())
    pdf.set_text_color(10, 10, 10)
    pdf.set_font("helvetica", "B", 24)
    pdf.set_xy(15, 68)
    pdf.cell(180, 10, worker_name, align="C")

    # Worker Area / Location
    area = _clean(str(payload.get("area", "")).strip())
    if area:
        pdf.set_text_color(120, 120, 120)
        pdf.set_font("helvetica", "", 10)
        pdf.set_xy(15, 79)
        pdf.cell(180, 6, area, align="C")

    # Competency statement
    pdf.set_text_color(80, 80, 80)
    pdf.set_font("times", "I", 11)
    pdf.set_xy(15, 90)
    pdf.cell(180, 6, "has demonstrated practical vocational competency in", align="C")

    # Trade & Skill
    trade = _clean(str(payload.get("trade", "Vocational Trade")).strip().upper())
    skill = _clean(str(payload.get("skill", "Practical Skill")).strip().upper())
    pdf.set_text_color(255, 85, 0)
    pdf.set_font("helvetica", "B", 15)
    pdf.set_xy(15, 98)
    pdf.cell(180, 8, f"{trade} - {skill}", align="C")

    # 5. Trust Metrics Card Box
    box_x = 25
    box_y = 114
    box_w = 160
    box_h = 44

    # Background of metrics box
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(220, 215, 205)
    pdf.set_line_width(0.4)
    pdf.rect(box_x, box_y, box_w, box_h, "DF")

    # 3 Column values in metrics box
    col_w = box_w / 3.0

    # Column 1: Tier
    tier_val = int(payload.get("tier", 1))
    tier_str = TIER_NAMES.get(tier_val, f"Tier {tier_val}")

    pdf.set_xy(box_x, box_y + 6)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(col_w, 4, "SEAL TIER", align="C")

    pdf.set_xy(box_x, box_y + 13)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 85, 0)
    pdf.cell(col_w, 6, f"TIER {tier_val}", align="C")

    pdf.set_xy(box_x, box_y + 21)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    subtier = "Demonstrated" if tier_val == 1 else ("Witnessed" if tier_val == 2 else ("Trusted" if tier_val == 3 else "Unverified"))
    pdf.cell(col_w, 4, subtier, align="C")

    # Column 2: Trust Score
    score = int(payload.get("trust_score", 0))
    pdf.set_xy(box_x + col_w, box_y + 6)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(col_w, 4, "TRUST SCORE", align="C")

    pdf.set_xy(box_x + col_w, box_y + 13)
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(col_w, 6, f"{score}/100", align="C")

    pdf.set_xy(box_x + col_w, box_y + 21)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(col_w, 4, "High Confidence" if score >= 75 else "Verified", align="C")

    # Column 3: Vouches / Witnesses
    witness_count = int(payload.get("witness_count", 0))
    pdf.set_xy(box_x + col_w * 2, box_y + 6)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(col_w, 4, "WITNESS VOUCHES", align="C")

    pdf.set_xy(box_x + col_w * 2, box_y + 13)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(col_w, 6, str(witness_count), align="C")

    pdf.set_xy(box_x + col_w * 2, box_y + 21)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(col_w, 4, "Peer Attestations", align="C")

    # Bottom strip of metrics box
    pdf.set_draw_color(230, 226, 218)
    pdf.line(box_x, box_y + 30, box_x + box_w, box_y + 30)
    pdf.set_xy(box_x, box_y + 33)
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(box_w, 5, "Verified via Multi-Modal AI Evaluation & Peer Witness Attestation Protocol", align="C")

    # 6. Verification & QR Code Section
    sec_y = 170
    pdf.set_xy(25, sec_y)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(160, 5, "CRYPTOGRAPHIC PROVENANCE & VERIFICATION", align="L")

    pdf.set_draw_color(212, 206, 191)
    pdf.line(25, sec_y + 6, 185, sec_y + 6)

    # Render QR Code
    cred_id = str(payload.get("cred_id", "N/A"))
    effective_url = verify_url or f"https://sakshi.org/c/{cred_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(effective_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Draw QR code image on left side
    qr_x = 25
    qr_y = sec_y + 11
    qr_size = 38
    pdf.image(qr_buffer, x=qr_x, y=qr_y, w=qr_size, h=qr_size)

    # Details on right side of QR code
    det_x = qr_x + qr_size + 6
    det_y = qr_y

    def add_meta_field(label: str, value: str, curr_y: float) -> float:
        pdf.set_xy(det_x, curr_y)
        pdf.set_font("helvetica", "B", 7.5)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(32, 4, label)

        pdf.set_xy(det_x + 32, curr_y)
        pdf.set_font("courier", "", 7.5)
        pdf.set_text_color(20, 20, 20)
        # truncate value if too long
        display_val = _clean(value if len(value) <= 48 else value[:45] + "...")
        pdf.cell(90, 4, display_val)
        return curr_y + 5.5

    cur = det_y
    cur = add_meta_field("CREDENTIAL ID:", cred_id, cur)
    issued_str = str(payload.get("issued_at", ""))[:19]
    cur = add_meta_field("ISSUED AT:", issued_str or "N/A", cur)
    valid_str = str(payload.get("valid_until", ""))[:19]
    cur = add_meta_field("VALID UNTIL:", valid_str or "N/A", cur)
    sha = str(payload.get("evidence_sha256", "none"))
    cur = add_meta_field("EVIDENCE SHA256:", sha, cur)
    cur = add_meta_field("VERIFY URL:", effective_url, cur)

    pdf.set_xy(det_x, cur + 2)
    pdf.set_font("helvetica", "I", 7.5)
    pdf.set_text_color(255, 85, 0)
    pdf.cell(90, 4, "Scan QR code or visit URL above to verify digital signature.")

    # 7. Signature Seal & Attestation block
    sig_y = 232
    pdf.set_draw_color(220, 215, 205)
    pdf.line(25, sig_y, 185, sig_y)

    # Left: SAKSHI seal text
    pdf.set_xy(25, sig_y + 4)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(10, 10, 10)
    pdf.cell(80, 4, "SAKSHI TRUST PROTOCOL")

    pdf.set_xy(25, sig_y + 9)
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(80, 3.5, "Cryptographic Ed25519 Signed Payload")

    pdf.set_xy(25, sig_y + 13)
    pdf.cell(80, 3.5, "Immutable Digital Evidence Record")

    # Right: Verification status badge
    pdf.set_xy(125, sig_y + 4)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(255, 85, 0)
    pdf.cell(60, 4, "[ OFFICIAL CERTIFICATE ]", align="R")

    pdf.set_xy(125, sig_y + 9)
    pdf.set_font("courier", "", 7)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(60, 3.5, "Tamper-evident record", align="R")

    # 8. Bottom Footer
    pdf.set_xy(15, 272)
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(140, 140, 140)
    pdf.cell(
        180,
        4,
        "SAKSHI — Decentralized Vocational Competency Network | Mystery Track: UnlockED (Problem 1)",
        align="C",
    )

    return bytes(pdf.output())
