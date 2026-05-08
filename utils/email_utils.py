import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_verification_email(to_email, verification_code):
    """Send verification code to user's email"""
    return _send_email(
        to_email,
        "Email Verification Code - Smart Complaint System",
        "Thank you for registering with our Smart Complaint Management System.",
        verification_code
    )


def send_reset_code_email(to_email, verification_code):
    """Send password reset code to user's email"""
    return _send_email(
        to_email,
        "Password Reset Code - Smart Complaint System",
        "We received a request to reset your password.",
        verification_code
    )


def _send_email(to_email, subject, intro_text, verification_code):
    try:
        from_email = os.getenv('EMAIL_USER')
        password = os.getenv('EMAIL_PASSWORD')
        
        if not from_email or not password:
            message = "Email credentials are not configured in .env file"
            return False, message
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 20px auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    padding: 40px;
                    text-align: center;
                }}
                .code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #667eea;
                    background: #f0f0f0;
                    padding: 20px;
                    border-radius: 10px;
                    letter-spacing: 5px;
                    margin: 20px 0;
                    font-family: monospace;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Smart Complaint System</h1>
                    <p>{subject}</p>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>{intro_text}</p>
                    <p>Please use the following code to continue:</p>
                    <div class="code">{verification_code}</div>
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply to this email.</p>
                    <p>&copy; 2024 Smart Complaint System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        
        return True, None
        
    except Exception as e:
        error_message = str(e)
        return False, error_message

