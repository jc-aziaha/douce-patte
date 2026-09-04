from email.message import EmailMessage
from html import escape

import aiosmtplib

from app.config import Settings
from app.schemas import SERVICE_LABELS, ContactFields


def _build_text_body(data: ContactFields, service_label: str) -> str:
    contact_line = (
        f"{data.name} vous a contactée depuis le site pour une demande de "
        f"« {service_label} ». Vous pouvez la ou le joindre par e-mail à {data.email}, "
        f"ou par téléphone au {data.phone}."
    )

    if data.message:
        message_block = f"Voici ce qu'elle ou il a écrit :\n\n« {data.message} »"
    else:
        message_block = f"{data.name} n'a pas laissé de message avec sa demande."

    return "\n\n".join(
        [
            "Bonjour Manon,",
            contact_line,
            message_block,
            f"Vous pouvez répondre directement à cet e-mail : la réponse partira à {data.email}.",
        ]
    )


def _build_html_body(data: ContactFields, service_label: str) -> str:
    name = escape(data.name)
    email_addr = escape(data.email)
    phone = escape(data.phone)

    if data.message:
        message_section = f"""\
        <p style="margin:0 0 8px;">Voici ce qu'elle ou il a écrit :</p>
        <div style="margin:0;padding:16px 18px;background:#fff9ef;
            border-radius:8px;line-height:1.6;">
          « {escape(data.message).replace("\n", "<br>")} »
        </div>"""
    else:
        message_section = (
            f'<p style="margin:0;">{name} n\'a pas laissé de message avec sa demande.</p>'
        )

    serif = "Georgia,'Times New Roman',serif"
    sans = "Arial,Helvetica,sans-serif"

    return f"""\
<!doctype html>
<html lang="fr">
<body style="margin:0;padding:32px 16px;background:#fff9ef;
    font-family:{serif};color:#38423f;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="
      max-width:520px;margin:0 auto;background:#ffffff;border-radius:16px;
      overflow:hidden;border:1px solid rgba(56,66,63,.08);">
    <tr>
      <td style="padding:28px 32px 20px;">
        <p style="margin:0;font-size:13px;font-weight:bold;letter-spacing:.08em;
            text-transform:uppercase;color:#bd4732;">Douce Patte</p>
        <h1 style="margin:6px 0 0;font-size:22px;font-weight:normal;color:#38423f;">
          Nouvelle demande de contact</h1>
      </td>
    </tr>
    <tr>
      <td style="padding:0 32px;">
        <span style="display:inline-block;padding:6px 14px;border-radius:999px;
            background:#f1e8dc;color:#38423f;font-family:{sans};font-size:13px;
            font-weight:bold;">{escape(service_label)}</span>
      </td>
    </tr>
    <tr>
      <td style="padding:20px 32px 0;font-family:{sans};font-size:15px;line-height:1.7;">
        <p style="margin:0;"><strong>{name}</strong> vous a contactée depuis le site pour
          cette demande. Vous pouvez la ou le joindre par e-mail à
          <a href="mailto:{email_addr}" style="color:#bd4732;text-decoration:none;">
            {email_addr}</a>, ou par téléphone au <strong>{phone}</strong>.</p>
      </td>
    </tr>
    <tr>
      <td style="padding:16px 32px 28px;font-family:{sans};font-size:15px;line-height:1.7;">
        {message_section}
      </td>
    </tr>
    <tr>
      <td style="padding:0 32px 28px;font-family:{sans};font-size:13px;color:#5d6a66;">
        Vous pouvez répondre directement à cet e-mail : la réponse partira à {email_addr}.
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_contact_notification(data: ContactFields, settings: Settings) -> None:
    service_label = SERVICE_LABELS[data.service]

    message = EmailMessage()
    message["Subject"] = f"Nouvelle demande — {service_label}"
    message["From"] = settings.from_email
    message["To"] = settings.notify_email
    message["Reply-To"] = data.email

    message.set_content(_build_text_body(data, service_label))
    message.add_alternative(_build_html_body(data, service_label), subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_use_tls,
    )
