# Google OAuth Setup Guide for Mobilize CRM

This guide walks you through setting up Google OAuth2 credentials for your Mobilize CRM application.

## Project Information
- **Project ID**: `mobilize-crm-1750430768`
- **Project Name**: Mobilize CRM
- **APIs Enabled**: Gmail, Google Calendar, Google People

## Step 1: Access Google Cloud Console

1. Go to: https://console.cloud.google.com
2. Make sure "Mobilize CRM" project is selected in the top dropdown

## Step 2: Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. Select **Internal** user type (since this is for crossoverglobal.net users only)
3. Click **CREATE**

**Benefits of Internal App**:
- No Google verification required
- No user limits
- All scopes available without review
- Only crossoverglobal.net users can access

### App Information
Fill in these fields:

- **App name**: Mobilize CRM
- **User support email**: j.burchel@crossoverglobal.net
- **App logo**: (optional - you can upload your logo)

### App Domain
- **Application home page**: http://localhost:8000 (update later with Railway URL)
- **Application privacy policy**: (leave blank for now)
- **Application terms of service**: (leave blank for now)

### Authorized domains
- Not needed for internal apps (automatically restricted to crossoverglobal.net)

### Developer contact information
- **Email addresses**: j.burchel@crossoverglobal.net

Click **SAVE AND CONTINUE**

## Step 3: Configure Scopes

Click **ADD OR REMOVE SCOPES** and select these scopes:

### Essential Scopes (Required)
- `openid` - OpenID Connect authentication
- `email` - View email address
- `profile` - View basic profile info

### Gmail Scopes
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.compose` - Compose emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify emails

### Calendar Scopes
- `https://www.googleapis.com/auth/calendar` - Full calendar access
- `https://www.googleapis.com/auth/calendar.events` - Manage events

### Contacts Scopes
- `https://www.googleapis.com/auth/contacts` - Manage contacts
- `https://www.googleapis.com/auth/contacts.readonly` - Read contacts

Click **UPDATE** and then **SAVE AND CONTINUE**

## Step 4: Test Users (Not Required for Internal Apps)

Since you selected "Internal" user type, this step is automatically skipped. All users in your crossoverglobal.net organization can access the app without being explicitly added as test users.

Click **SAVE AND CONTINUE**

## Step 5: Create OAuth2 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Select **Application type**: Web application
4. **Name**: Mobilize CRM Web Client

### Authorized JavaScript origins
Add these URLs:
- http://localhost:8000
- http://127.0.0.1:8000

### Authorized redirect URIs
Add these URLs:
- http://localhost:8000/auth/google/callback
- http://127.0.0.1:8000/auth/google/callback
- http://localhost:8000/accounts/google/login/callback/
- http://127.0.0.1:8000/accounts/google/login/callback/

Click **CREATE**

## Step 6: Save Your Credentials

After creation, you'll see a popup with your credentials:

- **Client ID**: (copy this)
- **Client Secret**: (copy this)

**IMPORTANT**: Save these immediately!

## Step 7: Update Your .env File

Update your `.env` file with the new credentials:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-new-client-id-here
GOOGLE_CLIENT_SECRET=your-new-client-secret-here
```

## Step 8: Later - Add Production URLs

When you deploy to Railway, come back and add these URLs:

### Authorized JavaScript origins
- https://your-app.railway.app
- https://your-custom-domain.com

### Authorized redirect URIs
- https://your-app.railway.app/auth/google/callback
- https://your-app.railway.app/accounts/google/login/callback/
- https://your-custom-domain.com/auth/google/callback
- https://your-custom-domain.com/accounts/google/login/callback/

## Verification Requirements

**Internal apps are exempt from verification!** Since you selected "Internal" user type:
- No verification required regardless of user count
- All sensitive scopes available immediately
- No need to stay in "Testing" mode
- App can be published to "Production" status immediately

## Troubleshooting

### Common Issues

1. **"Access blocked" error**
   - Make sure you're logged in with a crossoverglobal.net email address
   - Only organization members can access internal apps

2. **"Redirect URI mismatch"**
   - Ensure the exact URI is in your OAuth client settings
   - Check for trailing slashes
   - Verify http vs https

3. **"Scope not authorized"**
   - Go back to OAuth consent screen
   - Make sure all required scopes are added

## Quick Links

- [Google Cloud Console](https://console.cloud.google.com/projectselector2/home/dashboard?project=mobilize-crm-1750430768)
- [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent?project=mobilize-crm-1750430768)
- [Credentials Page](https://console.cloud.google.com/apis/credentials?project=mobilize-crm-1750430768)

## Notes

- Keep your Client Secret secure - never commit it to Git
- You can regenerate the secret if it's ever compromised
- The Client ID is safe to expose (it's visible in browser requests)