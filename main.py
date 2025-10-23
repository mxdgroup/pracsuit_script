from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_logs.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Email Forwarding Logger", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Email Logger API is running", "status": "active"}


@app.post("/webhook/email")
async def receive_email(request: Request):
    """
    Endpoint to receive email data from Google Apps Script
    Logs the complete email structure
    """
    try:
        # Get the raw body
        body = await request.body()
        
        # Try to parse as JSON
        try:
            email_data = await request.json()
            logger.info("=" * 80)
            logger.info("NEW EMAIL RECEIVED")
            logger.info("=" * 80)
            
            # Log the entire structure
            logger.info("Complete Email Structure:")
            logger.info(json.dumps(email_data, indent=2, default=str))
            
            # Log specific fields if they exist
            if isinstance(email_data, dict):
                logger.info("\n--- Email Details ---")
                logger.info(f"From: {email_data.get('from', 'N/A')}")
                logger.info(f"To: {email_data.get('to', 'N/A')}")
                logger.info(f"Subject: {email_data.get('subject', 'N/A')}")
                logger.info(f"Date: {email_data.get('date', 'N/A')}")
                logger.info(f"Body Length: {len(email_data.get('body', ''))}")
                
                if 'attachments' in email_data:
                    logger.info(f"Attachments: {len(email_data.get('attachments', []))}")
                    for idx, att in enumerate(email_data.get('attachments', [])):
                        logger.info(f"  Attachment {idx + 1}: {att.get('name', 'N/A')} ({att.get('size', 'N/A')} bytes)")
            
            logger.info("=" * 80)
            
            # Also save to a JSON file for inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = Path(f"emails/email_{timestamp}.json")
            json_file.parent.mkdir(exist_ok=True)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(email_data, f, indent=2, default=str)
            
            logger.info(f"Email data saved to: {json_file}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Email logged successfully",
                    "timestamp": datetime.now().isoformat(),
                    "saved_to": str(json_file)
                }
            )
            
        except json.JSONDecodeError:
            # If not JSON, log the raw body
            logger.warning("Received non-JSON data:")
            logger.info(f"Raw body: {body.decode('utf-8', errors='replace')}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "warning",
                    "message": "Received non-JSON data, logged as raw text",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

