---
layout: page
title: Our Services
---

<style>
/* ── Reset & Base ──────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0d2137 !important;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* ── Hero Section ──────────────────────────────────────────────────────────── */
.services-hero {
  text-align: center;
  padding: 72px 24px 56px;
  background: radial-gradient(ellipse at 50% 0%, rgba(0,217,255,0.12) 0%, transparent 70%);
  border-bottom: 1px solid rgba(0,217,255,0.1);
  margin-bottom: 60px;
}
.services-hero h2 {
  font-size: 2.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #00D9FF 0%, #7C3AED 60%, #EC4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
  letter-spacing: -0.02em;
}
.services-hero p {
  font-size: 1.1rem;
  color: rgba(230,241,255,0.65) !important;
  max-width: 600px;
  margin: 0 auto 32px;
  line-height: 1.7;
}
.hero-cta {
  display: inline-block;
  background: linear-gradient(135deg, #00D9FF 0%, #7C3AED 100%);
  color: #0d2137 !important;
  font-weight: 700;
  font-size: 1rem;
  padding: 14px 36px;
  border-radius: 50px;
  text-decoration: none !important;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 4px 24px rgba(0,217,255,0.25);
}
.hero-cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 40px rgba(0,217,255,0.45);
}

/* ── Section Labels ────────────────────────────────────────────────────────── */
.section-label {
  text-align: center;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(0,217,255,0.7) !important;
  margin-bottom: 40px;
}

/* ── Services Grid ─────────────────────────────────────────────────────────── */
.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  padding: 0 16px 80px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ── Service Card ──────────────────────────────────────────────────────────── */
.svc-card {
  position: relative;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 32px 28px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  overflow: hidden;
}
.svc-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--card-accent, linear-gradient(90deg,#00D9FF,#7C3AED));
  border-radius: 20px 20px 0 0;
}
.svc-card:hover {
  transform: translateY(-12px);
  border-color: rgba(0,217,255,0.45);
  background: rgba(0,217,255,0.06);
  box-shadow: 0 20px 50px rgba(0,217,255,0.12);
}

/* ── Card variants ─────────────────────────────────────────────────────────── */
.svc-card.cyan   { --card-accent: linear-gradient(90deg,#00D9FF,#00B4D8); }
.svc-card.cyan:hover { box-shadow: 0 20px 50px rgba(0,217,255,0.18); }

.svc-card.teal   { --card-accent: linear-gradient(90deg,#00B4D8,#0077B6); }
.svc-card.teal:hover { box-shadow: 0 20px 50px rgba(0,180,216,0.18); }

.svc-card.purple { --card-accent: linear-gradient(90deg,#7C3AED,#9F67FA); }
.svc-card.purple:hover { border-color: rgba(124,58,237,0.5); background: rgba(124,58,237,0.06); box-shadow: 0 20px 50px rgba(124,58,237,0.18); }

.svc-card.pink   { --card-accent: linear-gradient(90deg,#EC4899,#F472B6); }
.svc-card.pink:hover { border-color: rgba(236,72,153,0.5); background: rgba(236,72,153,0.06); box-shadow: 0 20px 50px rgba(236,72,153,0.18); }

.svc-card.enterprise-cyan  { --card-accent: linear-gradient(90deg,#00D9FF,#0077B6); }
.svc-card.enterprise-purple{ --card-accent: linear-gradient(90deg,#7C3AED,#EC4899); }

/* ── Card Content ──────────────────────────────────────────────────────────── */
.card-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(0,217,255,0.12);
  color: #00D9FF !important;
  margin-bottom: 18px;
}
.card-badge.purple { background: rgba(124,58,237,0.15); color: #9F67FA !important; }
.card-badge.pink   { background: rgba(236,72,153,0.15); color: #F472B6 !important; }
.card-badge.teal   { background: rgba(0,180,216,0.15);  color: #00D9FF !important; }

.card-icon {
  font-size: 2.4rem;
  margin-bottom: 16px;
  display: block;
  transition: transform 0.3s cubic-bezier(0.4,0,0.2,1);
}
.svc-card:hover .card-icon { transform: scale(1.1); }

.card-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #e6f1ff !important;
  margin-bottom: 10px;
}
.card-hook {
  font-size: 0.95rem;
  font-style: italic;
  color: rgba(0,217,255,0.85) !important;
  margin-bottom: 12px;
  font-weight: 500;
}
.card-desc {
  font-size: 0.92rem;
  color: rgba(230,241,255,0.6) !important;
  line-height: 1.65;
  margin-bottom: 20px;
}
.card-benefits {
  list-style: none;
  margin-bottom: 24px;
}
.card-benefits li {
  font-size: 0.88rem;
  color: rgba(230,241,255,0.75) !important;
  padding: 4px 0;
}
.card-benefits li::before {
  content: '✓ ';
  color: #00D9FF;
  font-weight: 700;
}
.svc-card.purple .card-benefits li::before { color: #9F67FA; }
.svc-card.pink   .card-benefits li::before { color: #F472B6; }

.card-cta {
  display: inline-block;
  padding: 10px 24px;
  border-radius: 50px;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none !important;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  border: 1.5px solid rgba(0,217,255,0.5);
  color: #00D9FF !important;
  background: transparent;
}
.card-cta:hover {
  background: rgba(0,217,255,0.1);
  box-shadow: 0 0 16px rgba(0,217,255,0.25);
  transform: translateY(-2px);
}
.svc-card.purple .card-cta { border-color: rgba(124,58,237,0.5); color: #9F67FA !important; }
.svc-card.purple .card-cta:hover { background: rgba(124,58,237,0.1); box-shadow: 0 0 16px rgba(124,58,237,0.25); }
.svc-card.pink   .card-cta { border-color: rgba(236,72,153,0.5); color: #F472B6 !important; }
.svc-card.pink   .card-cta:hover { background: rgba(236,72,153,0.1); box-shadow: 0 0 16px rgba(236,72,153,0.25); }

/* ── Bottom CTA Banner ─────────────────────────────────────────────────────── */
.cta-banner {
  text-align: center;
  padding: 72px 24px;
  background: linear-gradient(135deg, rgba(0,217,255,0.08) 0%, rgba(124,58,237,0.08) 100%);
  border-top: 1px solid rgba(0,217,255,0.1);
  border-bottom: 1px solid rgba(124,58,237,0.1);
}
.cta-banner h2 {
  font-size: 2rem;
  font-weight: 800;
  color: #e6f1ff !important;
  margin-bottom: 12px;
}
.cta-banner p {
  color: rgba(230,241,255,0.6) !important;
  font-size: 1rem;
  margin-bottom: 32px;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}
</style>

<!-- Hero -->
<div class="services-hero">
  <h2>Discover Influencers That Drive Results</h2>
  <p>From instant profile audits to enterprise-grade infrastructure solutions, ATI &amp; AI powers the modern influencer economy.</p>
  <a href="https://calendly.com/automated-technical-insights/new-meeting" class="hero-cta">🚀 Start Your Free Audit</a>
</div>

<p class="section-label">Influencer Intelligence Platform</p>

<!-- Services Grid -->
<div class="services-grid">

  <!-- Card 1: Instant Social Audit -->
  <div class="svc-card cyan">
    <span class="card-badge">Influencer Intelligence</span>
    <span class="card-icon">🔍</span>
    <div class="card-title">Instant Social Audit</div>
    <div class="card-hook">Is that influencer worth the spend?</div>
    <div class="card-desc">Paste any Instagram handle and get instant insights on engagement rates, audience authenticity, demographics, and growth trends. Make data-driven decisions before you book.</div>
    <ul class="card-benefits">
      <li>Real-time profile analysis</li>
      <li>Authenticity scoring</li>
      <li>Demographic breakdown</li>
    </ul>
    <a href="https://calendly.com/automated-technical-insights/new-meeting" class="card-cta">Try Free Audit</a>
  </div>

  <!-- Card 2: Influencer Discovery -->
  <div class="svc-card teal">
    <span class="card-badge teal">Creator Search</span>
    <span class="card-icon">🔎</span>
    <div class="card-title">Influencer Discovery</div>
    <div class="card-desc">Find the perfect influencers for your brand. Filter by audience demographics, engagement rates, content themes, and more to identify creators who truly align with your goals.</div>
    <ul class="card-benefits">
      <li>Advanced filtering</li>
      <li>Audience matching</li>
      <li>Performance ranking</li>
    </ul>
    <a href="https://calendly.com/automated-technical-insights/new-meeting" class="card-cta">Explore Creators</a>
  </div>

  <!-- Card 3: Audience Analytics -->
  <div class="svc-card purple">
    <span class="card-badge purple">Data Intelligence</span>
    <span class="card-icon">👥</span>
    <div class="card-title">Audience Analytics</div>
    <div class="card-desc">Deep dive into influencer audience composition. Understand age, location, interests, and behavior patterns to ensure your message reaches the right people.</div>
    <ul class="card-benefits">
      <li>Demographic breakdowns</li>
      <li>Interest mapping</li>
      <li>Authenticity analysis</li>
    </ul>
    <a href="https://calendly.com/automated-technical-insights/new-meeting" class="card-cta">Analyze Audience</a>
  </div>

  <!-- Card 4: Influencer Scorecard -->
  <div class="svc-card pink">
    <span class="card-badge pink">Performance Ranking</span>
    <span class="card-icon">🏆</span>
    <div class="card-title">Influencer Scorecard</div>
    <div class="card-desc">Rate and compare influencers with our weighted scoring system. See who delivers the best ROI, and make confident booking decisions backed by data.</div>
    <ul class="card-benefits">
      <li>Weighted scoring</li>
      <li>Head-to-head comparison</li>
      <li>Historical tracking</li>
    </ul>
    <a href="https://calendly.com/automated-technical-insights/new-meeting" class="card-cta">View Scorecards</a>
  </div>

  <!-- Card 5: Merchant POS Solutions -->
  <div class="svc-card enterprise-cyan">
    <span class="card-badge">Enterprise</span>
    <span class="card-icon">💳</span>
    <div class="card-title">Merchant POS Solutions</div>
    <div class="card-desc">Strategic payment infrastructure for high-volume environments. We audit and optimize POS ecosystems to secure transaction flow and minimize processing friction through our partnership with <strong style="color:#00D9FF;">Beacon Payments</strong>.</div>
    <ul class="card-benefits">
      <li>99.9% uptime guarantee</li>
      <li>Real-time monitoring</li>
      <li>Seamless processing</li>
    </ul>
    <a href="https://calendly.com/automated-technical-insights/new-meeting" class="card-cta">Book Consultation</a>
  </div>

  <!-- Card 6: VMS Integration -->
  <div class="svc-card enterprise-purple">
    <span class="card-badge purple">Enterprise</span>
    <span class="card-icon">🎥</span>
    <div class="card-title">VMS Integration &amp; Maintenance</div>
    <div class="card-desc">Mission-critical Video Management System integration and 24/7 maintenance. We specialize in synchronizing legacy hardware with modern network protocols to prevent data loss and system downtime.</div>
    <ul class="card-benefits">
      <li>24/7 monitoring</li>
      <li>Zero downtime migration</li>
      <li>Legacy integration</li>
    </ul>
    <a href="https://calendly.com/automated-technical-insights/new-meeting" class="card-cta">Book Consultation</a>
  </div>

</div>

<!-- CTA Banner -->
<div class="cta-banner">
  <h2>Ready to Make Smarter Influencer Decisions?</h2>
  <p>Schedule a free strategy session and see how ATI &amp; AI can transform your influencer marketing program.</p>
  <a href="https://calendly.com/automated-technical-insights/new-meeting" class="hero-cta">📅 Book a Free Consultation</a>
</div>

