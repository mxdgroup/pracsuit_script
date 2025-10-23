/**
 * Google Apps Script to forward emails to FastAPI endpoint
 * 
 * Setup Instructions:
 * 1. Go to https://script.google.com/
 * 2. Create a new project
 * 3. Paste this code
 * 4. Set up a time-driven trigger to run checkEmails() every minute/5 minutes
 * 5. Update the FASTAPI_ENDPOINT with your actual endpoint URL
 */

// Configuration
const FASTAPI_ENDPOINT = "YOUR_FASTAPI_URL/webhook/email"; // Replace with your actual URL
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
      attachments.forEach(attachment => {
        emailData.attachments.push({
          name: attachment.getName(),
          size: attachment.getSize(),
          contentType: attachment.getContentType(),
          // Base64 encode the attachment if you want to send it
          // data: Utilities.base64Encode(attachment.getBytes())
        });
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

