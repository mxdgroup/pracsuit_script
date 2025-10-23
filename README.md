# Email Logger - Google Scripts to FastAPI

This project forwards emails from Gmail to a FastAPI endpoint and logs the complete email structure.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the FastAPI Server

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 3. Configure Google Apps Script

1. Go to https://script.google.com/
2. Create a new project
3. Copy the code from `google_script.js`
4. Update the `FASTAPI_ENDPOINT` variable with your public URL (use ngrok for local testing)
5. Run the `manualTrigger()` function to authorize the script
6. Set up a time-driven trigger:
   - Click on the clock icon (Triggers)
   - Add Trigger
   - Choose function: `checkEmails`
   - Select event source: Time-driven
   - Select type of time based trigger: Minutes timer
   - Select minute interval: Every 5 minutes (or your preference)

### 4. For Local Testing with ngrok

```bash
ngrok http 8000
```

Copy the ngrok URL and update it in the Google Apps Script.

## API Endpoints

- `GET /` - Root endpoint, returns API status
- `POST /webhook/email` - Receives email data from Google Scripts
- `GET /health` - Health check endpoint

## Logging

Emails are logged in two ways:
1. **Console & Log File**: All emails are logged to `email_logs.log`
2. **JSON Files**: Each email is saved as a JSON file in the `emails/` directory

## Email Structure

The Google Script sends the following data structure:

```json
{
  "messageId": "string",
  "threadId": "string",
  "from": "sender@example.com",
  "to": "recipient@example.com",
  "cc": "cc@example.com",
  "bcc": "bcc@example.com",
  "replyTo": "reply@example.com",
  "subject": "Email Subject",
  "date": "2024-01-01T12:00:00.000Z",
  "body": "Plain text body",
  "bodyHtml": "HTML body",
  "isUnread": true,
  "isStarred": false,
  "isDraft": false,
  "isInInbox": true,
  "isInTrash": false,
  "labels": ["Label1", "Label2"],
  "attachments": [
    {
      "name": "file.pdf",
      "size": 12345,
      "contentType": "application/pdf"
    }
  ]
}
``` 
