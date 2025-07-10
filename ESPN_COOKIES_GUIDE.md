# Getting ESPN Fantasy Football Cookies

To enable ESPN data fetching, you need to provide your ESPN authentication cookies. Here's how to get them:

## Steps to Get Your ESPN Cookies

1. **Log in to ESPN Fantasy Football**
   - Go to https://fantasy.espn.com/football/
   - Sign in with your ESPN account

2. **Open Browser Developer Tools**
   - Chrome/Edge: Press `F12` or right-click → "Inspect"
   - Firefox: Press `F12` or right-click → "Inspect Element"
   - Safari: Enable Developer menu in Preferences → Advanced, then press `Cmd+Option+I`

3. **Navigate to the Application/Storage Tab**
   - In Chrome/Edge: Click "Application" tab
   - In Firefox: Click "Storage" tab
   - In Safari: Click "Storage" tab

4. **Find the Cookies**
   - In the left sidebar, expand "Cookies"
   - Click on `https://fantasy.espn.com`
   - Look for these two cookies:
     - **espn_s2**: A long string (usually 100+ characters)
     - **SWID**: A UUID in curly braces like `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}`

5. **Copy the Cookie Values**
   - Click on each cookie
   - Copy the entire "Value" field

## Alternative Method: Using Network Tab

1. With Developer Tools open, go to the **Network** tab
2. Navigate to your ESPN fantasy league
3. Look for any request to `fantasy.espn.com`
4. Click on the request
5. Go to "Request Headers"
6. Find the "Cookie" header
7. Extract `espn_s2` and `SWID` values from the cookie string

## Using the Cookies in the App

1. Go to the ESPN Leagues page in the Fantasy Football Assistant
2. Click the Settings button for your league
3. Click "Update ESPN Cookies"
4. Paste your cookies:
   - ESPN S2: Paste the espn_s2 value
   - SWID: Paste the SWID value (including the curly braces)
5. Click "Update Cookies"

## Important Notes

- These cookies expire after a few weeks, so you may need to update them periodically
- Keep these cookies private - they provide access to your ESPN account
- The app stores these cookies securely and only uses them for ESPN API requests
- If you get authentication errors, try getting fresh cookies

## Troubleshooting

If player data fetching fails:
1. Ensure you're logged into ESPN in your browser
2. Get fresh cookies
3. Make sure you copied the entire cookie value
4. Check that the SWID includes the curly braces `{}`
5. Try using a different browser if issues persist