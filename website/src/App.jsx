import { useState } from "react";

import {
  Accessibility,
  ArrowRight,
  BookOpen,
  Check,
  Eye,
  Globe,
  Headphones,
  Landmark,
  Menu,
  Mic,
  Phone,
  Play,
  ShieldCheck,
  Sparkles,
  Users,
  Volume2,
  WifiOff,
  X,
} from "lucide-react";

import "./App.css";

/* =========================================================
   SCROLL HELPER
========================================================= */

function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({
    behavior: "smooth",
  });
}

/* =========================================================
   ACCESSIBILITY MENU
   Only READ ALOUD is retained
========================================================= */

function AccessibilityMenu() {
  const [open, setOpen] = useState(false);
  const [reading, setReading] = useState(false);

  const readPageAloud = () => {
    if (!("speechSynthesis" in window)) {
      alert(
        "Text-to-speech is not supported by this browser."
      );
      return;
    }

    if (reading) {
      window.speechSynthesis.cancel();
      setReading(false);
      return;
    }

    const text = document.body.innerText;

    const speech = new SpeechSynthesisUtterance(text);

    speech.lang = "en-KE";
    speech.rate = 0.9;
    speech.pitch = 1;

    speech.onstart = () => {
      setReading(true);
    };

    speech.onend = () => {
      setReading(false);
    };

    speech.onerror = () => {
      setReading(false);
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(speech);
  };

  const closeAccessibilityMenu = () => {
    if (reading) {
      window.speechSynthesis.cancel();
      setReading(false);
    }

    setOpen(false);
  };

  return (
    <div
      className={`accessibility-widget ${
        open ? "is-open" : ""
      }`}
    >
      {/* =====================================================
          FLOATING ACCESSIBILITY BUTTON
          ===================================================== */}

      <button
        className="accessibility-trigger"
        onClick={() => setOpen(!open)}
        aria-label={
          open
            ? "Close accessibility menu"
            : "Open accessibility menu"
        }
        aria-expanded={open}
      >
        {open ? (
          <X
            size={30}
            strokeWidth={2.5}
          />
        ) : (
          <Accessibility
            size={32}
            strokeWidth={2.2}
          />
        )}
      </button>

      {/* =====================================================
          ACCESSIBILITY PANEL
          ===================================================== */}

      {open && (
        <div className="accessibility-panel">

          {/* HEADER */}

          <div className="accessibility-panel-header">

            <div className="accessibility-title">

              <span>
                Accessibility Menu
              </span>

              <small>
                FAHAMIKA · Access beyond sight.
              </small>

            </div>

            <button
              className="accessibility-close"
              onClick={closeAccessibilityMenu}
              aria-label="Close accessibility menu"
            >
              <X size={25} />
            </button>

          </div>

          {/* =================================================
              READ ALOUD
              ================================================= */}

          <button
            className={
              reading
                ? "accessibility-read-button reading"
                : "accessibility-read-button"
            }
            onClick={readPageAloud}
          >

            <span className="read-icon">

              <Volume2
                size={28}
                strokeWidth={2}
              />

            </span>

            <span className="read-content">

              <strong>

                {reading
                  ? "Stop reading"
                  : "Read page aloud"}

              </strong>

              <small>

                {reading
                  ? "Fahamika is reading the page"
                  : "Listen to the information"}

              </small>

            </span>

            <span className="read-arrow">

              {reading ? (
                <X size={20} />
              ) : (
                <Play
                  size={17}
                  fill="currentColor"
                />
              )}

            </span>

          </button>

          {/* =================================================
              ACCESSIBILITY FOOTER
              ================================================= */}

          <div className="accessibility-footer">

            <span>
              FAHAMIKA
            </span>

            <strong>
              Access beyond sight.
            </strong>

          </div>

        </div>
      )}

    </div>
  );
}

/* =========================================================
   MAIN APP
========================================================= */

function App() {

  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => {
    setMenuOpen(false);
  };

  return (

    <div className="site">

      {/* ===================================================
          ACCESSIBILITY MENU
          =================================================== */}

      <AccessibilityMenu />

      {/* ===================================================
          ANNOUNCEMENT
          =================================================== */}

      <div className="announcement">

        <span className="pulse-dot"></span>

        Accessible civic information for everyone

        <a
          href="tel:0730731120"
          className="announcement-call"
          aria-label="Call Fahamika on 0730731120"
        >
          Call: 0730731120

          <Phone size={14} />

        </a>

      </div>

      {/* ===================================================
          NAVIGATION
          =================================================== */}

      <header className="navbar">

        <div className="nav-container">

          {/* LOGO */}

          <button
            className="logo"
            onClick={() =>
              scrollToSection("home")
            }
          >

            <span className="logo-icon">

              <Volume2 size={20} />

            </span>

            <span>
              Fahamika

              <span className="logo-dot">
                .
              </span>

            </span>

          </button>

          {/* NAVIGATION LINKS */}

          <nav
            className={
              menuOpen
                ? "nav-links mobile-open"
                : "nav-links"
            }
          >

            <button
              onClick={() => {
                scrollToSection("problem");
                closeMenu();
              }}
            >
              Why Fahamika
            </button>

            <button
              onClick={() => {
                scrollToSection("how");
                closeMenu();
              }}
            >
              How it works
            </button>

            <button
              onClick={() => {
                scrollToSection("accessibility");
                closeMenu();
              }}
            >
              Accessibility
            </button>

            <button
              onClick={() => {
                scrollToSection("trust");
                closeMenu();
              }}
            >
              Trust
            </button>

            <a
              className="nav-cta"
              href="tel:0730731120"
              onClick={closeMenu}
              aria-label="Call Fahamika on 0730731120"
            >

              Call Fahamika

              <Phone size={16} />

            </a>

          </nav>

          {/* MOBILE MENU */}

          <button
            className="menu-button"
            onClick={() =>
              setMenuOpen(!menuOpen)
            }
            aria-label="Open menu"
          >

            {menuOpen ? (
              <X />
            ) : (
              <Menu />
            )}

          </button>

        </div>

      </header>

      {/* ===================================================
          HERO
          =================================================== */}

      <section
        id="home"
        className="hero"
      >

        <div className="hero-glow glow-one"></div>

        <div className="hero-glow glow-two"></div>

        <div className="container hero-grid">

          {/* HERO TEXT */}

          <div className="hero-content fade-up">

            {/* =============================================
                FAHAMIKA MANTRA
                ============================================= */}

            <div className="hero-mantra">

              <span className="mantra-brand">
                FAHAMIKA
              </span>

              <span className="mantra-divider">
                •
              </span>

              <strong className="mantra-text">
                Access beyond sight.
              </strong>

            </div>

            {/* EYEBROW */}

            <div className="eyebrow">

              <Sparkles size={15} />

              Civic information, made accessible

            </div>

            {/* MAIN HEADING */}

            <h1>

              Understand your rights.

              <br />

              <em>
                Be heard.
              </em>

            </h1>

            {/* DESCRIPTION */}

            <p className="hero-description">

              Fahamika makes Kenyan civic
              information from trusted sources easier to access,
              understand and act on through a simple phone call. 

            </p>

            {/* BUTTONS */}

            <div className="hero-buttons">

              <a
                className="button primary"
                href="tel:0730731120"
                aria-label="Call Fahamika on 0730731120"
              >

                Call Fahamika

                <Phone size={18} />

              </a>

              <button
                className="button secondary"
                onClick={() =>
                  scrollToSection("how")
                }
              >

                <Play size={17} />

                See how it works

              </button>

            </div>

            {/* PHONE NUMBER */}

            <div className="hero-phone" style={{ marginTop: "20px" }}>

              <Phone size={17} style={{ marginRight: "6px" }} />

              <span style={{ marginRight: "6px" }}>
                Call Fahamika: 
              </span>

              <a
                href="tel:0730731120"
                aria-label="Call Fahamika on 0730731120"
              >
                0730731120
              </a>

            </div>

            {/* PROOF */}

            <div className="hero-proof">

              <span>

                <Check size={15} />

                Verified sources

              </span>

              <span>

                <Check size={15} />

                Voice first

              </span>

              <span>

                <Check size={15} />

                Low-data

              </span>

            </div>

          </div>

          {/* =================================================
              HERO PHONE
              ================================================= */}

          <div className="hero-visual fade-up delay-one">

            <div className="orbit orbit-one"></div>

            <div className="orbit orbit-two"></div>

            <div className="phone">

              <div className="phone-header">

                <div>

                  <small>
                    FAHAMIKA
                  </small>

                  <strong>
                    Civic Assistant
                  </strong>

                </div>

                <div className="live-status">

                  <span></span>

                  LIVE

                </div>

              </div>

              <div className="conversation">

                {/* QUESTION */}

                <div className="question-bubble">

                  What are my rights as a
                  person with a disability?

                </div>

                {/* ANSWER */}

                <div className="answer-bubble">

                  <div className="answer-title">

                    <span className="mini-logo">

                      <Volume2 size={12} />

                    </span>

                    Fahamika

                  </div>

                  <p>

                    You have the right to equal
                    access to public services
                    and opportunities.

                  </p>

                  <div className="listen-button">

                    <Volume2 size={15} />

                    Voice response

                  </div>

                </div>

                {/* VERIFIED */}

                <div className="verified-chip">

                  <ShieldCheck size={14} />

                  Grounded in verified civic
                  information

                </div>

              </div>

            </div>

            {/* FLOATING CARD 1 */}

            <div className="floating-card card-one">

              <Eye size={19} />

              <div>

                <strong>
                  Voice first
                </strong>

                <small>
                  Designed beyond sight
                </small>

              </div>

            </div>

            {/* FLOATING CARD 2 */}

            <div className="floating-card card-two">

              <Phone size={19} />

              <div>

                <strong>
                  IVR ready
                </strong>

                <small>
                  Works on feature phones
                </small>

              </div>

            </div>

          </div>

        </div>

        {/* SCROLL */}

        <div className="scroll-indicator">

          <span></span>

          Scroll to explore

        </div>

      </section>

      {/* ===================================================
          MARQUEE
          =================================================== */}

      <div className="marquee">

        <div className="marquee-track">

          {[
            "VOICE",
            "IVR",
            "CIVIC RIGHTS",
            "ACCESSIBILITY",
            "TRUST",
            "PARTICIPATION",
            "VOICE",
            "IVR",
            "CIVIC RIGHTS",
            "ACCESSIBILITY",
          ].map((item, index) => (

            <span key={index}>

              {item}

              <b>
                ✦
              </b>

            </span>

          ))}

        </div>

      </div>

      {/* ===================================================
          PROBLEM
          =================================================== */}

      <section
        id="problem"
        className="section white"
      >

        <div className="container">

          <div className="section-heading fade-up">

            <div className="eyebrow">
              The problem
            </div>

            <h2>

              Information exists.

              <br />

              <em>
                Access doesn't.
              </em>

            </h2>

            <p>

              Civic information can be available
              while still being practically
              unreachable to people who cannot rely
              on visual interfaces or accessible
              digital services.

            </p>

          </div>

          <div className="stats-grid">

            <Stat
              number="36.4%"
              title="of PWDs"
              text="are visually impaired in Kenya"
            />

            <Stat
              number="4%"
              title="of institutions"
              text="met the cited constitutional inclusion requirement in an accessibility assessment."
            />

            <Stat
              number="0"
              title="audio descriptions"
              text="were recorded across government websites evaluated in one accessibility assessment."
            />

          </div>

        </div>

      </section>

      {/* ===================================================
          ACCESSIBILITY
          =================================================== */}

      <section
        id="accessibility"
        className="section beige"
      >

        <div className="container split">

          <div className="fade-up">

            <div className="eyebrow">
              Accessibility by design
            </div>

            <h2>

              Not an add-on.

              <br />

              <em>
                The product.
              </em>

            </h2>

            <p>

              Fahamika starts from the user's access
              needs. Instead of expecting everyone
              to use the same interface, it makes
              civic information available through
              a phone call.

            </p>

            <div className="feature-list">

              <Feature
                icon={<Eye />}
                title="For blind & low vision users"
                text="Ask questions and hear responses without depending on a screen."
              />

              <Feature
                icon={<Phone />}
                title="Feature-phone friendly"
                text="IVR allows users to access information without a smartphone or visual interface."
              />

              <Feature
                icon={<WifiOff />}
                title="Low-data access"
                text="Voice interaction over a phone call can reach communities where internet access is limited."
              />

            </div>

          </div>

          <div className="accessibility-visual fade-up delay-one">

            <div className="access-circle">

              <Volume2 size={42} />

            </div>

            <div className="access-center">

              FAHAMIKA

            </div>

            <div className="access-label label-top">

              <Mic size={17} />

              <div>

                <strong>
                  VOICE
                </strong>

                <small>
                  Speak naturally
                </small>

              </div>

            </div>

            <div className="access-label label-right">

              <Phone size={17} />

              <div>

                <strong>
                  IVR
                </strong>

                <small>
                  Call to access
                </small>

              </div>

            </div>

            <div className="access-label label-bottom">

              <Headphones size={17} />

              <div>

                <strong>
                  LISTEN
                </strong>

                <small>
                  Hear the response
                </small>

              </div>

            </div>

          </div>

        </div>

      </section>

      {/* ===================================================
          HOW IT WORKS
          =================================================== */}

      <section
        id="how"
        className="section dark"
      >

        <div className="container">

          <div className="section-heading light fade-up">

            <div className="eyebrow">
              How Fahamika works
            </div>

            <h2>

              AI works behind the scenes.

              <br />

              <em>
                Access comes first.
              </em>

            </h2>

            <p>

              Fahamika uses AI as an accessibility
              layer between people and trusted civic
              information — not as a replacement
              for it.

            </p>

          </div>

          <div className="steps">

            <Step
              number="01"
              icon={<Mic />}
              title="Ask"
              text="Ask a civic question naturally using your voice."
            />

            <Step
              number="02"
              icon={<BookOpen />}
              title="Retrieve"
              text="Fahamika finds relevant information from approved civic sources."
            />

            <Step
              number="03"
              icon={<Sparkles />}
              title="Simplify"
              text="AI transforms complex language into a simpler explanation."
            />

            <Step
              number="04"
              icon={<Volume2 />}
              title="Listen"
              text="The answer is converted into speech and delivered back to the user."
            />

          </div>

        </div>

      </section>

      {/* ===================================================
          RESPONSIBLE AI
          =================================================== */}

      <section
        id="trust"
        className="section white"
      >

        <div className="container split trust-section">

          <div className="trust-graphic fade-up">

            <div className="shield-icon">

              <ShieldCheck size={34} />

            </div>

            <div className="trust-lines">

              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>

            </div>

            <div className="verified">

              <Check size={16} />

              Source verified

            </div>

          </div>

          <div className="fade-up delay-one">

            <div className="eyebrow">
              Responsible AI
            </div>

            <h2>

              Make information easier.

              <br />

              <em>
                Never less trustworthy.
              </em>

            </h2>

            <p>

              Fahamika keeps authoritative civic
              information at the centre. AI helps
              people understand and access that
              information; it does not replace
              the source.

            </p>

            <div className="trust-list">

              <Trust
                title="Verified sources"
                text="Responses are grounded in approved civic and government publications."
              />

              <Trust
                title="Traceability"
                text="Answers can be connected back to the information they came from."
              />

              <Trust
                title="No guessing"
                text="When reliable information is unavailable, Fahamika should say so."
              />

              <Trust
                title="Legal safeguards"
                text="Legally sensitive simplifications should undergo formal review."
              />

            </div>

          </div>

        </div>

      </section>

      {/* ===================================================
          SOURCES
          =================================================== */}

      <section className="section sources">

        <div className="container centered">

          <div className="eyebrow fade-up">
            Trusted foundation
          </div>

          <h2 className="fade-up">

            AI doesn't replace the source.

            <br />

            <em>
              It opens the door to it.
            </em>

          </h2>

          <p className="source-description fade-up">

            Fahamika uses authoritative Kenyan civic
            information as its foundation and AI as
            the accessibility layer.

          </p>

          <div className="source-grid fade-up delay-one">

            <Source
              icon={<Landmark />}
              title="Constitution of Kenya"
            />

            <Source
              icon={<Globe />}
              title="IEBC"
            />

            <Source
              icon={<Users />}
              title="NCPWD"
            />

            <Source
              icon={<BookOpen />}
              title="Official civic publications"
            />

          </div>

        </div>

      </section>

      {/* ===================================================
          FINAL CTA
          =================================================== */}

      <section className="final-section">

        <div className="final-glow"></div>

        <div className="container final-content">

          <div className="eyebrow light">
            Fahamika
          </div>

          <h2>

            When information is accessible
            beyond sight, participation
            becomes possible.

          </h2>

          <p>

            Building a more accessible way for
            Kenyans with disabilities to understand
            their rights and participate in civic life.

          </p>

          <a
            className="button white-button"
            href="tel:0730731120"
            aria-label="Call Fahamika on 0730731120"
          >

            Call Fahamika

            <Phone size={18} />

          </a>

          <div className="final-phone-number">

            <Phone size={18} style={{ marginRight: "6px" }}/>

            <span>
              0730731120
            </span>

          </div>

        </div>

      </section>

      {/* ===================================================
          FOOTER
          =================================================== */}

      <footer>

        <div className="container footer-content">

          <button
            className="footer-logo"
            onClick={() =>
              scrollToSection("home")
            }
          >

            <span className="logo-icon">

              <Volume2 size={18} />

            </span>

            Fahamika

            <span>
              .
            </span>

          </button>

          <p>
            Civic information, accessible to everyone.
          </p>

          <a
            className="footer-phone"
            href="tel:0730731120"
            aria-label="Call Fahamika on 0730731120"
          >
            <Phone size={15} style={{ marginRight: "6px" }} />
            0730731120
          </a>

          <span className="copyright">
            © 2026 Fahamika
          </span>

        </div>

      </footer>

    </div>

  );
}

/* =========================================================
   STAT COMPONENT
========================================================= */

function Stat({
  number,
  title,
  text,
}) {

  return (

    <div className="stat-card fade-up">

      <div className="stat-number">
        {number}
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

    </div>

  );
}

/* =========================================================
   FEATURE COMPONENT
========================================================= */

function Feature({
  icon,
  title,
  text,
}) {

  return (

    <div className="feature">

      <div className="feature-icon">
        {icon}
      </div>

      <div>

        <h3>
          {title}
        </h3>

        <p>
          {text}
        </p>

      </div>

    </div>

  );
}

/* =========================================================
   STEP COMPONENT
========================================================= */

function Step({
  number,
  icon,
  title,
  text,
}) {

  return (

    <div className="step">

      <div className="step-number">
        {number}
      </div>

      <div className="step-icon">
        {icon}
      </div>

      <h3>
        {title}
      </h3>

      <p>
        {text}
      </p>

    </div>

  );
}

/* =========================================================
   TRUST COMPONENT
========================================================= */

function Trust({
  title,
  text,
}) {

  return (

    <div className="trust-item">

      <div className="trust-check">

        <ShieldCheck size={17} />

      </div>

      <div>

        <h3>
          {title}
        </h3>

        <p>
          {text}
        </p>

      </div>

    </div>

  );
}

/* =========================================================
   SOURCE COMPONENT
========================================================= */

function Source({
  icon,
  title,
}) {

  return (

    <div className="source-card">

      <div className="source-icon">
        {icon}
      </div>

      <span>
        {title}
      </span>

    </div>

  );

}

/* =========================================================
   EXPORT
========================================================= */

export default App;