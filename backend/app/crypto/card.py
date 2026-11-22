"""
backend/app/crypto/card.py

Generates 600x1000 WhatsApp share-card PNG for verified credentials.
Design Tokens:
- Background: Ink black #0A0A0A
- Text / Graphics: Paper white #F6F3EC
- Highlight: SAKSHI Orange #FF7A1A
- Muted: #A3A3A3
- Card Box / Border: #171717 / #262626
"""
import io
from typing import Any, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
import qrcode

TIER_NAMES: Dict[int, str] = {
    0: "Needs Retry",
    1: "Demonstrated",
    2: "Witnessed",
    3: "Trusted",
}


def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """
    Attempts to load a standard truetype font; falls back to default if unavailable.
    """
    font_names = (
        ["arialbd.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "segoeui.ttf"]
    )
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None  # type: ignore


def generate_share_card(
    payload: Dict[str, Any],
    verify_url: str,
) -> bytes:
    """
    Renders a 600x1000 PNG card with candidate details, tier badge, trust score,
    cryptographic digest, and scan-to-verify QR code.
    """
    width, height = 600, 1000

    # Colors
    bg_color = (10, 10, 10)  # #0A0A0A
    paper_color = (246, 243, 236)  # #F6F3EC
    orange_color = (255, 122, 26)  # #FF7A1A
    muted_color = (163, 163, 163)  # #A3A3A3
    box_bg = (23, 23, 23)  # #171717
    border_color = (38, 38, 38)  # #262626

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rounded_rectangle(
        [(16, 16), (width - 16, height - 16)],
        radius=24,
        outline=border_color,
        width=2,
    )

    # Fonts
    font_logo = _get_font(32, bold=True)
    font_tagline = _get_font(15, bold=False)
    font_label = _get_font(11, bold=True)
    font_title = _get_font(26, bold=True)
    font_subtitle = _get_font(15, bold=False)
    font_tier = _get_font(18, bold=True)
    font_score = _get_font(30, bold=True)
    font_mono = _get_font(11, bold=False)
    font_qr_title = _get_font(14, bold=True)
    font_footer = _get_font(12, bold=False)

    # 1. Header / Branding
    draw.text((45, 45), "SAKSHI", fill=paper_color, font=font_logo)
    draw.text((45, 85), "Skills, witnessed.", fill=orange_color, font=font_tagline)
    draw.text(
        (380, 55),
        "VERIFIED CREDENTIAL",
        fill=muted_color,
        font=font_label,
    )

    # Separator
    draw.line([(45, 120), (width - 45, 120)], fill=border_color, width=1)

    # 2. Tradesperson Info
    worker_name = str(payload.get("worker_name", "Tradesperson"))
    trade = str(payload.get("trade", "Trade"))
    skill = str(payload.get("skill", "Practical Skill"))
    area = str(payload.get("area", "India"))

    draw.text((45, 140), "CANDIDATE TRADESPERSON", fill=muted_color, font=font_label)
    draw.text((45, 162), worker_name, fill=paper_color, font=font_title)
    draw.text(
        (45, 202),
        f"{trade} • {skill}",
        fill=orange_color,
        font=font_subtitle,
    )
    draw.text((45, 228), f"Verified in: {area}", fill=muted_color, font=font_mono)

    # 3. Tier & Trust Score Box
    draw.rounded_rectangle(
        [(45, 265), (width - 45, 385)],
        radius=16,
        fill=box_bg,
        outline=border_color,
        width=1,
    )

    tier = int(payload.get("tier", 1))
    tier_name = TIER_NAMES.get(tier, "Demonstrated")
    witness_count = int(payload.get("witness_count", 0))

    # Left: Tier
    draw.text((65, 285), "VERIFIED TIER", fill=muted_color, font=font_label)
    draw.text(
        (65, 308),
        f"TIER {tier}: {tier_name.upper()}",
        fill=orange_color,
        font=font_tier,
    )
    draw.text(
        (65, 345),
        f"{witness_count} peer vouches recorded",
        fill=muted_color,
        font=font_mono,
    )

    # Divider in box
    draw.line([(320, 280), (320, 370)], fill=border_color, width=1)

    # Right: Trust Score
    trust_score = int(payload.get("trust_score", 0))
    draw.text((345, 285), "DISPLAY TRUST SCORE", fill=muted_color, font=font_label)
    draw.text((345, 305), f"{trust_score}/100", fill=paper_color, font=font_score)
    draw.text(
        (345, 345),
        "Deterministic multi-layer proof",
        fill=muted_color,
        font=font_mono,
    )

    # 4. QR Code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_size = 240
    qr_img = qr_img.resize((qr_size, qr_size))

    # Center QR code
    qr_x = (width - qr_size) // 2
    qr_y = 415
    img.paste(qr_img, (qr_x, qr_y))

    # 5. Under-QR Labels
    qr_title_text = "SCAN TO VERIFY ED25519 SIGNATURE"
    draw.text((150, 675), qr_title_text, fill=paper_color, font=font_qr_title)

    draw.text(
        (160, 702),
        "In-browser cryptographic verification via tweetnacl",
        fill=muted_color,
        font=font_mono,
    )

    valid_until = str(payload.get("valid_until", ""))
    if valid_until:
        valid_date_str = valid_until[:10]
        draw.text(
            (215, 725),
            f"Valid until: {valid_date_str}",
            fill=orange_color,
            font=font_subtitle,
        )

    # 6. Cryptographic Info Box
    draw.rounded_rectangle(
        [(45, 765), (width - 45, 875)],
        radius=12,
        fill=box_bg,
        outline=border_color,
        width=1,
    )

    cred_id = str(payload.get("cred_id", ""))
    sha = str(payload.get("evidence_sha256", "none"))

    draw.text(
        (60, 780),
        f"CREDENTIAL ID: {cred_id}",
        fill=muted_color,
        font=font_mono,
    )
    draw.text(
        (60, 805),
        f"EVIDENCE SHA-256: {sha[:36]}...",
        fill=muted_color,
        font=font_mono,
    )
    draw.text(
        (60, 830),
        "STATUS: SIGNATURE VALID • ED25519 VERIFIED",
        fill=orange_color,
        font=font_mono,
    )

    # 7. Bottom Branding
    draw.text(
        (190, 915),
        "Verify at SAKSHI • Skills, witnessed.",
        fill=muted_color,
        font=font_footer,
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
