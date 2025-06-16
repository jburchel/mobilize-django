# Google OAuth Setup Instructions

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Project name: "Mobilize CRM" (or similar)

## Step 2: Enable Required APIs

Navigate to "APIs & Services" > "Library" and enable:
- Google+ API
- Gmail API
- Google Calendar API
- People API (for contacts)

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Application type: "Web application"
4. Name: "Mobilize CRM Local Dev"

## Step 4: Configure Redirect URIs

Add these authorized redirect URIs:
- `http://localhost:8000/auth/google-auth-callback/`
- `http://127.0.0.1:8000/auth/google-auth-callback/`

## Step 5: Update .env File

Replace these values in your `.env` file:
```
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
```

## Step 6: Configure Domain Restriction (Optional)

In Google Cloud Console:
1. Go to "OAuth consent screen"
2. Under "Authorized domains", add: `crossoverglobal.net`
3. This provides an additional layer of domain restriction

## Important Notes

- The app now restricts access to @crossoverglobal.net email addresses only
- Google logo display issue has been fixed with inline SVG
- Once OAuth is properly configured, users will be able to sign in with their Crossover Global Google accounts

## Testing

After setup, test with:
1. A @crossoverglobal.net email (should work)
2. A non-@crossoverglobal.net email (should show access denied message)