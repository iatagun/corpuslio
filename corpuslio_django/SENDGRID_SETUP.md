# SendGrid Setup Guide for CorpusLIO

## Why SendGrid?
- **Free Tier:** 100 emails/day forever (enough for small-medium projects)
- **Professional:** Industry-standard email delivery
- **Analytics:** Track open rates, click rates, bounces
- **API-First:** Easy integration with Django
- **Reliable:** 99%+ delivery rate

---

## Step 1: Create SendGrid Account

1. **Sign up:** https://signup.sendgrid.com/
   - Use your email (e.g., `ilker.atagun@gmail.com`)
   - Choose "Free" plan (100 emails/day)

2. **Verify your email** (SendGrid will send verification email)

3. **Complete onboarding:**
   - Skip "Sender Authentication" for now (we'll do it later)
   - Choose "I'm using SMTP" when asked

---

## Step 2: Create API Key

1. **Navigate to Settings → API Keys**
   - https://app.sendgrid.com/settings/api_keys

2. **Create API Key:**
   - Click "Create API Key"
   - Name: `CorpusLIO Production`
   - Permissions: **Full Access** (or "Restricted Access" → Mail Send only)
   - Click "Create & View"

3. **IMPORTANT:** Copy API key IMMEDIATELY!
   ```
   SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   - You can only see it once
   - Save it to your password manager

---

## Step 3: Configure Django

### 3.1 Update `.env` File

Open `corpuslio_django/.env` and paste your API key:

```bash
# SendGrid Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.paste_your_api_key_here
DEFAULT_FROM_EMAIL=CorpusLIO <noreply@corpuslio.com>
```

**Note:** `EMAIL_HOST_USER` must be literally `apikey` (not your email)

### 3.2 Update Sender Email (Optional)

If you own a domain (e.g., `corpuslio.com`):
```bash
DEFAULT_FROM_EMAIL=CorpusLIO <noreply@corpuslio.com>
```

If you don't have a domain yet:
```bash
DEFAULT_FROM_EMAIL=CorpusLIO <your-email@gmail.com>
```

---

## Step 4: Verify Sender Identity

SendGrid requires sender verification (anti-spam measure).

### Option A: Single Sender Verification (Quick)

1. **Go to Settings → Sender Authentication → Single Sender Verification**
   - https://app.sendgrid.com/settings/sender_auth/senders

2. **Create New Sender:**
   - From Name: `CorpusLIO`
   - From Email: `your-email@gmail.com` (or your domain email)
   - Reply To: Same as From Email
   - Company: `CorpusLIO`
   - Address: Your address
   - Click "Create"

3. **Verify Email:**
   - SendGrid sends verification email
   - Click verification link

4. **Update `.env`:**
   ```bash
   DEFAULT_FROM_EMAIL=CorpusLIO <your-verified-email@gmail.com>
   ```

### Option B: Domain Authentication (Professional - for custom domain)

Only if you own `corpuslio.com`:

1. **Go to Settings → Sender Authentication → Domain Authentication**
   - https://app.sendgrid.com/settings/sender_auth/domains

2. **Add DNS records** (provided by SendGrid) to your domain registrar

3. **Verify domain** (takes 24-48 hours)

4. **Use domain email:**
   ```bash
   DEFAULT_FROM_EMAIL=CorpusLIO <noreply@corpuslio.com>
   ```

---

## Step 5: Test Email Integration

### 5.1 Restart Django Server

```powershell
# Stop current server (Ctrl+C or kill process)
Get-Process python | Stop-Process -Force

# Start with new .env settings
cd corpuslio_django
python manage.py runserver
```

### 5.2 Test Email Sending

**Method 1: Via Web UI**
1. Register new user: http://127.0.0.1:8000/tr/auth/register/
2. Check your REAL inbox (e.g., Gmail)
3. Click verification link

**Method 2: Via Django Shell**
```powershell
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test Email', 'Bu bir test emailidir.', 'noreply@corpuslio.com', ['your-email@gmail.com'], fail_silently=False); print('Email gönderildi!')"
```

**Expected Result:**
- Email arrives in your inbox within 30 seconds
- Check spam folder if not in inbox

---

## Step 6: Monitor Email Activity

1. **Dashboard:** https://app.sendgrid.com/
   - View sent emails, delivery rate, opens, clicks

2. **Activity Feed:**
   - https://app.sendgrid.com/email_activity
   - See detailed logs of each email

3. **Daily Quota:**
   - Free: 100 emails/day
   - Upgrade if you need more

---

## Troubleshooting

### Issue 1: "Authentication failed"
**Cause:** Wrong API key or username

**Solution:**
- Verify `EMAIL_HOST_USER=apikey` (literal string, not your email)
- Re-create API key if needed
- Check for typos in API key

### Issue 2: "Sender address not verified"
**Cause:** Sender email not verified in SendGrid

**Solution:**
- Complete Single Sender Verification (Step 4)
- Wait for verification email
- Update `DEFAULT_FROM_EMAIL` to match verified address

### Issue 3: "Connection timeout"
**Cause:** Firewall blocking port 587

**Solution:**
- Check firewall settings
- Try port 2525: `EMAIL_PORT=2525`
- Contact your hosting provider

### Issue 4: Emails go to spam
**Cause:** No domain authentication

**Solution:**
- Complete Domain Authentication (Step 4, Option B)
- Add SPF/DKIM records
- Avoid spam trigger words ("Free", "Click here", etc.)

---

## Production Checklist

Before deploying to production:

- [x] SendGrid account created
- [x] API key generated and saved
- [x] Sender identity verified
- [ ] `.env` configured with real values
- [ ] `.env` added to `.gitignore` (check!)
- [ ] Test email sent successfully
- [ ] Domain authentication configured (optional but recommended)
- [ ] Rate limiting enabled (`RATELIMIT_ENABLE=True`)
- [ ] DEBUG=False in production
- [ ] SECRET_KEY changed to new random value

---

## Cost Estimate

### Free Tier (Current)
- **100 emails/day** = 3,000 emails/month
- **Forever free**
- Good for: 50-100 active users

### Paid Plans (If you grow)
- **Essentials ($15/month):** 50,000 emails/month
- **Pro ($60/month):** 100,000 emails/month
- **Premier ($custom):** Unlimited

---

## Alternative: Gmail SMTP (NOT Recommended for Production)

If you want to test quickly without SendGrid:

```bash
# .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # NOT your real password!
DEFAULT_FROM_EMAIL=CorpusLIO <your-email@gmail.com>
```

**Gmail App Password Setup:**
1. Enable 2FA: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Use 16-char password (e.g., `abcd efgh ijkl mnop`)

**Limitations:**
- 500 emails/day limit
- Less reliable delivery
- May be flagged as spam
- Not suitable for professional use

---

## Next Steps

After email verification works:

1. **Test complete workflow:**
   - Register → Receive email → Verify → Login

2. **Enable rate limiting:**
   ```bash
   # .env
   RATELIMIT_ENABLE=True
   ```

3. **Deploy to production:**
   - Use `settings_prod.py`
   - Set `DEBUG=False`
   - Configure domain (e.g., corpuslio.com)

4. **Monitor email deliverability:**
   - Check SendGrid dashboard daily
   - Adjust templates if emails go to spam

---

## Support

- **SendGrid Docs:** https://docs.sendgrid.com/
- **Django Email Docs:** https://docs.djangoproject.com/en/stable/topics/email/
- **CorpusLIO Issues:** Open GitHub issue if problems persist
