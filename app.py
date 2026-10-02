import streamlit as st
import pandas as pd
from streamlit_quill import st_quill
from mailer import send_email
from template_engine import render_template
import os
import base64
import re
from dotenv import load_dotenv

# Load environment variables if .env file exists
load_dotenv()

st.set_page_config(page_title="Bulk Email Blaster", layout="wide")

st.title("Bulk Email Blaster")
st.markdown("Send rich-text bulk emails with attachments using your company's SMTP server.")

# --- SIDEBAR: SMTP CONFIGURATION ---
st.sidebar.header("SMTP Configuration")
smtp_host = st.sidebar.text_input("SMTP Host", value=os.getenv("SMTP_HOST", "mail.olympia-education.com"))
smtp_port = st.sidebar.number_input("SMTP Port", value=int(os.getenv("SMTP_PORT", 587)))
smtp_user = st.sidebar.text_input("SMTP User/Email", value=os.getenv("SMTP_USER", ""))
smtp_pass = st.sidebar.text_input("SMTP Password", value=os.getenv("SMTP_PASS", ""), type="password")

st.sidebar.markdown("---")
st.sidebar.info("Your SMTP connection is configured for olympia-education.com.")

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<div style='text-align: center; color: #888888; font-size: 12px; margin-top: 20px;'>Made by dhwplt</div>", 
    unsafe_allow_html=True
)

# --- STEP 1: UPLOAD DATA ---
st.header("1. Upload Contact List")
data_file = st.file_uploader("Upload Excel File (.xlsx)", type=["xlsx"])

df = None
if data_file:
    df = pd.read_excel(data_file)
    
    # Sanitize column names to prevent Jinja syntax errors (removes spaces/special chars)
    df.columns = [re.sub(r'\W+', '_', str(c)).strip('_') for c in df.columns]
    
    st.success("File uploaded successfully!")
    st.dataframe(df, height=250)
    
    # Highlight placeholders based on Excel columns
    placeholders = ", ".join([f"`{{{{ {col} }}}}`" for col in df.columns])
    st.info(f"**Available Placeholders:** {placeholders}")
    
    if not any('email' in col.lower() for col in df.columns):
        st.warning("Could not find an 'Email' column in your Excel sheet. The app looks for a column containing the word 'Email' to send to.")

# --- STEP 2: COMPOSE EMAIL ---
st.header("2. Compose Email")
subject_template = st.text_input("Email Subject", placeholder="Hello {{ Full_Name }}, your monthly update")

editor_col1, editor_col2 = st.columns([3, 1])
with editor_col1:
    st.write("Email Body (Rich Text)")
with editor_col2:
    use_fallback = st.checkbox("Use Basic Editor (Fixes UI Glitches)", value=False)

if use_fallback:
    body_template = st.text_area(
        "Email Body", 
        placeholder="Write your HTML or text here... Use {{ ColumnName }} for placeholders.",
        height=300
    )
else:
    # Assigning a unique key prevents the iframe from breaking when you upload a file
    body_template = st_quill(
        placeholder="Write your email here... Use {{ ColumnName }} to insert dynamic values from your Excel file.",
        html=True,
        key="quill_email_editor"
    )

st.subheader("Header & Footer Images")
st.info("Upload image files directly from your computer. They will be securely embedded into your emails.")

col1, col2 = st.columns(2)
with col1:
    st.write("**Header Image**")
    header_file = st.file_uploader("Upload Header Image", type=['png', 'jpg', 'jpeg'])
    header_width = st.number_input("Header Width (px)", min_value=50, max_value=800, value=600, step=10)
with col2:
    st.write("**Footer Image**")
    footer_file = st.file_uploader("Upload Footer Image", type=['png', 'jpg', 'jpeg'])
    footer_width = st.number_input("Footer Width (px)", min_value=50, max_value=800, value=600, step=10)

def get_image_base64(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
    return None

def assemble_email_html(preview_mode=False):
    """Wraps the Quill body with the header and footer images."""
    body_content = body_template if body_template else ""
    
    header_html = ""
    if header_file:
        if preview_mode:
            b64 = get_image_base64(header_file)
            src = f"data:{header_file.type};base64,{b64}"
        else:
            src = "cid:header_img"
        header_html = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{src}" width="{header_width}" style="max-width: 100%; height: auto;"></div>\n'
        
    footer_html = ""
    if footer_file:
        if preview_mode:
            b64 = get_image_base64(footer_file)
            src = f"data:{footer_file.type};base64,{b64}"
        else:
            src = "cid:footer_img"
        footer_html = f'\n<div style="text-align: center; margin-top: 20px;"><img src="{src}" width="{footer_width}" style="max-width: 100%; height: auto;"></div>'
        
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #ffffff;">
        <div style="max-width: 600px; margin: 0 auto; padding: 15px;">
            {header_html}
            {body_content}
            {footer_html}
        </div>
    </body>
    </html>
    """
    return final_html

# Setup inline images dictionary for the mailer
inline_images = {}
if header_file:
    inline_images['header_img'] = header_file
if footer_file:
    inline_images['footer_img'] = footer_file

# --- LIVE PREVIEW ---
st.subheader("Live Email Preview")
st.info("This is how your email will look! (If you've uploaded an Excel file, we'll use the first row to test your placeholders).")
preview_html = assemble_email_html(preview_mode=True)
if df is not None and not df.empty:
    preview_context = df.iloc[0].to_dict()
    preview_context['RowNumber'] = "001"
    try:
        preview_html = render_template(preview_html, preview_context)
    except Exception:
        pass # Fallback to raw placeholders if syntax is broken while typing

st.components.v1.html(
    f"<div style='border: 1px solid #ccc; padding: 20px; border-radius: 5px; background: white; color: black; font-family: Arial, sans-serif;'>{preview_html}</div>", 
    height=450, 
    scrolling=True
)

# --- STEP 3: ATTACHMENTS ---
st.header("3. Attachments")
attachment_mode = st.radio("Attachment Mode", [
    "No Attachments", 
    "Same attachments for everyone", 
    "Personalized attachments (different file per person)"
])

attachments = []
attachment_match_method = None
attachment_column = None
attachment_template = None

if attachment_mode != "No Attachments":
    attachments = st.file_uploader("Upload Attachments", accept_multiple_files=True)
    
    if attachment_mode == "Personalized attachments (different file per person)":
        if df is not None and not df.empty:
            attachment_match_method = st.radio("How should we match files to people?", [
                "Construct filename dynamically (e.g. cert_{{ Full_Name }}.pdf)",
                "I have an Excel column with the exact filenames"
            ])
            
            if attachment_match_method == "I have an Excel column with the exact filenames":
                attachment_column = st.selectbox("Which Excel column contains the attachment filename(s)?", df.columns)
                st.info(f"Make sure the files you upload exactly match the names in the `{attachment_column}` column (e.g., `cert.pdf`). \n\n**Tip:** To attach multiple files to one person, separate the filenames with a comma in your Excel sheet.")
            else:
                attachment_template = st.text_input("Filename Template", value="{{ RowNumber }}_{{ Full_Name | replace(' ', '_') }}.pdf")
                st.info("💡 **Pro-Tip:** We automatically added a `{{ RowNumber }}` placeholder (001, 002) and you can use `| replace(' ', '_')` to change spaces to underscores so it matches your files perfectly!")
        else:
            st.warning("Please upload your Excel file first to configure attachments.")

def get_row_attachments(context_dict):
    """Helper to fetch the correct attachments for a given row context."""
    if attachment_mode == "Same attachments for everyone":
        return attachments
    elif attachment_mode == "Personalized attachments (different file per person)":
        target_filenames_raw = ""
        if attachment_match_method == "I have an Excel column with the exact filenames" and attachment_column:
            target_filenames_raw = str(context_dict.get(attachment_column, "")).strip()
        elif attachment_match_method == "Construct filename dynamically (e.g. cert_{{ Full_Name }}.pdf)" and attachment_template:
            target_filenames_raw = render_template(attachment_template, context_dict).strip()

        if target_filenames_raw and target_filenames_raw.lower() != "nan":
            # Support multiple files separated by comma or semicolon
            filenames = [f.strip() for f in re.split(r'[,;]', target_filenames_raw) if f.strip()]
            
            matched_files = []
            for fname in filenames:
                matched_file = next((f for f in attachments if f.name == fname), None)
                if matched_file:
                    matched_files.append(matched_file)
                else:
                    raise Exception(f"Required attachment '{fname}' was not found in the uploaded files.")
            return matched_files
    return []


# --- STEP 4: PRE-FLIGHT CHECK ---
st.header("4. Verify Matches (Pre-Flight Check)")
st.info("Check this table to ensure the right files are matched to the right people before you send anything.")

if df is not None and not df.empty:
    if st.button("Run Pre-Flight Check"):
        with st.spinner("Analyzing rows..."):
            preview_data = []
            email_col = next((col for col in df.columns if 'email' in col.lower()), None)
            
            for index, row in df.iterrows():
                context = row.to_dict()
                context['RowNumber'] = f"{index + 1:03d}"
                target_email = context.get(email_col) if email_col else "Missing Email"
                
                try:
                    subject_prev = render_template(subject_template, context) if subject_template else "No Subject"
                except Exception:
                    subject_prev = "❌ Template Syntax Error"
                    
                attached_names = []
                status = "✅ Ready"
                
                try:
                    atts = get_row_attachments(context)
                    attached_names = [a.name for a in atts]
                    if attachment_mode == "Personalized attachments (different file per person)" and not attached_names:
                        status = "⚠️ No files matched"
                except Exception as e:
                    status = f"❌ {str(e)}"
                
                if pd.isna(target_email) or not str(target_email).strip():
                     status = "❌ Missing Email Address"
                
                preview_data.append({
                    "Excel Row": index + 2,
                    "Target Email": target_email,
                    "Subject Preview": subject_prev,
                    "Attachments Matched": ", ".join(attached_names) if attached_names else "None",
                    "Status": status
                })
            
            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df.astype(str), use_container_width=True, height=300)
            
            error_count = sum(1 for d in preview_data if '❌' in d['Status'])
            warn_count = sum(1 for d in preview_data if '⚠️' in d['Status'])
            
            if error_count > 0:
                st.error(f"Cannot send: Found {error_count} critical errors. Please check the Status column.")
            elif warn_count > 0:
                st.warning(f"Found {warn_count} warnings (e.g. no attachments for some people). Review before sending.")
            else:
                st.success("All rows verified! Everything matches perfectly.")


# --- STEP 5: SEND TEST ---
st.header("5. Test & Send")
st.subheader("Test Send")
test_email = st.text_input("Test Email Address (Sends row 1 data to this address)")

if st.button("Send Test Email"):
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        st.error("Please fill in all SMTP configurations in the sidebar.")
    elif not test_email:
        st.error("Please provide a test email address.")
    elif df is None or df.empty:
        st.error("Please upload an Excel file to serve as test data.")
    elif not subject_template or not body_template:
        st.error("Please provide an email subject and body.")
    else:
        # Use first row for testing template rendering
        test_context = df.iloc[0].to_dict()
        test_context['RowNumber'] = "001"
        try:
            full_html_template = assemble_email_html(preview_mode=False)
            rendered_subject = render_template(subject_template, test_context)
            rendered_body = render_template(full_html_template, test_context)
            row_attachments = get_row_attachments(test_context)
            
            with st.spinner("Sending test email..."):
                send_email(
                    smtp_host=smtp_host, 
                    smtp_port=int(smtp_port), 
                    smtp_user=smtp_user, 
                    smtp_pass=smtp_pass, 
                    to_email=test_email, 
                    subject=rendered_subject, 
                    html_content=rendered_body, 
                    attachments=row_attachments,
                    inline_images=inline_images
                )
            st.success(f"Test email sent successfully to {test_email}! Check your inbox to verify formatting.")
                
        except Exception as e:
            st.error(f"Failed to send test email: {str(e)}")


# --- STEP 5: BLAST ALL ---
st.subheader("Blast Emails")
st.warning("Clicking 'Send All' will immediately begin sending emails to every row in the uploaded Excel file.")

if st.button("Send All", type="primary"):
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        st.error("Please fill in all SMTP configurations in the sidebar.")
    elif df is None or df.empty:
        st.error("Please upload an Excel file.")
    elif not subject_template or not body_template:
        st.error("Please provide an email subject and body.")
    else:
        # Find the email column (case insensitive)
        email_col = next((col for col in df.columns if 'email' in col.lower()), None)
        
        if not email_col:
            st.error("Could not find a column named 'Email'. Please ensure your Excel file has an Email column.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            error_count = 0
            errors = []
            
            full_html_template = assemble_email_html(preview_mode=False)
            
            for index, row in df.iterrows():
                context = row.to_dict()
                context['RowNumber'] = f"{index + 1:03d}"
                target_email = context.get(email_col)
                
                # Skip rows with no email
                if pd.isna(target_email) or not str(target_email).strip():
                    error_count += 1
                    errors.append(f"Row {index + 2}: Missing email address.")
                    continue
                    
                try:
                    rendered_subject = render_template(subject_template, context)
                    rendered_body = render_template(full_html_template, context)
                    row_attachments = get_row_attachments(context)
                    
                    send_email(
                        smtp_host=smtp_host, 
                        smtp_port=int(smtp_port), 
                        smtp_user=smtp_user, 
                        smtp_pass=smtp_pass, 
                        to_email=target_email, 
                        subject=rendered_subject, 
                        html_content=rendered_body, 
                        attachments=row_attachments,
                        inline_images=inline_images
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {index + 2} ({target_email}): {str(e)}")
                    
                # Update progress
                progress = (index + 1) / len(df)
                progress_bar.progress(progress)
                status_text.text(f"Sent {index + 1} of {len(df)} emails...")
            
            st.success(f"Blast Complete! Successfully sent: {success_count}. Errors: {error_count}.")
            
            if errors:
                with st.expander("View Errors"):
                    for error in errors:
                        st.write(error)
