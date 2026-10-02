import smtplib
import mimetypes
from email.message import EmailMessage

def get_mime_type(file_name):
    maintype, subtype = None, None
    ctype, encoding = mimetypes.guess_type(file_name)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    return maintype, subtype

def send_email(smtp_host, smtp_port, smtp_user, smtp_pass, to_email, subject, html_content, attachments=None, inline_images=None):
    """
    Sends an email using the specified SMTP server.
    Supports HTML content, file attachments, and inline CID images.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = to_email
    
    # Set primary content directly to HTML
    msg.set_content(html_content, subtype='html')

    # Handle inline images (for Headers and Footers via CID)
    if inline_images:
        for cid, img_file in inline_images.items():
            maintype, subtype = get_mime_type(img_file.name)
            msg.add_related(img_file.getvalue(), maintype=maintype, subtype=subtype, cid=f"<{cid}>")

    # Handle attachments
    if attachments:
        for uploaded_file in attachments:
            file_data = uploaded_file.getvalue()
            file_name = uploaded_file.name
            maintype, subtype = get_mime_type(file_name)
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

    # Send the email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        # Secure the connection
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
