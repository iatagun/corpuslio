# Multi-Language Support (i18n) - Implementation Guide

## Overview
OCRchestra now supports **Turkish (Türkçe)** and **English** with seamless language switching.

## Implementation Details

### 1. Django Settings (`settings.py`)
```python
# Available languages
LANGUAGES = [
    ('tr', 'Türkçe'),
    ('en', 'English'),
]

# Default language
LANGUAGE_CODE = 'tr'

# Translation file location
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Enable internationalization
USE_I18N = True
```

### 2. Middleware Configuration
`LocaleMiddleware` added after `SessionMiddleware`:
```python
MIDDLEWARE = [
    # ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n support
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

### 3. URL Configuration
```python
from django.conf.urls.i18n import i18n_patterns

# Language switcher endpoint
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

# All app URLs wrapped in i18n_patterns (adds /tr/ or /en/ prefix)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('corpus.urls')),
    # ...
)
```

### 4. Language Switcher UI
Located in `base.html` header, next to theme switcher:
- **Button**: Displays current language code (TR/EN)
- **Dropdown**: Shows available languages with flag icons
- **Form submission**: Uses Django's built-in `set_language` view

**Features:**
- 🇹🇷 Turkish flag for TR
- 🇬🇧 UK flag for EN
- Active language highlighted
- Click outside to close
- Keyboard accessible

### 5. CSS Styling
Added to `styles.css`:
```css
.language-switcher { position: relative; }
.language-btn { /* Circular button similar to theme switcher */ }
.language-menu { /* Dropdown menu */ }
.language-option { /* Language item */ }
.language-option.active { /* Selected language */ }
```

### 6. JavaScript
Added `toggleLanguageMenu()` function in `base.html`:
- Toggles dropdown visibility
- Closes when clicking outside
- Works alongside theme menu

## How to Use

### For End Users
1. **Desktop**: Click the language button (TR/EN) in top-right header
2. **Select**: Choose desired language from dropdown
3. **Auto-reload**: Page refreshes with selected language
4. **Persistence**: Language preference saved in session

### For Developers

#### Mark strings for translation in Python:
```python
from django.utils.translation import gettext_lazy as _

class MyModel(models.Model):
    name = models.CharField(_("Name"), max_length=100)

def my_view(request):
    message = _("Welcome to OCRchestra")
    return render(request, 'template.html', {'message': message})
```

#### Mark strings for translation in templates:
```html
{% load i18n %}

<h1>{% trans "Welcome" %}</h1>
<p>{% blocktrans %}Hello {{ username }}{% endblocktrans %}</p>
```

#### Generate translation files:
**Note:** Requires `gettext` tools (not available by default on Windows)

```bash
# Create/update message files
python manage.py makemessages -l tr
python manage.py makemessages -l en

# Edit files in locale/tr/LC_MESSAGES/django.po
# Edit files in locale/en/LC_MESSAGES/django.po

# Compile translations
python manage.py compilemessages
```

#### Alternative: Manual Translation Files
Since gettext is not available, you can:
1. Create JSON-based translation dictionaries
2. Use Django's JavaScript i18n catalog
3. Implement client-side translations for dynamic content

## Current State (Week 12)

### ✅ Implemented
- [x] Django i18n framework configured
- [x] Language switcher UI in header
- [x] TR/EN language support enabled
- [x] URL patterns with language prefix (`/tr/...`, `/en/...`)
- [x] Session-based language persistence
- [x] Accessible, keyboard-navigable UI

### ⏳ To Be Completed (Future)
- [ ] Extract all translatable strings from Python code
- [ ] Extract all translatable strings from templates
- [ ] Create Turkish translation files
- [ ] Create English translation files
- [ ] Install gettext tools (Windows: https://mlocati.github.io/articles/gettext-iconv-windows.html)
- [ ] Compile translation messages
- [ ] Test all pages in both languages
- [ ] Add language metadata to API responses
- [ ] Document API language switching (Accept-Language header)

## Testing

### Manual Testing Steps:
1. **Start server**: `python manage.py runserver`
2. **Visit homepage**: `http://localhost:8000/`
3. **Click language switcher**: Top-right corner, next to theme button
4. **Select EN**: Should redirect to `/en/` with English UI
5. **Select TR**: Should redirect to `/tr/` with Turkish UI
6. **Check persistence**: Language should remain after page reload
7. **Test all pages**: Library, Dashboard, Statistics, etc.

### Expected Behavior:
- URL changes from `/` to `/tr/` or `/en/`
- Language button updates (TR ↔ EN)
- Session cookie `django_language` set
- Static content (CSS, JS) remains functional
- CSRF tokens work correctly across language switches

## Troubleshooting

### Issue: "gettext not found"
**Solution**: This is expected on Windows. Follow one of these approaches:
1. **Install GetText**: Download from https://mlocati.github.io/articles/gettext-iconv-windows.html
2. **Use WSL**: `sudo apt-get install gettext` in Ubuntu/WSL
3. **Skip for now**: Language switcher works; translations can be added later

### Issue: "404 on /i18n/setlang/"
**Solution**: Ensure `path('i18n/', include('django.conf.urls.i18n'))` is in `urls.py` **before** `i18n_patterns`.

### Issue: Language dropdown not closing
**Solution**: Check JavaScript console for errors. Ensure `toggleLanguageMenu()` function exists in `base.html`.

### Issue: CSS styles missing
**Solution**: Clear browser cache and check `styles.css` includes `.language-switcher` styles.

## Integration with Existing Features

### Compatible with:
- ✅ Theme switcher (dark/light/auto)
- ✅ User authentication (login/logout)
- ✅ CSRF protection
- ✅ Session management
- ✅ Admin panel
- ✅ API endpoints (via Accept-Language header)

### Future Considerations:
- **Search queries**: Allow searching in both languages
- **Document metadata**: Store language of uploaded documents
- **Analysis results**: Translate frequency/n-gram labels
- **Export files**: Include language metadata in CSV/JSON headers
- **API responses**: Return localized error messages

## Resources

### Django i18n Documentation:
- https://docs.djangoproject.com/en/4.2/topics/i18n/
- https://docs.djangoproject.com/en/4.2/topics/i18n/translation/

### GetText Tools:
- Windows: https://mlocati.github.io/articles/gettext-iconv-windows.html
- Linux: `sudo apt-get install gettext`
- macOS: `brew install gettext`

### Translation Best Practices:
- Use `gettext_lazy` for model fields and class-level strings
- Use `gettext` for dynamic content in views
- Use `{% trans %}` for simple template strings
- Use `{% blocktrans %}` for strings with variables
- Keep UI strings short and context-aware
- Test pluralization rules (Turkish has different plural rules than English)

## Maintenance

### Adding a New Language (e.g., German):
1. Update `settings.py`: `LANGUAGES = [('tr', 'Türkçe'), ('en', 'English'), ('de', 'Deutsch')]`
2. Add flag icon: Update `base.html` flag logic
3. Create message file: `python manage.py makemessages -l de`
4. Translate strings in `locale/de/LC_MESSAGES/django.po`
5. Compile: `python manage.py compilemessages`
6. Test: Visit `/de/` URLs

### Updating Translations:
1. Extract new strings: `python manage.py makemessages -a`
2. Edit `.po` files in `locale/*/LC_MESSAGES/`
3. Compile: `python manage.py compilemessages`
4. Restart server

---

**Week 12 Status**: Language switcher UI implemented ✅  
**Next Step**: Extract and translate all strings (Week 13 or future release)
