# Google Cloud Console Configuration Guide for Gemini API

This guide walks through configuring Google Cloud Console to enable paid-tier Gemini API access for Otto, specifically for embedding operations.

## Overview

**Problem**: API keys hitting free-tier quota limits despite billing claims
**Solution**: Ensure API keys are associated with a billing-enabled Google Cloud project with proper API enablement and quota configuration

---

## Step 1: Verify Current API Key Configuration

### 1.1 Identify Which Project Your API Keys Belong To

1. Go to: https://console.cloud.google.com/apis/credentials
2. Log in with your Google account
3. **Check the project selector** (top left, next to "Google Cloud")
   - Note which project is currently selected
   - Click the dropdown to see all available projects
4. Find your API keys in the credentials list:
   - Look for `AIzaSyBsh8J4mbuLjnqDwZiTp3gS8j_5RGjMgmI`
   - Look for `AIzaSyDVIuMzVwfJpu39mFi2NKRG-9eUO320NdQ`
5. **Click on each API key** to see its details
   - Note which project it belongs to
   - Check "API restrictions" section - is it restricted to specific APIs?

### 1.2 Key Information to Record

For each API key, note:
- Project name
- Project ID
- API restrictions (if any)
- Created date

---

## Step 2: Verify Billing Configuration

### 2.1 Check If Project Has Billing Enabled

1. Go to: https://console.cloud.google.com/billing
2. You'll see a list of billing accounts and linked projects
3. **Find your project** (the one containing your API keys)
4. Check if it shows:
   - ✅ **"Billing enabled"** - Good, proceed to Step 3
   - ❌ **"No billing account"** - Need to link billing account (see 2.2)
   - ⚠️ **"Billing account closed"** - Need to activate billing account

### 2.2 Link Billing Account to Project (if needed)

If your project doesn't have billing enabled:

1. Go to: https://console.cloud.google.com/billing/linkedaccount
2. Select your project from dropdown
3. Click "Link a billing account"
4. Choose an existing billing account or create new one:
   - To create new: Click "Create billing account"
   - Enter billing information (credit card, address)
   - Accept terms and create

**Important**: After linking, it may take 5-15 minutes for billing to fully activate.

### 2.3 Verify Billing Account Status

1. Go to: https://console.cloud.google.com/billing/accounts
2. Find your billing account
3. Verify:
   - Status: "Active" (not "Closed" or "Suspended")
   - Payment method: Valid credit card or payment method configured
   - No overdue invoices or payment issues

---

## Step 3: Enable Generative Language API

The Generative Language API must be explicitly enabled for embedding operations.

### 3.1 Enable the API

1. Go to: https://console.cloud.google.com/apis/library
2. **Ensure correct project is selected** (top left dropdown)
3. Search for: **"Generative Language API"**
4. Click on "Generative Language API" in results
5. Click the blue **"ENABLE"** button
6. Wait for confirmation (usually takes 10-30 seconds)

### 3.2 Verify API is Enabled

1. Go to: https://console.cloud.google.com/apis/dashboard
2. **Ensure correct project is selected**
3. Look for "Generative Language API" in the enabled APIs list
4. If you see it listed, it's successfully enabled

**Alternative verification**:
- Go to: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com
- Should show "API enabled" status

---

## Step 4: Check and Configure Quotas

This is the most critical step - verifying your quotas are set to paid tier, not free tier.

### 4.1 Navigate to Quotas Page

1. Go to: https://console.cloud.google.com/iam-admin/quotas
2. **Ensure correct project is selected**
3. In the filter/search box, type: `generativelanguage.googleapis.com/embed_content`

### 4.2 Check Embedding Quotas

Look for these specific quota metrics:
- `generativelanguage.googleapis.com/embed_content_requests`
- `generativelanguage.googleapis.com/embed_content_free_tier_requests`

**What you should see**:
- ✅ **Paid Tier**: `embed_content_requests` with limit > 0 (e.g., 1500/minute)
- ❌ **Free Tier**: `embed_content_free_tier_requests` with limit = 0

### 4.3 If Showing Free Tier Quotas

**This is your problem!** The API keys are still using free-tier quotas.

**Why this happens**:
- Billing account not properly linked
- API enabled before billing was linked
- Project quota not upgraded to paid tier

**Solutions**:

**Option A: Wait for Propagation** (if you just linked billing)
- Billing changes can take 15-30 minutes to propagate
- Wait and check quotas again in 30 minutes

**Option B: Request Quota Increase**
1. On the quotas page, select the free-tier quota checkbox
2. Click "EDIT QUOTAS" button (top right)
3. Fill out quota increase request form
4. Explain: "Need paid-tier embedding quotas for development work"
5. Submit request (can take 24-48 hours for approval)

**Option C: Create New Project** (fastest solution - see Step 5)

### 4.4 Verify Quota Limits

Once you have paid-tier quotas, verify the limits:
- Embeddings per minute: Should be at least 1,500
- Embeddings per day: Should be at least 1,500
- If limits show as "0", you're still on free tier

---

## Step 5: Create New Project with Billing (Recommended)

If your current API keys are stuck on free tier, the fastest solution is to create a fresh project with billing from the start.

### 5.1 Create New Project

1. Go to: https://console.cloud.google.com/projectcreate
2. Enter project details:
   - **Project name**: "Otto Development" (or your choice)
   - **Organization**: Select your organization (if applicable)
   - **Location**: Leave as default or select organization
3. Click **"CREATE"**
4. Wait for project creation (10-30 seconds)

### 5.2 Enable Billing for New Project

1. With new project selected, go to: https://console.cloud.google.com/billing/linkedaccount
2. Select your new project
3. Click "Link a billing account"
4. Choose your active billing account
5. Confirm linking

### 5.3 Enable Generative Language API

1. Go to: https://console.cloud.google.com/apis/library
2. **Verify new project is selected** (top left)
3. Search for "Generative Language API"
4. Click on it and click **"ENABLE"**
5. Wait for confirmation

### 5.4 Create New API Key

1. Go to: https://console.cloud.google.com/apis/credentials
2. **Verify new project is selected**
3. Click **"+ CREATE CREDENTIALS"** (top)
4. Select **"API key"**
5. New API key will be generated and displayed
6. **Copy the API key immediately** (you'll need this)
7. Click "RESTRICT KEY" (recommended for security)

### 5.5 Restrict API Key (Security Best Practice)

1. On the API key details page:
2. Under "API restrictions":
   - Select "Restrict key"
   - Check only: "Generative Language API"
3. Under "Application restrictions" (optional):
   - Can restrict by IP address if needed
   - For local development, can leave as "None"
4. Click **"SAVE"**

### 5.6 Verify New Key Has Paid Quotas

1. Go to: https://console.cloud.google.com/iam-admin/quotas
2. Search for: `generativelanguage.googleapis.com/embed_content`
3. Verify you see **paid-tier quotas** (not free-tier):
   - Should show limits > 0 (e.g., 1500/minute)
   - Should NOT show "free_tier" in metric names

### 5.7 Update Otto Configuration

1. Open: `C:\otto\Otto\django\.env`
2. Update the GEMINI_API_KEY line:
   ```
   GEMINI_API_KEY=<your-new-api-key-here>
   ```
3. Save the file
4. Restart Django server and Celery worker (if running)

---

## Step 6: Test the Configuration

### 6.1 Test with Simple API Call

You can test the new API key with a simple curl command:

```bash
# Test Gemini model access (should work with free or paid tier)
curl -X GET "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash?key=YOUR_API_KEY"

# Test embedding access (requires paid tier)
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"models/embedding-001","content":{"parts":[{"text":"Hello world"}]}}'
```

**Expected results**:
- First command: Should return model details (JSON)
- Second command:
  - ✅ Paid tier: Returns embedding values (array of numbers)
  - ❌ Free tier: Returns 429 error with quota exceeded message

### 6.2 Test with Otto Application

Run the test suite again:

```bash
cd C:\otto\Otto\django
../venv/Scripts/python.exe -m pytest tests/chat/test_answer_sources.py -v --tb=short
```

**Expected results**:
- ✅ Should process Wikipedia URL and generate embeddings successfully
- ✅ Test should run without quota errors
- ❌ If still fails with 429 error, repeat Step 4 to verify quotas

---

## Step 7: Monitoring and Usage

### 7.1 Monitor API Usage

1. Go to: https://console.cloud.google.com/apis/dashboard
2. Select your project
3. Click on "Generative Language API"
4. View usage charts:
   - Requests over time
   - Errors
   - Latency

### 7.2 Check Quota Usage

1. Go to: https://ai.google.dev/usage (requires sign-in)
2. Or go to: https://console.cloud.google.com/iam-admin/quotas
3. Filter for: `generativelanguage.googleapis.com`
4. Monitor current usage vs. limits

### 7.3 Set Up Budget Alerts (Recommended)

1. Go to: https://console.cloud.google.com/billing/budgets
2. Click "CREATE BUDGET"
3. Configure:
   - Budget name: "Gemini API Monthly Budget"
   - Projects: Select your project
   - Amount: Set your monthly budget (e.g., $50)
   - Threshold rules: Alert at 50%, 90%, 100%
4. Save budget

---

## Common Issues and Solutions

### Issue: "Permission denied" when accessing console

**Solution**: Ensure you're logged in with the correct Google account that has Owner or Editor role on the project.

### Issue: Can't find API keys in credentials

**Solution**: Check all projects - API keys might be in a different project than you expect. Use project selector dropdown.

### Issue: Billing account shows "Closed"

**Solution**:
1. Go to billing account details
2. Click "REOPEN ACCOUNT"
3. Update payment method if needed
4. May need to clear any outstanding invoices first

### Issue: Still showing free-tier quotas after linking billing

**Solution**:
1. Wait 30 minutes for propagation
2. Try disabling and re-enabling the Generative Language API
3. Or create a new project (fastest option)

### Issue: API key works for chat but not embeddings

**Solution**: Embeddings require paid tier even if chat works on free tier. Follow quota configuration steps above.

### Issue: 429 errors persist after configuration

**Solution**:
1. Verify correct API key is in .env file
2. Restart Django and Celery completely
3. Check quotas page to confirm paid-tier limits
4. Wait 5-10 minutes after making changes

---

## Cost Estimates

### Embedding API Costs

From Google Cloud pricing (as of documentation):
- **Model**: embedding-001
- **Cost**: $0.00001 per 1000 characters (approximately)
- **Typical usage**: ~10,000 embeddings for full test suite
- **Estimated cost**: ~$0.10-$0.50 for full test suite

### Chat API Costs (Gemini 1.5 Flash)

From test-results.md cost types:
- **Input**: $0.075 per 1M tokens
- **Output**: $0.30 per 1M tokens
- **Typical test run**: ~500K tokens total
- **Estimated cost**: ~$0.10-$0.20 per test run

### Monthly Development Costs

For active Otto development:
- **Testing**: ~$5-10/month
- **Development chat usage**: ~$10-20/month
- **Vector embeddings**: ~$5-10/month
- **Total estimate**: $20-40/month for development

---

## Next Steps After Configuration

1. ✅ Complete Step 1-6 above
2. ✅ Verify API key works with curl test
3. ✅ Update django/.env with new API key
4. ✅ Restart Django and Celery
5. ✅ Run: `pytest tests/chat/test_answer_sources.py -v`
6. ✅ If successful, run full test suite: `pytest tests/chat/ -v`
7. ✅ Update test-results.md with successful results

---

## Support Resources

- **Gemini API Documentation**: https://ai.google.dev/gemini-api/docs
- **Pricing Information**: https://ai.google.dev/pricing
- **Quota Documentation**: https://ai.google.dev/gemini-api/docs/rate-limits
- **Google Cloud Support**: https://cloud.google.com/support
- **API Status Page**: https://status.cloud.google.com/

---

## Security Notes

- **Never commit API keys** to version control
- **Use .env files** for local development (already in .gitignore)
- **Restrict API keys** to only necessary APIs
- **Set budget alerts** to avoid unexpected costs
- **Rotate keys regularly** (every 90 days recommended)
- **Use separate keys** for development vs. production

---

**Created**: 2025-11-03
**Last Updated**: 2025-11-03
**Status**: Ready for use
