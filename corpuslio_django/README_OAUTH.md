Google OAuth (django-allauth) setup

1) Ensure package installed:

   pip install django-allauth

2) Add Google OAuth credentials (in your .env or environment):

   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   DJANGO_SITE_ID=1

3) Run migrations:

   python manage.py migrate

4) Create or verify Site in admin:
   - Admin -> Sites -> ensure your domain is present and its ID matches `SITE_ID`.

5) Create Social Application (one of two ways):

   A) Via Django admin:
      - Admin -> Social applications -> Add
      - Provider: Google
      - Name: Google
      - Client id: (from Google Cloud)
      - Secret key: (from Google Cloud)
      - Sites: add your site

   B) Using the management command (automated):

      Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in settings (via env).
      Then run:

      python manage.py create_social_app

6) Configure Google Cloud Console:
   - Create OAuth 2.0 Client ID
   - Authorized redirect URIs: http://localhost:8000/accounts/google/login/callback/

7) Test:
   - Start server: `python manage.py runserver`
   - Visit the login page and click "Google ile Giriş" or `/accounts/google/login/`

Notes:
- `ACCOUNT_EMAIL_VERIFICATION` is set to `optional` in settings; adjust as needed.
- If you want only signups via Google, further settings in allauth can be configured.
