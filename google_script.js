/**
 * Google Apps Script to forward emails with attachments to FastAPI endpoint
 * 
 * Features:
 * - Forwards email metadata and content
 * - Base64 encodes and sends attachments
 * - Marks emails as read after processing
 * - Adds "Forwarded" label to processed emails
 * 
 * Setup Instructions:
 * 1. Go to https://script.google.com/
 * 2. Create a new project
 * 3. Paste this code
 * 4. Update the FASTAPI_ENDPOINT with your actual endpoint URL
 * 5. Run manualTrigger() once to authorize the script
 * 6. Set up a time-driven trigger to run checkEmails() every 5 minutes
 * 
 * Important: This script now sends attachment data as base64
 * Make sure your FastAPI endpoint can handle large payloads for Excel files
 */

// Configuration
const FASTAPI_ENDPOINT = "https://joann-premoral-ayla.ngrok-free.dev/webhook/email";
const LABEL_NAME = "Forwarded"; // Label to mark processed emails

function checkEmails() {
  try {
    // Get unread messages from inbox
    const threads = GmailApp.search('is:unread in:inbox', 0, 10);
    
    Logger.log(`Found ${threads.length} unread threads`);
    
    threads.forEach(thread => {
      const messages = thread.getMessages();
      
      messages.forEach(message => {
        if (message.isUnread()) {
          forwardEmailToAPI(message);
          message.markRead();
          
          // Add label to track processed emails
          const label = getOrCreateLabel(LABEL_NAME);
          thread.addLabel(label);
        }
      });
    });
    
  } catch (error) {
    Logger.log(`Error in checkEmails: ${error.toString()}`);
  }
}

function forwardEmailToAPI(message) {
  try {
    // Extract email data
    const emailData = {
      messageId: message.getId(),
      threadId: message.getThread().getId(),
      from: message.getFrom(),
      to: message.getTo(),
      cc: message.getCc(),
      bcc: message.getBcc(),
      replyTo: message.getReplyTo(),
      subject: message.getSubject(),
      date: message.getDate().toISOString(),
      body: message.getPlainBody(),
      bodyHtml: message.getBody(),
      isUnread: message.isUnread(),
      isStarred: message.isStarred(),
      isDraft: message.isDraft(),
      isInInbox: message.isInInbox(),
      isInTrash: message.isInTrash(),
      labels: message.getThread().getLabels().map(label => label.getName()),
      attachments: []
    };
    
    // Process attachments
    const attachments = message.getAttachments();
    if (attachments.length > 0) {
      Logger.log(`Found ${attachments.length} attachment(s)`);
      attachments.forEach(attachment => {
        const attachmentData = {
          name: attachment.getName(),
          size: attachment.getSize(),
          contentType: attachment.getContentType(),
          data: Utilities.base64Encode(attachment.getBytes()) // Base64 encode for transmission
        };
        emailData.attachments.push(attachmentData);
        Logger.log(`Attachment: ${attachmentData.name} (${attachmentData.size} bytes)`);
      });
    }
    
    Logger.log(`Processing email: ${emailData.subject}`);
    
    // Send to FastAPI endpoint
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(emailData),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(FASTAPI_ENDPOINT, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    Logger.log(`API Response Code: ${responseCode}`);
    Logger.log(`API Response: ${responseText}`);
    
    if (responseCode >= 200 && responseCode < 300) {
      Logger.log(`Successfully forwarded email: ${emailData.subject}`);
    } else {
      Logger.log(`Failed to forward email. Status: ${responseCode}`);
    }
    
  } catch (error) {
    Logger.log(`Error forwarding email to API: ${error.toString()}`);
  }
}

function getOrCreateLabel(labelName) {
  let label = GmailApp.getUserLabelByName(labelName);
  if (!label) {
    label = GmailApp.createLabel(labelName);
  }
  return label;
}

// Test function to send a single test email
function testForwardEmail() {
  const threads = GmailApp.search('in:inbox', 0, 1);
  if (threads.length > 0) {
    const message = threads[0].getMessages()[0];
    forwardEmailToAPI(message);
  } else {
    Logger.log('No emails found to test');
  }
}

// Function to manually trigger email check (for testing)
function manualTrigger() {
  checkEmails();
}

