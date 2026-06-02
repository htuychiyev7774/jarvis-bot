import base64
import html
from google_auth import get_google_service
import google.generativeai as genai
import config

def get_gmail_service():
    """Returns a Gmail API service instance."""
    return get_google_service('gmail', 'v1')

def fetch_unread_emails(max_results=10):
    """Fetches unread messages from the inbox."""
    service = get_gmail_service()
    # List unread messages in the inbox
    results = service.users().messages().list(
        userId='me', 
        q='is:unread label:INBOX', 
        maxResults=max_results
    ).execute()
    
    return results.get('messages', [])

def get_email_details(message_id):
    """Retrieves and parses the details of a single email message."""
    service = get_gmail_service()
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    
    payload = message.get('payload', {})
    headers = payload.get('headers', [])
    
    subject = "No Subject"
    sender = "Unknown Sender"
    
    for header in headers:
        name = header.get('name', '').lower()
        if name == 'subject':
            subject = header.get('value', '')
        elif name == 'from':
            sender = header.get('value', '')
            
    snippet = message.get('snippet', '')
    
    # Extract body
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='ignore')
                    break
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='ignore')
            
    if not body:
        body = snippet  # Fallback to snippet if body extraction failed
        
    return {
        'id': message_id,
        'subject': subject,
        'sender': sender,
        'snippet': snippet,
        'body': body
    }

def categorize_and_summarize(email_details):
    """
    Categorizes the email and generates a summary.
    Uses Gemini API if available, otherwise falls back to a rule-based engine.
    """
    subject = email_details['subject']
    sender = email_details['sender'].lower()
    snippet = email_details['snippet']
    body = email_details['body'][:2000]  # Truncate body for prompt safety

    # 1. Use Gemini API if configured
    if config.GEMINI_API_KEY:
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = (
                "You are an AI assistant helping to triage emails.\n"
                f"Subject: {subject}\n"
                f"Sender: {sender}\n"
                f"Body snippet: {body}\n\n"
                "Please categorize this email into exactly one of these groups: Work, Personal, Urgent, Newsletter, Social, Spam.\n"
                "And provide a short, 1-sentence summary of the email in Uzbek (if the email content is in other languages, translate the summary to Uzbek).\n"
                "Response format: CATEGORY|SUMMARY (Only return this text, nothing else, no markdown, e.g. 'Urgent|Sizga yangi shartnoma loyihasi yuborildi, imzolash kutilmoqda.')"
            )
            
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            parts = result.split('|')
            if len(parts) >= 2:
                category = parts[0].strip()
                summary = parts[1].strip()
                return category, summary
        except Exception as e:
            print(f"Warning: Gemini email categorization failed, falling back to rule-based: {e}")

    # 2. Rule-Based Fallback
    category = "Personal"
    summary = snippet[:150] + "..." if len(snippet) > 150 else snippet
    
    # Simple keyword triaging
    combined_text = (subject + " " + snippet).lower()
    
    if any(k in sender for k in ["no-reply", "noreply", "notification", "alert"]):
        category = "Newsletter"
    if any(k in combined_text for k in ["unsubscribe", "newsletter", "mailing list", "click here", "subscribe"]):
        category = "Newsletter"
    elif any(k in combined_text for k in ["urgent", "action required", "asap", "critical", "important"]):
        category = "Urgent"
    elif any(k in sender for k in ["facebook", "linkedin", "twitter", "instagram", "social"]):
        category = "Social"
    elif any(k in combined_text for k in ["promo", "discount", "offer", "sale", "win", "free"]):
        category = "Spam"
    elif any(k in sender for k in ["work", "corp", "office", "manager", "team"]) or any(k in combined_text for k in ["report", "meeting", "project", "deadline"]):
        category = "Work"
        
    return category, f"[Tizim tomonidan saralangan: {category}] " + summary

def mark_email_as_read(message_id):
    """Removes the UNREAD label from a message."""
    service = get_gmail_service()
    service.users().messages().batchModify(
        userId='me',
        body={
            'ids': [message_id],
            'removeLabelIds': ['UNREAD']
        }
    ).execute()

def escape_tg_html(text):
    """Safely escapes text for Telegram's HTML parse mode."""
    return html.escape(text)
