# OCRchestra Platform Tutorial - Video Script
**Duration:** 7-8 minutes  
**Target Audience:** Academic researchers, linguistics students, NLP developers  
**Tone:** Professional, educational, welcoming  

---

## SCENE 1: Introduction (0:00 - 0:45)

### [Screen: OCRchestra homepage with hero section]

**Narrator:**  
"Hoş geldiniz! Welcome to OCRchestra - Turkey's national corpus platform for Turkish language research and analysis."

**[Cursor hovers over mission badge: "Eğitim ve Araştırma İçin Ücretsiz Erişim"]**

**Narrator:**  
"OCRchestra provides free access to millions of Turkish text tokens for education and research. Whether you're a linguist, researcher, NLP developer, or student - this platform offers powerful tools for corpus analysis."

**[Scroll through features section showing 6 cards]**

**Narrator:**  
"With advanced search capabilities, statistical analysis, secure data export, and full GDPR compliance - let's explore how to get started."

---

## SCENE 2: Registration & Roles (0:45 - 2:00)

### [Screen: Navigate to Sign Up page]

**Narrator:**  
"First, let's create an account. Click 'Kayıt Ol' in the top-right corner."

**[Cursor clicks Register button]**

**[Screen: Registration form]**

**Narrator:**  
"Fill in your details - username, email, and password. The platform offers multiple access levels based on your needs."

**[Show role comparison table overlay - animated graphic]**

**Visual Overlay:**
```
┌─────────────────┬──────────────┬─────────────────┬──────────────┐
│ ROLE            │ SEARCHES/DAY │ EXPORT QUOTA    │ SPECIAL      │
├─────────────────┼──────────────┼─────────────────┼──────────────┤
│ Anonymous       │ 50           │ -               │ Preview only │
│ Registered      │ 100          │ 5MB/month       │ -            │
│ Verified        │ 500          │ 20MB/month      │ Upload docs  │
│ Developer       │ 2000         │ 100MB/month     │ API access   │
└─────────────────┴──────────────┴─────────────────┴──────────────┘
```

**Narrator:**  
"As a registered user, you get 100 searches per day and 5MB monthly export quota. To become a Verified Researcher with higher quotas and document upload rights, you can apply through your profile settings."

**[Screen: Click consent checkboxes]**

**Narrator:**  
"Notice the KVKK compliance - your data privacy is protected under Turkish and European regulations. Required consents are for basic data processing, while marketing is optional."

**[Screen: Click Register, show success toast]**

---

## SCENE 3: Library & Search (2:00 - 3:30)

### [Screen: Homepage → Click "Kütüphane" in sidebar]

**Narrator:**  
"Now let's explore the corpus library. Here you'll find all available documents."

**[Screen: Library page with filters]**

**Narrator:**  
"Use filters to narrow down by format - TXT, DOCX, PDF, or ePub. Sort by upload date, word count, or processing status."

**[Scroll through document cards]**

**Narrator:**  
"Each document shows metadata like word count, format, and tags. Let's click on one to see details."

**[Screen: Document detail page]**

**Narrator:**  
"The detail page shows full statistics, tags, and preview. Now, let's perform a search."

**[Screen: Search bar at top]**

**Narrator:**  
"Type your query - let's search for 'dil bilim' (linguistics)."

**[Type query, press Enter]**

**Narrator:**  
"The search supports multiple modes:"

**[Click search type dropdown]**

**Visual Overlay - Search Types:**
- **Basit**: Standard text search
- **Regex**: Pattern matching (`.*bilim`, `dil[ie]?`)
- **Fuzzy**: Finds similar words ("oklama" → "okuma")
- **Kollokasyon**: Word co-occurrence analysis

**Narrator:**  
"Results appear in KWIC format - Key Word In Context - showing your search term highlighted with surrounding text."

---

## SCENE 4: Analysis Tools (3:30 - 5:00)

### [Screen: Navigate to Statistics/Dashboard]

**Narrator:**  
"OCRchestra offers four powerful analysis tools. Let's explore them."

### [Screen: Frequency Analysis]

**Narrator:**  
"First, Frequency Analysis. Enter a query or select a collection."

**[Type query, click Analyze]**

**Narrator:**  
"The tool generates a frequency distribution showing the most common words, with options for bar charts, pie charts, and word clouds."

**[Show visualizations switching]**

**Narrator:**  
"Type-Token Ratio (TTR) measures lexical diversity - scores below 0.4 indicate low diversity, while scores above 0.6 show rich vocabulary."

### [Screen: N-gram Analysis]

**Narrator:**  
"Next, N-grams. This finds frequently occurring word sequences."

**[Select bigrams, enter query]**

**Narrator:**  
"Choose bigrams for two-word phrases, trigrams for three-word, up to 5-grams. Results show phrases like 'bu nedenle' (therefore) or 'dil bilim' (linguistics) with occurrence counts."

### [Screen: Collocation Analysis]

**Narrator:**  
"Collocation analysis discovers words that frequently appear together."

**[Enter keyword: "kahve"]**

**Narrator:**  
"For example, searching 'kahve' (coffee) reveals collocates like 'türk kahvesi' (Turkish coffee), 'kahve içmek' (drink coffee), with statistical measures like Mutual Information and T-score."

### [Screen: KWIC Concordance]

**Narrator:**  
"Finally, concordance view shows your keyword in context, with adjustable left and right context windows from 5 to 50 words."

---

## SCENE 5: Data Export (5:00 - 6:00)

### [Screen: Click Export button on analysis page]

**Narrator:**  
"Ready to download your results? OCRchestra supports three export formats."

**[Show export options dialog]**

**Visual Overlay - Export Formats:**
1. **CSV** - Spreadsheet compatible, with watermark
2. **JSON** - Machine-readable, with full metadata
3. **Excel** - Three sheets: Results, Statistics, Citation

**Narrator:**  
"Each export includes an academic citation watermark for proper attribution."

**[Select CSV, click Export]**

**Narrator:**  
"Large exports are processed in the background. You'll receive a notification when ready."

**[Screen: Export notification appears]**

**[Click Download]**

**Narrator:**  
"The CSV file includes your data with a comment header containing:"

**[Open CSV file in viewer]**

```csv
# OCRchestra Export
# Date: 2026-01-28
# User: researcher@example.com
# Query: "dil bilim"
# Citation: OCRchestra Platformu. (2026). Türkçe Korpus Veritabanı...
```

**Narrator:**  
"Remember your monthly quota - registered users have 5MB, verified researchers 20MB, and developers 100MB."

---

## SCENE 6: Collections (6:00 - 6:45)

### [Screen: Navigate to Collections]

**Narrator:**  
"Collections let you organize documents into custom sub-corpora."

**[Click Create Collection]**

**Narrator:**  
"Give it a name, description, and choose visibility:"

**Visual Overlay:**
- 🔒 **Private** - Only you
- 👥 **Shared** - Specific users
- 🌐 **Public** - Everyone

**[Create collection, add documents]**

**Narrator:**  
"Add documents by searching and selecting. Collections can be used in searches with namespace syntax:"

**[Type in search: `collection:my-collection dilbilim`]**

**Narrator:**  
"This searches only within your custom collection."

---

## SCENE 7: Privacy & GDPR Compliance (6:45 - 7:15)

### [Screen: Navigate to Profile → Privacy Settings]

**Narrator:**  
"OCRchestra takes data privacy seriously. Under KVKK and GDPR, you have seven fundamental rights:"

**Visual Overlay - Your Rights:**
1. ✅ **Access** - View your data
2. ✅ **Portability** - Download your data
3. ✅ **Correction** - Fix inaccuracies
4. ✅ **Deletion** - Request removal
5. ✅ **Objection** - Oppose processing
6. ✅ **Restriction** - Limit usage
7. ✅ **Withdraw** - Revoke consent

**Narrator:**  
"You can manage consents, view processing history, and request data export or account deletion - with a 7-day cancellation window for safety."

**[Screen: Consent management switches]**

**Narrator:**  
"Required consent is only for core platform functionality. Marketing, third-party sharing, and analytics are always optional."

---

## SCENE 8: Advanced Features (7:15 - 7:45)

### [Screen: Show API documentation page]

**Narrator:**  
"For developers, OCRchestra offers a REST API with endpoints for search, analysis, export, and collections."

**[Scroll through API docs]**

**Narrator:**  
"Rate-limited at 100 requests per minute, with code examples in Python, JavaScript, and R."

**[Show code example]**

```python
import requests

api_key = "YOUR_API_KEY"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(
    "https://api.ocrchestra.tr/v1/search",
    params={"q": "dilbilim", "limit": 100},
    headers=headers
)
```

**Narrator:**  
"Apply for API access through your profile settings."

---

## SCENE 9: Conclusion (7:45 - 8:00)

### [Screen: Back to homepage]

**Narrator:**  
"That's CorpusLIO - your comprehensive Turkish corpus platform."

**[Show use cases section with 4 cards]**

**Narrator:**  
"Join thousands of linguists, researchers, NLP developers, and educators advancing Turkish language research."

**[Show academic citation section]**

**Narrator:**  
"Start exploring today at corpuslio.tr - and don't forget to cite the platform in your publications."

**[Screen: Contact information and social media icons appear]**

**Narrator:**  
"Questions? Contact us at support@corpuslio.tr or join our community on GitHub and Twitter."

**[Fade to CorpusLIO logo]**

**Narrator:**  
"İyi araştırmalar! Happy researching!"

**[End screen: CorpusLIO logo + website URL]**

---

## POST-PRODUCTION NOTES

### Screen Recording Checklist:
- [ ] Use 1920x1080 resolution
- [ ] Enable cursor highlighting
- [ ] Disable notifications/popups
- [ ] Use test account: demo@corpuslio.tr
- [ ] Pre-populate sample data (documents, collections)
- [ ] Test all features before recording
- [ ] Record in quiet environment

### Video Editing:
- **Intro**: 5 seconds with logo animation
- **Outro**: 5 seconds with credits
- **Transitions**: Smooth crossfades (0.5s)
- **Annotations**: Arrow callouts for UI elements
- **Overlays**: Use branded color scheme (#4f46e5, #7c3aed)
- **Background Music**: Subtle, non-intrusive, 30% volume
- **Subtitles**: Turkish and English SRT files

### Visual Overlays Design:
- **Tables**: Use platform color scheme (purple gradient)
- **Icons**: Material Icons consistent with UI
- **Highlights**: Yellow circle for cursor focus areas
- **Tooltips**: Animated popups explaining features

### Voiceover:
- **Language**: Bilingual (Turkish primary, English subtitles)
- **Pace**: Moderate (120-140 words/min)
- **Tone**: Friendly professor / helpful guide
- **Equipment**: Professional microphone (eliminate echo)

### Publishing:
- **YouTube**: Upload with TR/EN subtitles, hashtags #corpuslinguistics #NLP #Turkish
- **Platform**: Embed on homepage
- **Formats**: 1080p60, 720p60, 480p
- **Thumbnail**: Custom designed with platform logo + "Tutorial" text

### Alternative Versions:
1. **Quick Start** (2 min): Registration + Basic Search
2. **Analysis Deep Dive** (5 min): All 4 analysis tools
3. **API Tutorial** (4 min): REST API for developers
4. **Admin Guide** (6 min): Document upload, tagging, management

---

## SCRIPT VARIATIONS

### Turkish Version Script:
```
[SAHNE 1: Giriş]
"Merhaba! OCRchestra'ya hoş geldiniz - Türkiye'nin ulusal Türkçe korpus platformuna..."
```

### English Version Script:
```
[SCENE 1: Introduction]
"Welcome! This is OCRchestra - Turkey's national corpus platform for Turkish language research..."
```

### Student-Friendly Version:
- Simpler language
- More examples
- Slower pace
- Focus on basic features (search, view, export)

### Researcher-Focused Version:
- Emphasize citations
- Statistical methods explanation
- GDPR compliance details
- API integration examples

---

**Estimated Production Time:**
- Script finalization: 2 hours
- Screen recording: 3 hours (multiple takes)
- Video editing: 6 hours
- Voiceover recording: 2 hours
- Subtitle creation: 2 hours
- Review & revisions: 3 hours
- **Total**: ~18 hours

**Tools Needed:**
- **Screen Recording**: OBS Studio (free)
- **Video Editing**: DaVinci Resolve (free) or Adobe Premiere Pro
- **Voiceover**: Audacity (free) or Adobe Audition
- **Subtitles**: Subtitle Edit (free)
- **Graphics**: Canva or Adobe Illustrator

**Script Status**: ✅ Ready for production (Week 12 complete)
