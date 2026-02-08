# Corpus Platform Implementation Roadmap

**Project:** OCRchestra → National Educational Corpus Platform  
**Start Date:** February 2026  
**Timeline:** 12 weeks (3 months) to MVP  
**Status:** 🟢 IN PROGRESS

---

## Overview

Transform OCRchestra from a general OCR/analysis tool into a **national-scale corpus query platform** following the architectural vision defined in `CORPUS_PLATFORM_VISION.md`.

---

## Phase 1: Foundation & Access Control (Weeks 1-3)

### **Week 1: User Roles & Permissions System** ✅ CURRENT

**Goals:**
- Implement 5-tier role system
- Create custom permission decorators
- Update user registration flow

**Tasks:**
1. ✅ Create User Role model (extends Django User)
2. ✅ Define permission groups (anonymous, registered, verified, developer, admin)
3. ✅ Build role verification workflow
4. ✅ Create permission decorators (`@role_required`, `@verified_researcher_only`)
5. ✅ Update templates to show role-specific content

**Deliverables:**
- `corpus/models.py`: UserProfile model with role field
- `corpus/permissions.py`: Enhanced permission system
- `corpus/decorators.py`: Role-based view decorators
- Migration files

**Testing:**
- [ ] Anonymous users see limited results
- [ ] Registered users can export CSV
- [ ] Verified researchers access API
- [ ] Admins have full control

---

### **Week 2: Rate Limiting & Audit Logging**

**Goals:**
- Prevent abuse with rate limits
- Track all queries and exports
- Build audit trail

**Tasks:**
1. [ ] Install `django-ratelimit` package
2. [ ] Configure rate limits per role
3. [ ] Create QueryLog model (user, query, timestamp, results_count)
4. [ ] Create ExportLog model (user, exported_data, format, size)
5. [ ] Build admin dashboard for audit logs
6. [ ] Implement IP-based rate limiting for anonymous users

**Deliverables:**
- `corpus/models.py`: QueryLog, ExportLog
- `corpus/middleware.py`: Rate limiting middleware
- `corpus/admin.py`: Log inspection interface
- Settings update with rate limit configs

**Testing:**
- [ ] Anonymous user hits 10 queries/hour limit
- [ ] Registered user tracked in QueryLog
- [ ] Admin can review all searches

---

### **Week 3: Export System with Watermarking**

**Goals:**
- Controlled export with attribution
- Watermarked CSV/JSON/CoNLL-U exports
- Export quota enforcement

**Tasks:**
1. [ ] Build ExportService class (CSV, JSON, CoNLL-U formats)
2. [ ] Implement watermark injection (header/footer with citation)
3. [ ] Create export quota tracking (MB per month)
4. [ ] Add export download view (requires login)
5. [ ] Add "Export concordance" button to KWIC results
6. [ ] Email notification on export completion

**Deliverables:**
- `corpus/services/export_service.py`
- `corpus/views/export_views.py`
- Templates: `export_download.html`, `export_history.html`
- Celery task for large exports

**Testing:**
- [ ] Export CSV with watermark + citation
- [ ] Quota enforced (5MB/month for registered users)
- [ ] Export history visible in user dashboard

---

## Phase 2: Data Model & Format Support (Weeks 4-6)

### **Week 4: CoNLL-U Format Support**

**Goals:**
- Store and serve dependency annotations
- Enable dependency queries

**Tasks:**
1. [ ] Extend Analysis model to support CoNLL-U
2. [ ] Create CoNLL-U parser/serializer
3. [ ] Build dependency query interface
4. [ ] Add dependency visualization (tree diagram)
5. [ ] Update export to include CoNLL-U format option

**Deliverables:**
- `ocrchestra/parsers/conllu_parser.py`
- `corpus/views/dependency_view.py`
- Template with interactive dependency tree (D3.js or similar)
- Updated analysis storage schema

**Testing:**
- [ ] Upload CoNLL-U file → visualize tree
- [ ] Query: "find all objects of verb 'yazmak'"
- [ ] Export results as CoNLL-U

---

### **Week 5: VRT Format & Metadata Enhancement**

**Goals:**
- Support corpus linguistics standard (VRT)
- Rich metadata for filtering

**Tasks:**
1. [ ] Create VRT parser
2. [ ] Extend Document model with structured metadata (genre, year, source, license)
3. [ ] Build metadata filtering UI (faceted search)
4. [ ] Implement subcorpus comparison tool
5. [ ] Add metadata export (JSON schema)

**Deliverables:**
- `ocrchestra/parsers/vrt_parser.py`
- `corpus/models.py`: DocumentMetadata model
- `corpus/views/metadata_views.py`
- Template: `subcorpus_compare.html`

**Testing:**
- [ ] Filter: "only educational texts from 2020-2025"
- [ ] Compare: word frequency in textbooks vs. news
- [ ] Export metadata as JSON

---

### **Week 6: Privacy & Anonymization**

**Goals:**
- Mask personal identifiers
- KVKK/GDPR compliance

**Tasks:**
1. [ ] Implement NER-based masking (person names, IDs, emails)
2. [ ] Add privacy_status field to Document
3. [ ] Build anonymization report (what was masked)
4. [ ] Create data retention policy settings
5. [ ] Implement user data deletion (GDPR "right to be forgotten")

**Deliverables:**
- `ocrchestra/privacy/anonymizer.py`
- `corpus/management/commands/anonymize_corpus.py`
- Privacy policy page
- User data export/deletion endpoints

**Testing:**
- [ ] Upload text with "Ahmet Yılmaz" → masked to [PERSON]
- [ ] User deletes account → all personal data removed
- [ ] Anonymization report shows masked entities

---

## Phase 3: API & Advanced Features (Weeks 7-9)

### **Week 7: REST API with Django REST Framework**

**Goals:**
- Programmatic access for developers
- API key management
- API rate limiting

**Tasks:**
1. [ ] Install Django REST Framework
2. [ ] Create API endpoints:
   - `/api/v1/search/` (concordance query)
   - `/api/v1/documents/` (list with metadata filter)
   - `/api/v1/frequency/` (word/lemma frequency)
   - `/api/v1/export/` (request export)
3. [ ] Implement API key authentication
4. [ ] API-specific rate limits (1000 requests/day for standard tier)
5. [ ] API documentation (Swagger/OpenAPI)

**Deliverables:**
- `api/` app with serializers and viewsets
- `api/authentication.py`: API key auth
- `api/throttling.py`: Custom rate limits
- Auto-generated API docs at `/api/docs/`

**Testing:**
- [ ] POST /api/v1/search/ → concordance JSON
- [ ] API key authentication works
- [ ] Rate limit enforced (HTTP 429 after 1000 calls)

---

### **Week 8: User Dashboard & Statistics**

**Goals:**
- User-facing control panel
- Query history, export history
- Usage statistics

**Tasks:**
1. [ ] Create dashboard view
2. [ ] Display query history (last 100 searches)
3. [ ] Show export quota usage (5MB / 100MB used)
4. [ ] Personal collections (bookmark documents)
5. [ ] Saved queries (reusable searches)

**Deliverables:**
- `corpus/views/dashboard_views.py`
- Templates: `dashboard.html`, `query_history.html`, `collections.html`
- Bookmark/save functionality

**Testing:**
- [ ] User sees query history
- [ ] Export quota progress bar accurate
- [ ] Saved queries loadable with one click

---

### **Week 9: Advanced Search & CQP-Style Queries**

**Goals:**
- Pattern matching (e.g., `[pos="ADJ"] [pos="NOUN"]`)
- Regex over annotations
- Complex filters

**Tasks:**
1. [ ] Implement CQP-like query parser
2. [ ] Build pattern matching engine
3. [ ] Add advanced search UI (query builder)
4. [ ] Support regex in lemma/POS fields
5. [ ] Add query syntax help/tutorial

**Deliverables:**
- `ocrchestra/query_parser.py`
- `corpus/views/advanced_search.py`
- Template: `advanced_search.html` with query builder
- Tutorial page: "How to search the corpus"

**Testing:**
- [ ] Query: `[pos="ADJ"] [pos="NOUN"]` → finds "güzel kitap"
- [ ] Regex: `lemma="git.*"` → matches "gitti, gidiyor, gittim"
- [ ] Invalid syntax → helpful error message

---

## Phase 4: Compliance, Security & Polish (Weeks 10-12)

### **Week 10: Security Hardening**

**Goals:**
- Production-ready security
- Penetration testing
- HTTPS enforcement

**Tasks:**
1. [ ] Enable Django security settings (SECURE_SSL_REDIRECT, CSRF protection)
2. [ ] Implement Content Security Policy headers
3. [ ] Add CAPTCHA to registration (prevent bots)
4. [ ] Rate limiting on auth endpoints (prevent brute force)
5. [ ] Security audit checklist

**Deliverables:**
- Updated `settings.py` with security flags
- `corpus/middleware/security_headers.py`
- CAPTCHA integration (hCaptcha or reCAPTCHA)
- Security documentation

**Testing:**
- [ ] XSS attacks blocked by CSP
- [ ] Login brute force rate-limited
- [ ] HTTPS enforced in production

---

### **Week 11: KVKK/GDPR Compliance**

**Goals:**
- Legal compliance for public sector
- Data processing agreements
- Consent management

**Tasks:**
1. [ ] Create Terms of Service page
2. [ ] Create Privacy Policy page
3. [ ] Implement consent checkboxes (registration)
4. [ ] Build data export for users (download my data)
5. [ ] Implement account deletion workflow
6. [ ] Create Data Protection Officer contact page

**Deliverables:**
- Legal pages: ToS, Privacy Policy, Cookie Policy
- `corpus/views/privacy_views.py`
- User data export endpoint (`/my-data/export/`)
- Account deletion with 30-day grace period

**Testing:**
- [ ] User accepts ToS on registration
- [ ] User can download all their query history
- [ ] Account deletion removes personal data

---

### **Week 12: UI Polish & Documentation**

**Goals:**
- Professional, accessible UI
- Comprehensive documentation
- Tutorial videos

**Tasks:**
1. [ ] Redesign homepage (national corpus branding)
2. [ ] Add accessibility features (ARIA labels, keyboard navigation)
3. [ ] Create user guide (how to search, how to export)
4. [ ] Create API documentation with examples
5. [ ] Create video tutorial (5 min intro)
6. [ ] Multi-language support (Turkish/English toggle)

**Deliverables:**
- Redesigned templates with national branding
- `docs/` folder with user guides
- API documentation site
- Tutorial video (YouTube/hosted)
- i18n/l10n setup

**Testing:**
- [ ] Screen reader compatibility
- [ ] All major browsers supported (Chrome, Firefox, Safari, Edge)
- [ ] Tutorial video plays and is clear

---

## Post-MVP: Future Enhancements (Weeks 13+)

### **Phase 5: Scalability & Performance**
- ElasticSearch integration for faster queries
- Redis caching for frequent searches
- CDN for static assets
- Database optimization (indexing, partitioning)

### **Phase 6: Advanced Analytics**
- Collocation networks visualization
- Trend analysis (word frequency over time)
- Comparative subcorpus analysis
- Integration with external tools (Sketch Engine, AntConc)

### **Phase 7: Institutional Partnerships**
- Institutional data use agreements (DUA) workflow
- Bulk access portal for approved partners
- Integration with university SSO (CAS, Shibboleth)
- Researcher verification automation (ORCID API)

---

## Success Metrics

**By Week 12 (MVP Launch):**
- [ ] 5-tier role system operational
- [ ] 100+ documents in corpus (demo dataset)
- [ ] 10 registered test users
- [ ] 100% test coverage on critical features
- [ ] API functional with 3 sample integrations
- [ ] Security audit passed
- [ ] KVKK compliance checklist complete
- [ ] User documentation published

**By Month 6:**
- [ ] 1000+ registered users
- [ ] 10,000+ documents indexed
- [ ] 5 institutional partnerships
- [ ] API used by 3+ external projects
- [ ] 99.9% uptime

**By Year 1:**
- [ ] 10,000+ registered users
- [ ] 100,000+ documents (10M+ tokens)
- [ ] Cited in 10+ academic publications
- [ ] National platform recognized by Ministry

---

## Current Status: Week 1 - Day 1

**Starting Now:**
1. ✅ Create UserProfile model with role field
2. ✅ Build permission decorators
3. ✅ Update registration flow with role selection
4. ⏳ Migrate database
5. ⏳ Test role-based access in views

**Next Steps:**
- Complete Week 1 tasks (User Roles & Permissions)
- Deploy to staging environment
- Begin Week 2 (Rate Limiting & Audit Logging)

---

**Let's begin! 🚀**
