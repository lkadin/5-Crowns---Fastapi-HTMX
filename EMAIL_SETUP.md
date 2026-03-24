# Email Service Configuration

The 5 Crowns application supports email notifications when new rooms are created.

## Setup Instructions

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com          # Your SMTP server (default: Gmail)
SMTP_PORT=587                       # SMTP port (default: 587 for TLS)
SENDER_EMAIL=your-email@gmail.com   # Email address to send from
SENDER_PASSWORD=your-app-password   # SMTP password (see below)
```

### 2. Gmail Setup (Recommended)

If using Gmail:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable "2-Step Verification" if not already enabled
3. Create an "App Password":
   - Go to "App passwords" under "Security"
   - Select "Mail" and "Windows Computer"
   - Google will generate a 16-character password
   - Use this password as `SENDER_PASSWORD` in your `.env` file

### 3. Other Email Providers

For other SMTP providers, replace the SMTP_SERVER and SMTP_PORT with your provider's settings:

- **Outlook**: `smtp.outlook.com`, port 587
- **Yahoo**: `smtp.mail.yahoo.com`, port 587
- **Custom Server**: Use your server's SMTP details

## Features

When a new room is created:
- If an email address is provided, a notification email is sent to the creator
- The email contains:
  - Room name and ID
  - A clickable link to join the game
  - Clear, formatted HTML and plain text versions

## Testing

To test email notifications:

1. Create a new room and provide your email address
2. Check your email inbox for the notification
3. Verify the link in the email works correctly

## Troubleshooting

If emails are not being sent:

1. Check that `SENDER_EMAIL` and `SENDER_PASSWORD` are set correctly
2. Verify the SMTP server and port are correct for your provider
3. Check application logs for error messages (look for "Failed to send email notification")
4. Some servers may have firewall rules - ensure port 587 is accessible
5. Gmail may require "Less secure apps" access if App Passwords don't work
