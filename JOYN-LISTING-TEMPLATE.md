# JOYN-LISTING-TEMPLATE.md — Standard Listing Page Structure
**Version 1.0 · January 2026**
**Every AI staff listing page follows this exact template. No variations.**

---

## Overview

This document provides the exact HTML structure, copy framework, and asset requirements for every AI staff listing page on the Joyn marketplace. Builders generate these pages; the Reviewer Agent validates against this spec.

---

## Page Sections (Required Order)

```
1. Nav
2. Breadcrumb
3. Hero (identity, ROI chips, CTAs)
4. Screenshots Gallery
5. What [Name] Does (3 core tasks)
6. How It Works (Supervised only — workflow phases)
7. Named Outputs
8. Ratings & Reviews
9. Pricing
10. Built By (creator attribution)
11. Compliance & Security
12. Footer
```

---

## Section 1: Nav

Same across all pages. No customization.

```html
<nav class="nav">
  <a href="/index.html" class="nav-logo">JOYN.</a>
  <div class="nav-links">
    <a href="/marketplace/index.html" class="nav-link">Marketplace</a>
    <a href="/marketplace/creator-studio.html" class="nav-link">Creator Studio</a>
    <a href="https://app.tryjoyn.me/login" class="nav-link">Log in</a>
  </div>
</nav>
```

---

## Section 2: Breadcrumb

```html
<nav class="breadcrumb">
  <a href="/index.html">Home</a>
  <span class="breadcrumb-sep">→</span>
  <a href="/marketplace/index.html">Marketplace</a>
  <span class="breadcrumb-sep">→</span>
  <span class="breadcrumb-current">[Staff Name]</span>
</nav>
```

---

## Section 3: Hero

### Structure

```html
<section class="listing-hero">
  <div class="listing-hero-content">
    <!-- Vertical Label -->
    <div class="listing-vertical-label">[Vertical]</div>
    
    <!-- Mode Badge -->
    <div class="listing-mode-badge listing-mode-[autonomous|supervised]">
      [Autonomous · Live Now | Supervised Mode]
    </div>
    
    <!-- Staff Name -->
    <h1 class="listing-name">[Staff Name]</h1>
    
    <!-- One-Sentence Role -->
    <p class="listing-tagline">[One sentence that tells hirers exactly what this staff does.]</p>
    
    <!-- ROI Chips -->
    <div class="listing-roi-chips">
      <span class="roi-chip">[ROI Chip 1 — specific, measurable]</span>
      <span class="roi-chip">[ROI Chip 2 — specific, measurable]</span>
      <span class="roi-chip">[ROI Chip 3 — optional]</span>
    </div>
    
    <!-- Rating Summary -->
    <div class="listing-rating-summary">
      <span class="rating-stars">★★★★★</span>
      <span class="rating-score">[4.8]</span>
      <span class="rating-count">([23] verified hires)</span>
    </div>
    
    <!-- CTAs -->
    <div class="listing-ctas">
      <a href="#hire" class="btn btn-primary">Start Free Trial</a>
      <a href="#demo" class="btn btn-outline">Watch Demo</a>
    </div>
  </div>
  
  <!-- Hero Image/Video Preview -->
  <div class="listing-hero-media">
    <img src="[hero-screenshot.png]" alt="[Staff Name] dashboard preview">
  </div>
</section>
```

### Copy Rules

| Element | Rule |
|---------|------|
| **Vertical Label** | Exact vertical name from taxonomy |
| **Staff Name** | One word preferred, max two words |
| **Tagline** | Single sentence, <25 words, no "and" splitting scope |
| **ROI Chips** | 2-4 chips, each <40 characters, specific numbers preferred |

### ROI Chip Examples

**Good:**
- "~4h analyst time saved/week"
- "0 missed regulatory bulletins"
- "72h to IC-ready vs 2-4 weeks"
- "$12K avg annual savings"

**Bad:**
- "Saves time" (not specific)
- "Better compliance" (not measurable)
- "Up to 50% faster" (weasel word)

---

## Section 4: Screenshots Gallery

```html
<section class="listing-screenshots" id="screenshots">
  <div class="screenshots-track">
    <button class="screenshot-item active" data-index="0">
      <img src="[screenshot-1.png]" alt="[Description of what this shows]">
    </button>
    <button class="screenshot-item" data-index="1">
      <img src="[screenshot-2.png]" alt="[Description]">
    </button>
    <button class="screenshot-item" data-index="2">
      <img src="[screenshot-3.png]" alt="[Description]">
    </button>
    <!-- 3-5 screenshots required -->
  </div>
  <div class="screenshot-preview">
    <img src="[screenshot-1.png]" alt="[Staff Name] interface" id="screenshot-main">
  </div>
  <div class="screenshot-captions">
    <p class="screenshot-caption active" data-index="0">[Caption for screenshot 1]</p>
    <p class="screenshot-caption" data-index="1">[Caption for screenshot 2]</p>
    <p class="screenshot-caption" data-index="2">[Caption for screenshot 3]</p>
  </div>
</section>
```

### Screenshot Requirements

| Requirement | Specification |
|-------------|---------------|
| **Count** | 3-5 screenshots |
| **Size** | 1280x800 or 800x1280 (landscape or portrait) |
| **Format** | PNG, no transparency |
| **Content** | Real UI from running staff, not mockups |
| **Captions** | Each screenshot has descriptive caption |

### Screenshot Subjects (recommended)

1. **Dashboard overview** — What hirer sees on login
2. **Key output** — Example of main deliverable
3. **Activity feed** — Staff actions in progress
4. **Settings/config** — Customization options
5. **Alert/escalation** — How staff communicates

---

## Section 5: What [Name] Does

```html
<section class="listing-tasks">
  <div class="section-header">
    <div class="label">What [Name] Does</div>
    <h2>Three core tasks. <em>Done right.</em></h2>
  </div>
  
  <div class="tasks-grid">
    <!-- Task 1 -->
    <div class="task-card">
      <div class="task-icon">[Icon]</div>
      <h3 class="task-title">[Task 1 Title]</h3>
      <p class="task-description">[2-3 sentences explaining what this task accomplishes and why it matters to the hirer.]</p>
    </div>
    
    <!-- Task 2 -->
    <div class="task-card">
      <div class="task-icon">[Icon]</div>
      <h3 class="task-title">[Task 2 Title]</h3>
      <p class="task-description">[2-3 sentences explaining what this task accomplishes.]</p>
    </div>
    
    <!-- Task 3 -->
    <div class="task-card">
      <div class="task-icon">[Icon]</div>
      <h3 class="task-title">[Task 3 Title]</h3>
      <p class="task-description">[2-3 sentences explaining what this task accomplishes.]</p>
    </div>
  </div>
</section>
```

### Task Rules

- Exactly 3 tasks (no more, no less for v1)
- Each task is a verb phrase: "Monitors...", "Prepares...", "Analyzes..."
- Description answers: What, Why, How often

---

## Section 6: How It Works (Supervised Mode Only)

```html
<section class="listing-workflow">
  <div class="section-header">
    <div class="label">How It Works</div>
    <h2>Your involvement. <em>Mapped.</em></h2>
    <p>Total hirer time: ~[X] hours across [Y] weeks</p>
  </div>
  
  <div class="workflow-phases">
    <!-- Phase 1 -->
    <div class="workflow-phase">
      <div class="phase-number">01</div>
      <div class="phase-content">
        <h3 class="phase-title">[Phase Name]</h3>
        <p class="phase-description">[What happens in this phase]</p>
        <div class="phase-checkpoint">
          <span class="checkpoint-icon">◉</span>
          <span class="checkpoint-label">Your input: [What hirer does]</span>
          <span class="checkpoint-time">~[X] min</span>
        </div>
      </div>
    </div>
    
    <!-- Phase 2 -->
    <div class="workflow-phase">
      <div class="phase-number">02</div>
      <div class="phase-content">
        <h3 class="phase-title">[Phase Name]</h3>
        <p class="phase-description">[What happens]</p>
        <div class="phase-checkpoint">
          <span class="checkpoint-icon">◉</span>
          <span class="checkpoint-label">Your input: [What hirer does]</span>
          <span class="checkpoint-time">~[X] min</span>
        </div>
      </div>
    </div>
    
    <!-- Phases 3-4 as needed -->
  </div>
</section>
```

### Workflow Rules

- Autonomous mode: Skip this section entirely
- Supervised mode: Required, shows all intervention points
- Total time commitment must be disclosed upfront

---

## Section 7: Named Outputs

```html
<section class="listing-outputs">
  <div class="section-header">
    <div class="label">What You Receive</div>
    <h2>Named outputs. <em>Specified.</em></h2>
  </div>
  
  <div class="outputs-list">
    <!-- Output 1 -->
    <div class="output-item">
      <div class="output-icon">[PDF/Email/Dashboard icon]</div>
      <div class="output-content">
        <h4 class="output-name">[Output Name]</h4>
        <p class="output-spec">[Format] · [Frequency/trigger] · [Brief description]</p>
      </div>
      <a href="#specimen" class="output-preview-link">See example →</a>
    </div>
    
    <!-- Output 2 -->
    <div class="output-item">
      <div class="output-icon">[Icon]</div>
      <div class="output-content">
        <h4 class="output-name">[Output Name]</h4>
        <p class="output-spec">[Format] · [Frequency] · [Description]</p>
      </div>
      <a href="#specimen" class="output-preview-link">See example →</a>
    </div>
    
    <!-- All named outputs listed -->
  </div>
</section>
```

### Output Specification Format

```
[Output Name] — [Format] · [Frequency] · [Description]
```

Examples:
- "Regulatory Alert — Email · Real-time · Immediate notification when relevant bulletin published"
- "Weekly Digest — PDF · Every Monday 9am · Summary of all regulatory activity for monitored states"
- "Experiment Brief — PDF · Once at kickoff · Formalized hypothesis and experiment structure"

---

## Section 8: Ratings & Reviews

```html
<section class="listing-reviews" id="reviews">
  <div class="section-header">
    <div class="label">Reviews</div>
    <h2>From verified <em>hirers.</em></h2>
  </div>
  
  <!-- Rating Summary -->
  <div class="reviews-summary">
    <div class="rating-large">
      <span class="rating-number">[4.8]</span>
      <span class="rating-stars-large">★★★★★</span>
    </div>
    <div class="rating-breakdown">
      <div class="rating-bar">
        <span class="rating-label">Effectiveness</span>
        <div class="rating-bar-fill" style="width: [X]%"></div>
        <span class="rating-value">[4.9]</span>
      </div>
      <div class="rating-bar">
        <span class="rating-label">Output Quality</span>
        <div class="rating-bar-fill" style="width: [X]%"></div>
        <span class="rating-value">[4.8]</span>
      </div>
      <div class="rating-bar">
        <span class="rating-label">Time Saved</span>
        <div class="rating-bar-fill" style="width: [X]%"></div>
        <span class="rating-value">[4.7]</span>
      </div>
      <div class="rating-bar">
        <span class="rating-label">Ease of Use</span>
        <div class="rating-bar-fill" style="width: [X]%"></div>
        <span class="rating-value">[4.8]</span>
      </div>
      <div class="rating-bar">
        <span class="rating-label">Value</span>
        <div class="rating-bar-fill" style="width: [X]%"></div>
        <span class="rating-value">[4.6]</span>
      </div>
    </div>
    <p class="reviews-count">[23] verified hires</p>
  </div>
  
  <!-- Individual Reviews -->
  <div class="reviews-list">
    <!-- Review 1 -->
    <div class="review-card">
      <div class="review-header">
        <span class="review-stars">★★★★★</span>
        <span class="review-verified">✓ Verified Hire</span>
        <span class="review-date">[3 months ago]</span>
      </div>
      <p class="review-text">"[Actual review text from hirer, min 50 characters]"</p>
      <div class="review-author">
        <span class="author-name">[Name]</span>
        <span class="author-title">[Title] @ [Company]</span>
      </div>
    </div>
    
    <!-- Review 2, 3, etc. -->
  </div>
  
  <a href="#all-reviews" class="reviews-see-all">See all [23] reviews →</a>
</section>
```

### Review Display Rules

- Only show reviews with VERIFIED HIRE badge
- Minimum 50 characters for review text
- Display most helpful reviews first (voted by other hirers)
- Show 3 reviews on listing, "See all" expands

### For New Staff (No Reviews Yet)

```html
<div class="reviews-empty">
  <p>No reviews yet — be the first to hire and share your experience.</p>
  <a href="#hire" class="btn btn-outline">Start Free Trial</a>
</div>
```

---

## Section 9: Pricing

```html
<section class="listing-pricing" id="pricing">
  <div class="section-header">
    <div class="label">Pricing</div>
    <h2>Simple. <em>Transparent.</em></h2>
  </div>
  
  <div class="pricing-cards">
    <!-- Trial -->
    <div class="pricing-card pricing-trial">
      <div class="pricing-card-header">
        <h3>Trial</h3>
        <p class="pricing-card-tagline">See it work before you commit</p>
      </div>
      <div class="pricing-card-price">
        <span class="price-amount">Free</span>
        <span class="price-period">14 days</span>
      </div>
      <ul class="pricing-features">
        <li>Full access to all features</li>
        <li>Real outputs delivered</li>
        <li>No credit card required</li>
        <li>Cancel anytime</li>
      </ul>
      <a href="#hire" class="btn btn-outline">Start Free Trial</a>
    </div>
    
    <!-- Standard -->
    <div class="pricing-card pricing-standard">
      <div class="pricing-card-header">
        <h3>Standard</h3>
        <p class="pricing-card-tagline">For ongoing operations</p>
      </div>
      <div class="pricing-card-price">
        <span class="price-amount">$[X,XXX]</span>
        <span class="price-period">/month</span>
      </div>
      <div class="pricing-annual">
        Annual: $[XX,XXX] <span class="pricing-save">(save 15%)</span>
      </div>
      <ul class="pricing-features">
        <li>Everything in Trial</li>
        <li>Priority support</li>
        <li>Custom configurations</li>
        <li>Usage analytics</li>
      </ul>
      <a href="#hire" class="btn btn-primary">Hire [Name]</a>
    </div>
    
    <!-- Enterprise (optional) -->
    <div class="pricing-card pricing-enterprise">
      <div class="pricing-card-header">
        <h3>Enterprise</h3>
        <p class="pricing-card-tagline">For larger organizations</p>
      </div>
      <div class="pricing-card-price">
        <span class="price-amount">Custom</span>
      </div>
      <ul class="pricing-features">
        <li>Multiple team members</li>
        <li>Dedicated support</li>
        <li>Custom integrations</li>
        <li>SLA guarantees</li>
      </ul>
      <a href="mailto:hire@tryjoyn.me" class="btn btn-outline">Contact Us</a>
    </div>
  </div>
</section>
```

### Pricing Rules

- Trial always 14 days, always free, no credit card
- Price displayed prominently, no hidden fees
- Annual discount if offered must show savings
- Enterprise tier optional

---

## Section 10: Built By

```html
<section class="listing-creator">
  <div class="section-header">
    <div class="label">Built By</div>
  </div>
  
  <div class="creator-card">
    <img src="[creator-photo.jpg]" alt="[Creator Name]" class="creator-photo">
    <div class="creator-info">
      <h3 class="creator-name">[Creator Name]</h3>
      <p class="creator-credentials">[X] years in [Vertical/Domain]</p>
      <p class="creator-bio">"[One sentence about their expertise and why they built this staff.]"</p>
    </div>
  </div>
</section>
```

### Creator Attribution Rules

- Photo: 200x200 min, professional headshot
- Years: Verified domain experience
- Bio: One sentence, authentic voice

---

## Section 11: Compliance & Security

```html
<section class="listing-compliance">
  <div class="section-header">
    <div class="label">Compliance & Security</div>
  </div>
  
  <div class="compliance-badges">
    <div class="compliance-item">
      <span class="compliance-icon">[Shield]</span>
      <div class="compliance-content">
        <h4>Data Protection</h4>
        <p>GDPR compliant · Data processed in [region] · [X]-day retention</p>
      </div>
    </div>
    
    <div class="compliance-item">
      <span class="compliance-icon">[Lock]</span>
      <div class="compliance-content">
        <h4>Security</h4>
        <p>SOC 2 aligned · Encrypted at rest and in transit · No data sharing</p>
      </div>
    </div>
    
    <div class="compliance-item">
      <span class="compliance-icon">[Eye]</span>
      <div class="compliance-content">
        <h4>AI Transparency</h4>
        <p>[Risk level] risk · Human oversight at [points] · Explainable outputs</p>
      </div>
    </div>
  </div>
  
  <a href="#compliance-details" class="compliance-link">View full compliance documentation →</a>
</section>
```

---

## Section 12: Hire Form

```html
<section class="listing-hire" id="hire">
  <div class="section-header">
    <div class="label">Hire [Name]</div>
    <h2>Start your <em>trial.</em></h2>
  </div>
  
  <form class="hire-form" id="hire-form">
    <!-- Standard Fields (all staff) -->
    <div class="form-group">
      <label class="form-label" for="hire-name">Your name *</label>
      <input class="form-input" type="text" id="hire-name" name="name" required>
    </div>
    
    <div class="form-group">
      <label class="form-label" for="hire-email">Work email *</label>
      <input class="form-input" type="email" id="hire-email" name="email" required>
    </div>
    
    <div class="form-group">
      <label class="form-label" for="hire-company">Company name *</label>
      <input class="form-input" type="text" id="hire-company" name="company" required>
    </div>
    
    <div class="form-group">
      <label class="form-label" for="hire-role">Your role *</label>
      <input class="form-input" type="text" id="hire-role" name="role" required>
    </div>
    
    <!-- Staff-Specific Fields (varies by staff) -->
    <!-- IRIS EXAMPLE: States to monitor -->
    <div class="form-group">
      <label class="form-label" for="hire-states">States to monitor *</label>
      <input class="form-input" type="text" id="hire-states" name="states" 
             placeholder="e.g., Florida, Texas, California" required>
      <p class="form-hint">Comma-separated list of US states</p>
    </div>
    
    <!-- PROBE EXAMPLE: Innovation hypothesis -->
    <div class="form-group">
      <label class="form-label" for="hire-hypothesis">Innovation hypothesis *</label>
      <textarea class="form-textarea" id="hire-hypothesis" name="hypothesis" 
                placeholder="What are you trying to prove or disprove?" required></textarea>
    </div>
    
    <!-- Submit -->
    <button type="submit" class="form-submit">Start Free Trial →</button>
    <p class="form-note">14-day free trial · No credit card required · Cancel anytime</p>
  </form>
  
  <!-- Success State -->
  <div class="hire-success" id="hire-success" style="display:none;">
    <div class="success-icon">✓</div>
    <h3>Trial started!</h3>
    <p>Check your email for login details. [Name] will be ready within 10 minutes.</p>
  </div>
</section>
```

---

## Staff-Specific Form Fields

### Iris (Insurance Regulatory)

```html
<div class="form-group">
  <label class="form-label" for="hire-states">States to monitor *</label>
  <input class="form-input" type="text" id="hire-states" name="states" required>
</div>

<div class="form-group">
  <label class="form-label" for="hire-lines">Lines of business</label>
  <select class="form-select" id="hire-lines" name="lines">
    <option value="">Select primary line</option>
    <option value="P&C">Property & Casualty</option>
    <option value="L&H">Life & Health</option>
    <option value="Both">Both</option>
  </select>
</div>
```

### Probe (Innovation Experiments)

```html
<div class="form-group">
  <label class="form-label" for="hire-org-type">Organisation type *</label>
  <select class="form-select" id="hire-org-type" name="org_type" required>
    <option value="">Select type</option>
    <option value="carrier">Carrier</option>
    <option value="mga">MGA/MGU</option>
    <option value="broker">Broker</option>
    <option value="insurtech">Insurtech</option>
    <option value="other">Other</option>
  </select>
</div>

<div class="form-group">
  <label class="form-label" for="hire-hypothesis">Innovation hypothesis *</label>
  <textarea class="form-textarea" id="hire-hypothesis" name="hypothesis" required></textarea>
</div>
```

### TDD Practice Team (Tech Due Diligence)

```html
<div class="form-group">
  <label class="form-label" for="hire-target">Target company *</label>
  <input class="form-input" type="text" id="hire-target" name="target_company" required>
</div>

<div class="form-group">
  <label class="form-label" for="hire-engagement">Engagement type *</label>
  <select class="form-select" id="hire-engagement" name="engagement_type" required>
    <option value="">Select type</option>
    <option value="pre-loi">Pre-LOI screening</option>
    <option value="full-dd">Full due diligence</option>
    <option value="red-flag">Red flag review</option>
  </select>
</div>

<div class="form-group">
  <label class="form-label" for="hire-brief">Brief *</label>
  <textarea class="form-textarea" id="hire-brief" name="brief" required
            placeholder="What do you need to know about this target?"></textarea>
</div>
```

---

## File Naming Convention

```
marketplace/
├── index.html                          # Marketplace listing grid
├── [staff-slug].html                   # Individual listing page
├── [staff-slug]-hire.html              # Dedicated hire form (optional)
└── assets/
    └── [staff-slug]/
        ├── icon.png                    # 512x512 staff icon
        ├── hero.png                    # Hero screenshot
        ├── screenshot-1.png            # Gallery image 1
        ├── screenshot-2.png            # Gallery image 2
        ├── screenshot-3.png            # Gallery image 3
        ├── demo.mp4                    # Demo video
        └── creator.jpg                 # Creator headshot
```

---

## CSS Classes Reference

All classes follow JOYN-DESIGN-SPEC.md. Key listing-specific classes:

| Class | Usage |
|-------|-------|
| `.listing-hero` | Hero section container |
| `.listing-vertical-label` | Vertical tag (gold, DM Mono) |
| `.listing-mode-badge` | Mode indicator |
| `.listing-mode-autonomous` | Filled badge |
| `.listing-mode-supervised` | Outlined badge |
| `.listing-name` | Staff name (Cormorant, h1) |
| `.listing-tagline` | One-sentence description |
| `.roi-chip` | ROI value chip |
| `.task-card` | Core task card |
| `.workflow-phase` | Workflow phase item |
| `.output-item` | Named output row |
| `.review-card` | Individual review |
| `.pricing-card` | Pricing tier card |
| `.creator-card` | Builder attribution |
| `.compliance-item` | Compliance badge |
| `.hire-form` | Intake form |

---

*Joyn · tryjoyn.me · JOYN-LISTING-TEMPLATE.md*
*The standard every listing page follows.*
