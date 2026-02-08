# National Educational Corpus Platform: Architectural Vision & Policy Framework

**Document Type:** Architectural Blueprint & Policy Specification  
**Scope:** National-scale, publicly accessible linguistic corpus platform  
**Authority:** Ministry of Education / National Research Institution  
**Version:** 1.0  
**Date:** February 2026

---

## Executive Summary

This document defines the architectural principles, access policies, and operational model for a national-scale educational corpus (derlem) web platform. The platform serves pre-annotated linguistic data to researchers, educators, and the public while maintaining strict compliance with data protection standards and ensuring long-term sustainability.

**Key Principle:** The platform is a **corpus query and visualization service**, not an NLP processing engine or document archive. All linguistic annotation is performed offline; the platform's role is controlled access, efficient querying, and governed export.

---

## A) WHAT A MODERN CORPUS PLATFORM IS

### Definition

A **corpus web platform** is a specialized information system designed to provide structured, indexed access to linguistically annotated text collections. It serves as the primary interface between corpus data and end users (researchers, educators, students, developers).

### Core Functions

1. **Index & Serve Pre-Annotated Data**  
   - Store and index multi-layered linguistic annotations (tokens, lemmas, POS tags, syntactic dependencies, morphological features)
   - Provide fast retrieval through optimized database queries
   - Support complex linguistic queries without re-processing text

2. **Query Interface**  
   - Enable users to search by word forms, lemmas, part-of-speech tags, syntactic patterns
   - Generate concordances (KWIC - Key Word in Context) in real-time
   - Produce frequency distributions and statistical summaries

3. **Access Control & Governance**  
   - Enforce role-based permissions
   - Apply rate limits and export quotas
   - Log all access for audit and compliance

4. **Visualization & Analysis Tools**  
   - Display concordance lines with contextual metadata
   - Show frequency charts, n-gram distributions, collocation networks
   - Compare subcorpora and temporal trends

### What It Is NOT

| **What It Is NOT** | **Why This Distinction Matters** |
|--------------------|----------------------------------|
| **Document Archive** | Users cannot browse or download raw documents in bulk. The platform serves **annotated linguistic units**, not full texts. Raw documents may contain personal data, copyrighted material, or sensitive content. |
| **NLP Analysis Service** | The platform does NOT tokenize, POS-tag, or parse user input. All linguistic processing is **pre-computed offline**. This ensures speed, reproducibility, and controlled quality. |
| **File Download Portal** | Users cannot download entire corpus files like a file-sharing service. Exports are **governed, sampled, and logged**. Full corpus access requires institutional agreements. |
| **General Search Engine** | Unlike Google or Elasticsearch over raw text, this platform searches **structured linguistic annotations**. It understands "lemma=git" can match "gitti, gidiyorum, gitsem". |

### Why Serve Pre-Annotated Formats?

**Best Practice Justification:**

1. **Reproducibility:** All analyses use the same gold-standard annotations. Two researchers querying "verb+accusative" get identical results.

2. **Performance:** Linguistic queries (e.g., "all adjectives modifying 'bilim'") require indexed structures. Real-time NLP would be prohibitively slow at scale.

3. **Quality Assurance:** Offline processing allows human correction, inter-annotator agreement checks, and version control.

4. **Transparency:** Users know exactly what annotation scheme was used, by which tool/model, and when.

5. **Legal Compliance:** Pre-processing enables systematic removal of personal identifiers (names, ID numbers) before indexing.

---

## B) DATA & FILE MODEL

### Storage Architecture

The corpus is stored in **multi-layered formats** optimized for linguistic querying:

#### 1. CoNLL-U (Universal Dependencies Format)
```
# sent_id = doc1_s001
# text = Öğrenciler kitap okuyor.
1    Öğrenciler    öğrenci     NOUN    _    Case=Nom|Number=Plur    3    nsubj    _    _
2    kitap         kitap       NOUN    _    Case=Nom|Number=Sing    3    obj      _    _
3    okuyor        oku         VERB    _    Aspect=Prog|Tense=Pres  0    root     _    SpaceAfter=No
4    .             .           PUNCT   _    _                       3    punct    _    _
```

**Purpose:**
- Syntactic dependency trees
- Morphological features
- Inter-word relations
- Enables complex queries like "find all objects of 'okumak'"

#### 2. VRT (Vertical Text Format / CWB Format)
```
<text id="doc1" year="2024" genre="educational">
<s id="s001">
Öğrenciler    öğrenci    NOUN    Nom|Plur
kitap         kitap      NOUN    Nom|Sing
okuyor        oku        VERB    Prog|Pres
.             .          PUNCT   _
</s>
</text>
```

**Purpose:**
- Fast positional queries (Corpus Workbench / IMS Open Corpus Workbench)
- Metadata embedding (genre, year, author, region)
- Efficient concordance generation
- Standard in corpus linguistics (Sketch Engine, CQP)

#### 3. Metadata JSON
```json
{
  "document_id": "doc1",
  "source": "Ministry of Education Textbook Collection",
  "year": 2024,
  "genre": "educational",
  "education_level": "secondary",
  "word_count": 5432,
  "annotation_version": "v2.1",
  "processing_date": "2026-02-01",
  "privacy_status": "anonymized",
  "license": "CC BY-NC-SA 4.0"
}
```

**Purpose:**
- Document provenance
- Filtering by metadata (e.g., "only texts from 2020–2025")
- License and usage terms
- Privacy compliance markers

### Indexing Mechanism (Conceptual)

The platform maintains **inverted indices** over linguistic features:

- **Word Form Index:** "kitap" → [doc1:pos4, doc5:pos12, ...]
- **Lemma Index:** "oku" → [doc1:pos3, doc2:pos7, doc5:pos45, ...]
- **POS Index:** "VERB" → [all verb positions across corpus]
- **Dependency Index:** "nsubj of oku" → [all subject positions]
- **Metadata Index:** "genre=educational AND year=2024" → [doc1, doc3, ...]

**Query Example:**  
User searches: _"lemma='yaz' + POS=VERB + year>2020"_

The system:
1. Looks up all instances of lemma "yaz" tagged as VERB
2. Filters by document metadata (year > 2020)
3. Retrieves surrounding context (±5 words)
4. Returns concordance table

**No NLP is performed during query execution** — all data is pre-indexed.

### Visibility Model: What Users See vs. What Is Hidden

| **Data Layer** | **Public User** | **Registered User** | **Verified Researcher** |
|----------------|-----------------|---------------------|-------------------------|
| **Concordance (KWIC)** | ✅ Limited (20 results) | ✅ Full (1000 results) | ✅ Full + API access |
| **Lemma, POS, Morphology** | ✅ Visible in results | ✅ Full access | ✅ Full access |
| **Dependency Trees** | ❌ Hidden | ✅ Visible | ✅ Visible + export |
| **Full Document Text** | ❌ Hidden | ⚠️ Preview only (500 chars) | ⚠️ Extended preview (5000 chars) |
| **Raw Text Download** | ❌ No | ❌ No | ⚠️ Requires institutional agreement |
| **Metadata** | ✅ Basic (year, genre) | ✅ Full metadata | ✅ Full + processing logs |
| **Frequency Lists** | ✅ Top 100 words | ✅ Top 10,000 | ✅ Full distribution |

**Privacy-Protected Elements (Hidden from All Users):**
- Personal names (replaced with [PERSON])
- ID numbers, addresses, phone numbers
- Original file paths or author identities (if sensitive)

---

## C) USER ROLES AND ACCESS LEVELS

### 1. Anonymous Public User

**Purpose:** Enable broad educational access and public transparency.

**Can:**
- Search by word form, lemma, or simple POS tag
- View up to 20 concordance lines per query
- See basic metadata (year, genre, word count)
- View word frequency lists (top 100)
- View POS distribution charts

**Cannot:**
- Download any data
- Access API
- View syntactic trees
- See full document previews
- Export results

**Limits:**
- 10 queries per hour
- No session persistence
- Results cached for 5 minutes

**Rationale:** Allows students, educators, and curious citizens to explore Turkish language patterns without barriers, while preventing bulk data extraction.

---

### 2. Registered General User

**Registration Requirements:**
- Valid email address
- Verified via email confirmation
- Accepts Terms of Service

**Can:**
- All Anonymous User capabilities, plus:
- View up to 1000 concordance lines per query
- Export concordance tables as CSV (max 500 lines)
- View syntactic dependency annotations
- Access extended metadata (annotation version, processing tools)
- Save search queries for reuse
- Create personal collections (bookmark documents)

**Cannot:**
- Download raw corpus files
- Access bulk export API
- Remove rate limits

**Limits:**
- 100 queries per day
- 10 CSV exports per day
- 5 MB total export quota per month

**Rationale:** Supports individual researchers, teachers, students preparing theses, or journalists analyzing language use. Sufficient for most academic work without enabling mass scraping.

---

### 3. Verified Academic/Researcher

**Verification Requirements:**
- Institutional email (@university.edu.tr, @tubitak.gov.tr)
- ORCID or academic profile verification
- Research purpose declaration
- Acceptance of citation and attribution requirements

**Can:**
- All Registered User capabilities, plus:
- View full concordance results (no pagination limit)
- Export concordances with full annotations (CoNLL-U format)
- Download frequency lists and statistical aggregates
- Access API for programmatic queries (rate-limited)
- Request full-text access for specific documents (case-by-case approval)
- Download subcorpus samples (10,000 tokens max per request)

**Cannot:**
- Download entire corpus in bulk
- Redistribute corpus data outside research team
- Use data for commercial purposes without separate license

**Limits:**
- 1000 queries per day
- 100 MB export quota per month
- API: 1000 requests per day, 10 requests per minute
- Full-text requests reviewed within 5 business days

**Obligations:**
- Cite corpus in publications
- Share derivative annotations if publicly funded
- Notify platform of publications using corpus

**Rationale:** Enables serious academic research while maintaining control over full data. API access allows reproducible computational studies. Export limits prevent unauthorized redistribution.

---

### 4. Developer/API User

**Application Requirements:**
- Organization/project description
- Technical integration plan
- Data usage agreement
- API key request approval

**Can:**
- Programmatic access to all query functions
- Batch concordance retrieval
- Automated export with watermarking
- Webhook notifications for corpus updates
- Access to data schemas and documentation

**Cannot:**
- Bypass rate limits without elevated approval
- Scrape or mirror the corpus
- Resell API access

**Limits:**
- Standard tier: 5000 API calls per day
- Elevated tier (approved projects): 50,000 calls per day
- Burst limit: 100 requests per minute
- Export quota: 500 MB per month

**Monitoring:**
- All API calls logged with user, timestamp, query
- Anomaly detection for scraping patterns
- Automatic suspension on policy violation

**Rationale:** Supports developers building educational tools (dictionary apps, language learning platforms, journalistic analysis tools) while preventing abuse.

---

### 5. System Administrator

**Access:**
- Full database access (read/write)
- User management (approve, suspend, delete accounts)
- Audit log review
- System configuration
- Corpus update and re-indexing workflows

**Cannot (Policy Restrictions):**
- Export user personal data without legal mandate
- Modify historical queries or logs (immutable audit trail)
- Grant API access without documented approval process

**Obligations:**
- Annual security audit
- Quarterly access log review
- Immediate incident reporting (data breach, unauthorized access)
- Compliance with public records law (when applicable)

**Rationale:** Maintains operational control while ensuring accountability and preventing insider threats.

---

## D) QUERY & INTERACTION MODEL

### Core Query Types

#### 1. Simple Keyword Search
**User Input:** `"kitap"`  
**System Action:**
- Search word form index
- Return all instances with ±5 word context
- Display as concordance table

**Use Case:** Student exploring how a word is used in different contexts.

---

#### 2. Lemma-Based Search
**User Input:** `lemma:"yaz"` + `POS:VERB`  
**System Action:**
- Search lemma index for "yaz"
- Filter by POS=VERB
- Exclude nominal forms like "yazı" (NOUN)
- Return: _"yazıyor, yazdı, yazsam, yazacak"_

**Use Case:** Linguist studying verb conjugation patterns.

---

#### 3. POS Pattern Search
**User Input:** `[pos="ADJ"] [pos="NOUN"]`  
**CQP Syntax:** Pattern matching for "adjective + noun" sequences  
**Returns:** _"güzel kitap, büyük ev, yeni araba"_

**Use Case:** Researcher analyzing adjective-noun collocations.

---

#### 4. Dependency Query
**User Input:** Find all objects of verb "yazmak"  
**System Action:**
- Query dependency index: `deprel="obj" AND head_lemma="yaz"`
- Return: _"mektup yazdı, kitap yazıyor, şiir yazmış"_

**Use Case:** Syntactician studying verb argument structures.

---

#### 5. Metadata-Filtered Search
**User Input:** `lemma:"bilim"` + `genre="educational"` + `year>=2020`  
**System Action:**
- Filter corpus by metadata
- Search within subcorpus
- Compare frequency to other genres

**Use Case:** Educator comparing how "science" is discussed in textbooks vs. news.

---

#### 6. Frequency Lists & N-Grams
**Request:** Top 1000 words in educational texts (2020–2025)  
**Output:**
```
1. ve      - 145,234 occurrences
2. bir     - 98,432
3. bu      - 87,123
...
```

**Request:** Top bigrams (2-word sequences)  
**Output:**
```
1. bu yıl          - 3,421
2. örneğin bu     - 2,876
3. göre ise       - 2,543
```

**Use Case:** Language teacher identifying most common phrases for curriculum design.

---

#### 7. Subcorpus Comparison
**Scenario:** Compare word "teknoloji" frequency in:
- Educational texts (2000–2010) vs (2020–2025)
- Textbooks vs. news articles

**Output:**
- Frequency per million words
- Statistical significance test (log-likelihood ratio)
- Context comparison (concordance side-by-side)

**Use Case:** Researcher studying language change and domain-specific vocabulary.

---

### Query Execution Philosophy

**Critical Principle:** All queries operate on **pre-indexed annotations**, not raw text.

**Example Workflow:**

1. User submits: `lemma:"git" + tense=past`
2. System translates to database query:
   ```sql
   SELECT token, context, metadata 
   FROM corpus_index 
   WHERE lemma='git' AND morph_features LIKE '%Tense=Past%'
   ```
3. Retrieve matching tokens + surrounding context
4. Format as concordance table
5. Return to user

**No NLP pipeline is triggered.** The system is a **query engine**, not a processing engine.

---

## E) EXPORT POLICY

### Defining "Export" in a Public Corpus

Export is the **controlled transfer of corpus data** from the platform to the user's local environment. It must balance:
- **Research Needs:** Researchers require data for offline analysis, replication, archiving.
- **Data Protection:** Preventing bulk unauthorized redistribution.
- **Legal Compliance:** Honoring copyright, privacy laws, donor agreements.

---

### Export Categories

#### 1. Aggregated Data Export (Unrestricted)
**What:**
- Frequency lists
- POS distribution charts
- Statistical summaries (mean word length, type-token ratio)
- N-gram tables

**Why Unrestricted:**
- Aggregates cannot be reverse-engineered to original texts
- No personal data or copyrighted content
- Supports transparency and reproducibility

**Format:** CSV, JSON, Excel

**Example:**
```csv
word,frequency,relative_freq
bilim,4532,0.0023
teknoloji,3421,0.0017
eğitim,8765,0.0044
```

---

#### 2. Sample Concordance Export (Rate-Limited)
**What:**
- Up to 500 concordance lines per export
- Includes: left context, keyword, right context, POS, lemma, metadata
- Excludes: full document text, personal identifiers

**Restrictions:**
- Registered users: 10 exports per day
- Verified researchers: 100 exports per day
- Watermarked with export date, user ID, query

**Format:** CSV, CoNLL-U snippet

**Example:**
```csv
left_context,keyword,right_context,pos,lemma,doc_id,year
"öğrenciler her gün","kitap","okuyorlar ve öğreniyorlar",NOUN,kitap,doc42,2023
```

**Watermark (metadata row):**
```
# Exported from: National Turkish Corpus Platform
# User: researcher_12345
# Date: 2026-02-07
# Query: lemma="kitap" + genre="educational"
# License: CC BY-NC-SA 4.0 - Cite as DOI:10.xxxxx/corpus.v2
```

---

#### 3. Full Corpus Access (Strictly Controlled)

**What:**
- Complete annotated corpus files (CoNLL-U, VRT)
- Raw text documents (if legally permissible)
- Processing scripts and annotation guidelines

**Who:**
- Only institutional partners (universities, research institutes)
- Requires signed Data Use Agreement (DUA)
- Approved by Ministry/Corpus Steering Committee

**Conditions:**
- Non-commercial use only
- No redistribution without permission
- Mandatory citation in all publications
- Annual usage report required
- Data must be stored securely (encrypted, access-controlled)

**Process:**
1. Submit formal access request (research plan, team credentials)
2. Legal review (2–4 weeks)
3. DUA signing
4. Secure file transfer (SFTP, encrypted USB)
5. Access logged and audited

**Rationale:** Enables large-scale computational studies (LLM training, dialect analysis) while preventing misuse.

---

### Rate Limits & Quotas

| **User Type** | **Daily Queries** | **Export Quota/Month** | **API Calls/Day** |
|---------------|-------------------|------------------------|-------------------|
| Anonymous | 10 | 0 | 0 |
| Registered | 100 | 5 MB | 0 |
| Verified Researcher | 1000 | 100 MB | 1000 |
| Developer (API) | Unlimited (rate-limited) | 500 MB | 5000–50,000 |
| Institutional Partner | Unlimited | Unlimited | Custom |

**Enforcement:**
- Tracked per user session / API key
- Soft limit: Warning message
- Hard limit: Rate-limiting (HTTP 429)
- Abuse: Account suspension + review

---

### Watermarking & Attribution

Every export includes:
- **Timestamp & User ID**
- **Query parameters**
- **Corpus version** (e.g., v2.1, indexed 2026-01-15)
- **Citation requirement:**
  > "Data from National Turkish Corpus (NTC) v2.1, Ministry of Education, 2026. DOI:10.xxxxx/ntc.v2.1. Accessed via https://corpus.meb.gov.tr"

**Purpose:**
- Traceability (track data provenance in published research)
- Deterrence (unauthorized redistribution is traceable)
- Compliance (satisfies funding agency data-sharing mandates)

---

## F) PRIVACY & SECURITY (PUBLIC SECTOR LEVEL)

### Data Protection Principles

#### 1. Personal Data Masking (Anonymization)

**Requirement:** Remove all personal identifiers before indexing.

**Masked Elements:**
- **Person Names:** _"Ahmet Yılmaz"_ → `[PERSON]`
- **Locations (when sensitive):** _"İstanbul Atatürk Mahallesi"_ → `[LOCATION]`
- **ID Numbers:** _"TC: 12345678901"_ → `[ID_NUMBER]`
- **Contact Info:** _"555-1234, ahmet@email.com"_ → `[PHONE]`, `[EMAIL]`
- **Sensitive Attributes:** Medical records, ethnic identifiers → `[REDACTED]`

**Implementation:**
- Automated Named Entity Recognition (NER) during preprocessing
- Manual review for high-risk documents (medical, legal)
- Irreversible masking (original data not stored in platform)

**Example:**
```
Original: "Ahmet Bey, İzmir'de 1234567890 numaralı telefonu aradı."
Masked:   "[PERSON], [LOCATION]'de [PHONE] numaralı telefonu aradı."
```

**Rationale:** Protects privacy while preserving linguistic structure for research.

---

#### 2. Access Logging & Audit Trails

**What Is Logged:**
- User ID / IP address
- Timestamp (ISO 8601)
- Query parameters (lemma, POS, filters)
- Export actions (what was downloaded, how much)
- API calls (endpoint, response size)

**Log Retention:**
- Active logs: 2 years (for abuse detection)
- Archived logs: 10 years (for legal compliance)
- Anonymized aggregates: Indefinite (for usage analytics)

**Access to Logs:**
- System administrators (operational purposes)
- Legal authorities (with court order only)
- Public statistics (anonymized, aggregated)

**Immutability:**
- Logs cannot be modified or deleted (append-only database)
- Cryptographic hashing ensures integrity
- Regular backups to separate secure storage

**Example Log Entry:**
```json
{
  "timestamp": "2026-02-07T14:32:11Z",
  "user_id": "researcher_12345",
  "ip_address": "89.xxx.xxx.xxx (hashed)",
  "action": "concordance_query",
  "query": "lemma='bilim' + year>=2020",
  "results_returned": 342,
  "export": false
}
```

**Rationale:** Enables abuse investigation, compliance audits, and usage research (e.g., "most queried words in educational domain").

---

#### 3. Purpose Limitation

**Principle:** Data collected must be used ONLY for the stated purpose.

**Stated Purposes:**
- Provide corpus query and concordance services
- Improve platform usability (anonymized usage analytics)
- Ensure system security (detect abuse, prevent attacks)
- Comply with legal obligations (respond to court orders)

**Prohibited Uses:**
- Selling user data to third parties
- Profiling users for non-research purposes
- Linking corpus platform data with unrelated government databases (without explicit consent)

**User Control:**
- Users can request their query history
- Users can delete their account + all personal data (GDPR "right to be forgotten")
- Anonymized query data may remain for research (not attributable to individual)

---

#### 4. Differential Privacy for Statistics

**Challenge:** Frequency lists and statistics could reveal presence of rare words linked to individuals.

**Mitigation:**
- Suppress frequencies below threshold (e.g., words appearing <5 times)
- Add statistical noise to counts (Laplace mechanism)
- Aggregate rare categories (e.g., "Other: 47 low-frequency words")

**Example:**
```
Standard frequency list:
- "teknoloji": 15,234
- "ıhlamur": 3        ← SUPPRESSED (too rare, could identify source)

Released version:
- "teknoloji": 15,234
- [Rare words <5 occurrences]: 127 total
```

**Rationale:** Prevents re-identification attacks via statistical inference.

---

### Why Raw Text Access Is Restricted

**Legal Reasons:**
1. **Copyright:** Full texts may be under copyright. Platform may have license to index/analyze, but not redistribute.
2. **Privacy:** Even "anonymized" text can be re-identified via writing style, context clues.
3. **Donor Agreements:** Texts contributed by publishers/authors often prohibit full redistribution.

**Research Reasons:**
1. **Prevent Plagiarism:** Bulk text download could enable academic dishonesty.
2. **Encourage Proper Methodology:** Researchers should work with annotations, not re-annotate from scratch (inconsistent, wasteful).

**Ethical Reasons:**
1. **Trust:** Donors (teachers, students, authors) trust platform to use texts responsibly.
2. **Sustainability:** Unrestricted redistribution could undermine future corpus expansion (no one will contribute texts).

**Mitigations:**
- Provide sufficient context in concordances (±10 words is enough for most linguistic research)
- Allow extended previews for verified users (5000 characters)
- Grant full-text access case-by-case for justified research needs

---

### Compliance Framework

**Applicable Regulations:**
- **KVKK (Turkish Personal Data Protection Law)**
- **GDPR (for EU users/collaborations)**
- **Public Records Laws (transparency, archiving)**
- **Copyright Law (protection of literary works)**

**Compliance Measures:**

| **Requirement** | **Implementation** |
|-----------------|-------------------|
| **Data Minimization** | Collect only necessary user data (email, institution) |
| **Consent** | Clear terms of service + research use declaration |
| **Security** | Encryption (TLS 1.3), access control (role-based) |
| **Right to Access** | Users can download their query history |
| **Right to Deletion** | Account deletion removes personal data within 30 days |
| **Data Breach Notification** | 72-hour reporting to authorities + affected users |
| **Audit Trail** | Immutable logs for 10 years |

**Regular Audits:**
- Annual security penetration test
- Quarterly privacy impact assessment
- Independent audit by Data Protection Authority (upon request)

---

## G) WHAT THE PLATFORM MUST NOT DO

### Prohibited Functions

#### 1. Never Run NLP Pipelines on User Queries

**Anti-Pattern:**
```
User submits: "Tokenize and POS-tag this sentence: Kitap okudum."
System MUST NOT: Run a tokenizer/tagger on user input.
```

**Why:**
- **Performance:** Real-time NLP is slow at scale
- **Quality:** Ad-hoc tagging is inconsistent with corpus annotations
- **Security:** User input could inject malicious patterns (regex DoS)

**Correct Approach:**
- User can only query pre-indexed data
- If they need custom text analyzed, direct them to separate NLP tool

---

#### 2. Never Allow Bulk Download of Raw Texts

**Anti-Pattern:**
```
Endpoint: /api/download/all_texts
Response: 500GB of raw documents
```

**Why:**
- **Copyright violation:** Most texts not licensed for redistribution
- **Privacy risk:** Even anonymized texts can be re-identified
- **Abuse:** Corpus could be cloned and hosted elsewhere

**Correct Approach:**
- Concordances only (snippets with context)
- Full access requires institutional agreement

---

#### 3. Never Expose Personal Data in Logs or Exports

**Anti-Pattern:**
```
Log: "User Ahmet Yılmaz (ahmet@email.com) searched for 'political protest'"
Export: Concordance includes "Mehmet Demir, age 34, from Ankara said..."
```

**Why:**
- **Legal liability:** KVKK/GDPR violations
- **Ethical breach:** Users trust platform to protect their privacy

**Correct Approach:**
- Hash/pseudonymize IP addresses in logs
- Mask all personal identifiers in corpus before indexing

---

#### 4. Never Mix Roles Without Explicit Permission

**Anti-Pattern:**
```
Admin account used for personal research queries
Researcher account granted admin privileges without approval
```

**Why:**
- **Audit confusion:** Cannot distinguish operational vs. research access
- **Privilege escalation:** Security risk if researcher account compromised

**Correct Approach:**
- Separate accounts for admin vs. research roles
- Admins must use personal accounts for queries, admin account only for system operations

---

#### 5. Never Modify Linguistic Annotations Based on User Feedback

**Anti-Pattern:**
```
User: "This POS tag is wrong, it should be VERB not NOUN"
System: Automatically updates annotation in database
```

**Why:**
- **Data integrity:** Corpus must be stable, version-controlled
- **Inconsistency:** Ad-hoc changes create incompatible versions
- **Authority:** Only corpus curators (not end-users) decide annotation standards

**Correct Approach:**
- Users can report errors via feedback form
- Corpus team reviews, batches corrections into next version release
- Platform clearly displays "Corpus version 2.1" + changelog

---

#### 6. Never Cache Query Results Without Respecting Access Levels

**Anti-Pattern:**
```
Cache: Anonymous user query results remain in cache
Next user (also anonymous): Sees cached results exceeding 20-line limit
```

**Why:**
- **Access control bypass:** User gets more data than authorized
- **Privacy leak:** User A could see what User B searched

**Correct Approach:**
- Cache keys include user role/permissions
- Results tagged with access level, not served cross-role

---

#### 7. Never Ignore Rate Limits for "Trusted" Users

**Anti-Pattern:**
```
"Professor X is our collaborator, let's disable rate limits for them"
```

**Why:**
- **Fairness:** Sets precedent for exceptions, creates resentment
- **Security:** Compromised "trusted" account becomes unlimited scraper
- **Audit trail:** Unclear why one user has 10,000x more access

**Correct Approach:**
- All users subject to rate limits appropriate to their verified role
- Exceptions require formal institutional agreement (not ad-hoc)

---

### Architectural Anti-Patterns

#### ❌ The "Document Archive" Anti-Pattern
Treating corpus as a PDF repository with search.

**Problem:** Users expect to download full PDFs.  
**Correct Model:** Serve linguistic data (tokens, annotations), not documents.

---

#### ❌ The "Google for Texts" Anti-Pattern
Full-text search without linguistic structure.

**Problem:** Cannot distinguish "bank" (finance) vs. "bank" (river) without POS.  
**Correct Model:** Lemma + POS + dependency queries.

---

#### ❌ The "Free-for-All Export" Anti-Pattern
"Download entire corpus as ZIP file."

**Problem:** Corpus gets redistributed, original platform becomes irrelevant.  
**Correct Model:** Governed export with watermarking, quotas, and DUAs.

---

#### ❌ The "Closed Black Box" Anti-Pattern
No transparency about annotation methods.

**Problem:** Researchers cannot assess quality or reproducibility.  
**Correct Model:** Publish annotation guidelines, inter-annotator agreement, tool versions.

---

## H) DESIGN PHILOSOPHY

### 1. Longevity (10–20 Year Horizon)

**Principle:** The platform must outlive current technologies and political administrations.

**Implications:**

- **Open Standards:** Use VRT, CoNLL-U (community-maintained formats)
- **Avoid Vendor Lock-in:** No proprietary databases, no cloud-only infrastructure
- **Version Control:** Corpus v1.0 → v2.0 → v3.0 with clear changelogs
- **Data Portability:** Government can export entire corpus to new platform if needed

**Example:**
- British National Corpus (BNC) launched 1994, still widely used in 2024 (30 years)
- Platform switched from CD-ROM → Web → API, but data format remained stable

**Commitment:**
> "Corpus data will remain accessible for at least 20 years, regardless of technology changes."

---

### 2. Openness Without Data Leakage

**Principle:** Maximize public access while preventing unauthorized mass extraction.

**Balance:**

| **Open** | **Controlled** |
|----------|----------------|
| ✅ Anyone can search | ❌ Bulk download restricted |
| ✅ Aggregated statistics public | ❌ Raw texts require agreement |
| ✅ API for developers | ❌ Rate limits enforced |
| ✅ Documentation + tutorials | ❌ Watermarked exports |

**Philosophy:**
> "The corpus belongs to the nation, but access must be sustainable and legal."

---

### 3. Reproducible Research

**Principle:** Any study using this corpus must be independently verifiable.

**Enablers:**

- **Versioned Corpus:** Every export cites version (v2.1, indexed 2026-01-15)
- **Query Logging:** Researchers can share query syntax (e.g., CQP query: `[lemma="git" & pos="VERB"]`)
- **Stable IDs:** Each sentence has permanent ID (doc42_s0123)
- **API Consistency:** Same query today = same results in 5 years (for same version)

**Example Workflow:**

1. Researcher publishes paper: "Passive voice frequency in educational texts (2020–2025)"
2. Paper cites: NTC v2.1, query: `[pos="VERB" & voice="passive"]`, accessed 2026-02-07
3. Another researcher runs same query → gets identical results → confirms findings
4. Reproducibility achieved ✅

**Commitment:**
> "All research using this corpus must include sufficient metadata for independent replication."

---

### 4. Neutrality & Institutional Credibility

**Principle:** The platform must be politically neutral and scientifically rigorous.

**Governance:**

- **Advisory Board:** Linguists, educators, privacy experts (multi-party representation)
- **Transparent Policies:** Access rules, annotation guidelines publicly documented
- **No Censorship:** Corpus reflects real language use, including controversial topics (within legal limits)
- **Non-Commercial:** No ads, no paid tiers (public-sector funding only)

**Trust Mechanisms:**

- **Open Methodology:** Annotation tools, inter-annotator agreement scores published
- **Third-Party Audit:** Independent linguists can verify sample annotations
- **International Standards:** Follows Universal Dependencies, ISO standards

**Example:**
- Czech National Corpus (CNC) is trusted because it's government-funded, academically managed, and internationally peer-reviewed.

**Commitment:**
> "This platform serves the public interest, not political or commercial agendas."

---

## Conclusion

This document defines a **modern, sustainable, and ethically sound** national corpus platform. It is:

- **A query service**, not a document archive or NLP lab
- **Pre-annotated and indexed**, enabling fast, reproducible research
- **Role-based**, balancing public access with data protection
- **Export-governed**, preventing abuse while supporting research
- **Privacy-compliant**, meeting KVKK/GDPR standards
- **Long-term sustainable**, designed for 10–20 year lifespan
- **Institutionally credible**, politically neutral, scientifically rigorous

By adhering to these principles, the platform will serve as a **trusted national resource** for educators, researchers, students, and the public — advancing linguistic research, supporting Turkish language education, and demonstrating best practices in public-sector digital infrastructure.

---

**Next Steps:**
1. Form Corpus Steering Committee (linguists, legal, technical experts)
2. Draft Data Use Agreements for institutional partners
3. Develop technical architecture aligned with this vision
4. Launch pilot with 10M-word subcorpus
5. Public consultation period (gather feedback from research community)
6. Full launch with continuous improvement

**Contact:**  
National Corpus Initiative  
Ministry of Education / National Research Division  
Email: corpus@meb.gov.tr  
Web: https://corpus.meb.gov.tr (placeholder)

---

**Document End**
