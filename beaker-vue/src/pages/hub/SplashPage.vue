<template>
  <div class="splash-page">
    <header class="splash-header">
      <div class="header-nav">
        <div class="logo-section">
          <BeakerLogo />
          <h2 class="brand-name">BeakerHub</h2>
        </div>
        <nav class="nav-links">
          <Button text size="small" @click="scrollToSection('features')">Features</Button>
          <Button text size="small" @click="scrollToSection('domains')">Domains</Button>
          <Button text size="small" @click="scrollToSection('how-it-works')">How It Works</Button>
          <Button outlined size="small" class="cta-button" @click="tryBeakerHub">Try BeakerHub</Button>
        </nav>
      </div>
    </header>

    <main class="splash-main">
      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-content">
          <h1 class="hero-title">
            AI-Powered Interactive Notebook Environments
          </h1>
          <p class="hero-subtitle">
            Accelerate your scientific computing and data analysis with specialized AI agents,
            seamless Jupyter integration, and domain-specific tools. All in a sandboxed,
            collaborative environment.
          </p>
          <div class="hero-actions">
            <Button size="large" class="primary-cta" @click="tryBeakerHub">
              Try BeakerHub
              <i class="pi pi-arrow-right"></i>
            </Button>
            <Button outlined size="large" @click="scrollToSection('how-it-works')">
              Learn More
            </Button>
          </div>
        </div>
        <div class="hero-visual">
          <div class="placeholder-image hero-demo">
            <div class="placeholder-content">
              <i class="pi pi-play-circle placeholder-icon"></i>
              <span>Interactive Demo</span>
              <p class="placeholder-alt">BeakerHub interface showing AI-powered notebook with code cells, visualizations, and chat interface</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section id="features" class="features-section">
        <div class="section-header">
          <h2 class="section-title">Powerful Features for Scientific Computing</h2>
          <p class="section-subtitle">Everything you need for advanced data analysis and research</p>
        </div>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-media">
              <div class="placeholder-content">
                <i class="pi pi-robot placeholder-icon"></i>
                <p class="placeholder-alt">AI agent helping with data analysis and code generation</p>
              </div>
            </div>
            <div class="feature-content">
              <h3 class="feature-title">AI-Powered Interactive Notebooks</h3>
              <p class="feature-description">
                Get intelligent assistance with code generation, data analysis, and problem-solving
                from specialized AI agents trained in scientific domains.
              </p>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-media">
              <div class="placeholder-content">
                <i class="pi pi-users placeholder-icon"></i>
                <p class="placeholder-alt">Various specialized agents for different scientific domains</p>
              </div>
            </div>
            <div class="feature-content">
              <h3 class="feature-title">Specialized Domain Agents</h3>
              <p class="feature-description">
                Access trained agents in data science, weather analysis, biomedicine, and more.
                Each agent comes with pre-configured tools and domain knowledge.
              </p>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-media">
              <div class="placeholder-content">
                <i class="pi pi-code placeholder-icon"></i>
                <p class="placeholder-alt">Seamless integration with Jupyter notebooks and Python packages</p>
              </div>
            </div>
            <div class="feature-content">
              <h3 class="feature-title">Full Jupyter Compatibility</h3>
              <p class="feature-description">
                Interoperable with Jupyter notebooks and all PyPI Python packages. 
                Import existing work or export your BeakerHub sessions.
              </p>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-media">
              <div class="placeholder-content">
                <i class="pi pi-desktop placeholder-icon"></i>
                <p class="placeholder-alt">Multiple interface options including notebook and chat views</p>
              </div>
            </div>
            <div class="feature-content">
              <h3 class="feature-title">Flexible Interfaces</h3>
              <p class="feature-description">
                Choose between traditional notebook interface or chat-based interaction.
                Work the way that feels most natural to you.
              </p>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-media">
              <div class="placeholder-content">
                <i class="pi pi-download placeholder-icon"></i>
                <p class="placeholder-alt">Export options to various formats including Jupyter notebooks</p>
              </div>
            </div>
            <div class="feature-content">
              <h3 class="feature-title">Export to Any Format</h3>
              <p class="feature-description">
                Export your work to Jupyter notebooks, Python scripts, or other formats.
                Your analysis is never locked in.
              </p>
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-media">
              <div class="placeholder-content">
                <i class="pi pi-wrench placeholder-icon"></i>
                <p class="placeholder-alt">Predefined agent tools and contexts ready to use</p>
              </div>
            </div>
            <div class="feature-content">
              <h3 class="feature-title">Ready-to-Use Tools</h3>
              <p class="feature-description">
                Start immediately with predefined agent tools and contexts.
                No setup required - we provide the integrations and API keys.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Use Cases Section -->
      <section class="use-cases-section">
        <div class="section-header">
          <h2 class="section-title">How You Can Use Beaker Agent</h2>
          <p class="section-subtitle">Real examples of problems BeakerHub can solve</p>
        </div>
        <div class="use-cases-grid">
          <Card class="use-case-card">
            <template #header>
              <div class="use-case-header">
                <i class="pi pi-chart-line use-case-icon"></i>
                <h3>Data Analysis Request</h3>
              </div>
            </template>
            <template #content>
              <div class="use-case-content">
                <p class="request">"Analyze this CSV file for trends and create visualizations"</p>
                <div class="arrow">
                  <i class="pi pi-arrow-down"></i>
                </div>
                <p class="solution">
                  <strong>BeakerHub provides:</strong> Automated data cleaning, statistical analysis,
                  multiple visualization types, and a comprehensive report with insights.
                </p>
              </div>
            </template>
          </Card>

          <Card class="use-case-card">
            <template #header>
              <div class="use-case-header">
                <i class="pi pi-cloud use-case-icon"></i>
                <h3>Weather Analysis</h3>
              </div>
            </template>
            <template #content>
              <div class="use-case-content">
                <p class="request">"Compare temperature patterns across different regions over the last decade"</p>
                <div class="arrow">
                  <i class="pi pi-arrow-down"></i>
                </div>
                <p class="solution">
                  <strong>BeakerHub provides:</strong> Climate data retrieval, statistical comparisons,
                  trend analysis, and publication-ready visualizations.
                </p>
              </div>
            </template>
          </Card>

          <Card class="use-case-card">
            <template #header>
              <div class="use-case-header">
                <i class="pi pi-heart use-case-icon"></i>
                <h3>Biomedical Research</h3>
              </div>
            </template>
            <template #content>
              <div class="use-case-content">
                <p class="request">"Analyze gene expression data and identify significant pathways"</p>
                <div class="arrow">
                  <i class="pi pi-arrow-down"></i>
                </div>
                <p class="solution">
                  <strong>BeakerHub provides:</strong> Bioinformatics pipeline setup, pathway analysis,
                  statistical significance testing, and interactive results exploration.
                </p>
              </div>
            </template>
          </Card>
        </div>
      </section>

      <!-- Domains Section -->
      <section id="domains" class="domains-section">
        <div class="section-header">
          <h2 class="section-title">Available Domains</h2>
          <p class="section-subtitle">Specialized expertise across multiple scientific fields</p>
        </div>
        <div class="domains-grid">
          <Card class="domain-card">
            <template #content>
              <div class="domain-content">
                <div class="domain-icon">
                  <i class="pi pi-chart-bar"></i>
                </div>
                <h3 class="domain-title">Data Science</h3>
                <p class="domain-description">
                  Statistical analysis, machine learning, data visualization, and predictive modeling
                  with popular libraries like pandas, scikit-learn, and matplotlib.
                </p>
                <div class="domain-tools">
                  <Tag value="pandas" />
                  <Tag value="scikit-learn" />
                  <Tag value="matplotlib" />
                  <Tag value="seaborn" />
                </div>
              </div>
            </template>
          </Card>

          <Card class="domain-card">
            <template #content>
              <div class="domain-content">
                <div class="domain-icon">
                  <i class="pi pi-cloud"></i>
                </div>
                <h3 class="domain-title">Weather & Climate</h3>
                <p class="domain-description">
                  Meteorological analysis, climate data processing, weather forecasting,
                  and environmental data visualization with specialized weather APIs.
                </p>
                <div class="domain-tools">
                  <Tag value="weather APIs" />
                  <Tag value="climate data" />
                  <Tag value="forecasting" />
                  <Tag value="GIS tools" />
                </div>
              </div>
            </template>
          </Card>

          <Card class="domain-card">
            <template #content>
              <div class="domain-content">
                <div class="domain-icon">
                  <i class="pi pi-heart"></i>
                </div>
                <h3 class="domain-title">Biomedicine</h3>
                <p class="domain-description">
                  Bioinformatics, genomics analysis, protein structure analysis,
                  and biomedical data processing with domain-specific tools and databases.
                </p>
                <div class="domain-tools">
                  <Tag value="BioPython" />
                  <Tag value="genomics" />
                  <Tag value="proteomics" />
                  <Tag value="pathway analysis" />
                </div>
              </div>
            </template>
          </Card>
        </div>
      </section>

      <!-- How It Works Section -->
      <section id="how-it-works" class="how-it-works-section">
        <div class="section-header">
          <h2 class="section-title">How It Works</h2>
          <p class="section-subtitle">Get started in minutes with our streamlined workflow</p>
        </div>
        <div class="workflow-steps">
          <div class="workflow-step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3 class="step-title">Create a Session</h3>
              <p class="step-description">
                Launch a sandboxed environment with your own filesystem and Python environment.
                Choose from our specialized domain contexts.
              </p>
            </div>
            <div class="step-visual">
              <div class="placeholder-content">
                <i class="pi pi-plus-circle placeholder-icon"></i>
                <p class="placeholder-alt">Creating a new BeakerHub session with domain selection</p>
              </div>
            </div>
          </div>

          <div class="workflow-step reverse">
            <div class="step-visual">
              <div class="placeholder-content">
                <i class="pi pi-code placeholder-icon"></i>
                <p class="placeholder-alt">Working in the BeakerHub interface with AI assistance</p>
              </div>
            </div>
            <div class="step-content">
              <h3 class="step-title">Code or Ask the AI</h3>
              <p class="step-description">
                Use the interface to write code directly or request the Beaker AI Agent to solve
                problems for you. Switch between notebook and chat modes as needed.
              </p>
            </div>
            <div class="step-number">2</div>
          </div>

          <div class="workflow-step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3 class="step-title">Export or Continue</h3>
              <p class="step-description">
                Export your work to Jupyter notebooks and other formats when ready,
                or continue working on BeakerHub. Your sessions are saved automatically.
              </p>
            </div>
            <div class="step-visual">
              <div class="placeholder-content">
                <i class="pi pi-download placeholder-icon"></i>
                <p class="placeholder-alt">Exporting BeakerHub work to various formats</p>
              </div>
            </div>
          </div>

          <div class="workflow-step reverse">
            <div class="step-visual">
              <div class="placeholder-content">
                <i class="pi pi-share-alt placeholder-icon"></i>
                <p class="placeholder-alt">Sharing BeakerHub sessions with team members</p>
              </div>
            </div>
            <div class="step-content">
              <h3 class="step-title">Share with Others</h3>
              <p class="step-description">
                Share your BeakerHub session with team members or collaborators.
                Everyone can view, edit, and build upon your work in real-time.
              </p>
            </div>
            <div class="step-number">4</div>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="cta-section">
        <Card class="cta-card">
          <template #content>
            <div class="cta-content">
              <h2 class="cta-title">Ready to Accelerate Your Research?</h2>
              <p class="cta-description">
                Join researchers and data scientists who are already using BeakerHub
                to streamline their workflow and discover new insights.
              </p>
              <Button size="large" class="primary-cta" @click="tryBeakerHub">
                Try BeakerHub Now
                <i class="pi pi-arrow-right"></i>
              </Button>
              <p class="cta-note">Free to use • Invite only • No setup required</p>
            </div>
          </template>
        </Card>
      </section>
    </main>

    <!-- Footer -->
    <footer class="splash-footer">
      <div class="footer-content">
        <div class="footer-section">
          <div class="footer-brand">
            <BeakerLogo />
            <h3>BeakerHub</h3>
          </div>
          <p class="footer-description">
            AI-powered interactive notebook environments for scientific computing and data analysis.
          </p>
        </div>
        
        <div class="footer-section">
          <h4 class="footer-title">Get Started</h4>
          <ul class="footer-links">
            <li><a href="#" @click="tryBeakerHub">Sign Up</a></li>
            <li><a href="#" @click="scrollToSection('features')">Features</a></li>
            <li><a href="https://jataware.github.io/beaker-kernel" target="_blank" rel="noopener">Documentation</a></li>
            <li><a href="#">FAQ</a></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="footer-title">Company</h4>
          <ul class="footer-links">
            <li><a href="#">Privacy Policy</a></li>
            <li><a href="#">Terms of Service</a></li>
            <li><a href="#">Contact Us</a></li>
            <li><a href="#">Blog</a></li>
          </ul>
        </div>

        <div class="footer-section">
          <h4 class="footer-title">Connect</h4>
          <ul class="footer-links">
            <li><a href="https://github.com/jataware/beaker-kernel" target="_blank" rel="noopener">GitHub</a></li>
            <li><a href="#">YouTube</a></li>
            <li><a href="#">Email</a></li>
            <li><a href="#">Phone</a></li>
          </ul>
        </div>
      </div>
      
      <div class="footer-bottom">
        <p>&copy; 2024 Jataware. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import BeakerLogo from '../../components/BeakerHubLogo.vue';

const router = useRouter();

function scrollToSection(sectionId: string) {
  const element = document.getElementById(sectionId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
}

function tryBeakerHub() {
  router.push('/');
}
</script>

<style lang="scss" scoped>
.splash-page {
  min-height: 100vh;
  background: var(--p-surface-a);
  color: var(--p-text-color);
}

.splash-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--p-surface-a);
  border-bottom: 1px solid var(--p-surface-border);
  backdrop-filter: blur(8px);

  .header-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    max-width: 1200px;
    margin: 0 auto;

    .logo-section {
      display: flex;
      align-items: center;
      gap: 0.5rem;

      .brand-name {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--p-primary-color);
        margin: 0;
      }
    }

    .nav-links {
      display: flex;
      align-items: center;
      gap: 1rem;

      .cta-button {
        color: var(--p-primary-color);
        border-color: var(--p-primary-color);
      }
    }
  }
}

.splash-main {
  .hero-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
    padding: 4rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
    min-height: 80vh;

    .hero-content {
      .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 1.5rem;
        color: var(--p-text-color);

        background: linear-gradient(135deg, var(--p-primary-color), var(--p-blue-600));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .hero-subtitle {
        font-size: 1.25rem;
        line-height: 1.6;
        color: var(--text-color-secondary);
        margin-bottom: 2rem;
      }

      .hero-actions {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;

        .primary-cta {
          background: var(--p-primary-color);
          border-color: var(--p-primary-color);
          color: white;
          
          i {
            margin-left: 0.5rem;
          }
        }
      }
    }

    .hero-visual {
      .hero-demo {
        position: relative;
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        aspect-ratio: 16/10;

        .demo-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }
    }
  }

  .features-section, .domains-section, .use-cases-section, .how-it-works-section {
    padding: 6rem 2rem;
    max-width: 1200px;
    margin: 0 auto;

    .section-header {
      text-align: center;
      margin-bottom: 4rem;

      .section-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: var(--p-text-color);
      }

      .section-subtitle {
        font-size: 1.25rem;
        color: var(--text-color-secondary);
        max-width: 600px;
        margin: 0 auto;
      }
    }
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;

    .feature-card {
      background: var(--p-surface-b);
      border-radius: 1rem;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
      transition: transform 0.2s, box-shadow 0.2s;
      border: 1px solid var(--p-surface-border);

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      }

      .feature-media {
        position: relative;
        height: 200px;
        overflow: hidden;
        background: var(--p-surface-c);
        border-radius: 0.5rem 0.5rem 0 0;
      }

      .feature-content {
        padding: 2rem;

        .feature-title {
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: var(--p-text-color);
        }

        .feature-description {
          color: var(--text-color-secondary);
          line-height: 1.6;
        }
      }
    }
  }

  .use-cases-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;

    .use-case-card {
      .use-case-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;

        .use-case-icon {
          font-size: 2rem;
          color: var(--p-primary-color);
        }

        h3 {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 600;
        }
      }

      .use-case-content {
        .request {
          font-style: italic;
          color: var(--text-color-secondary);
          margin-bottom: 1rem;
        }

        .arrow {
          text-align: center;
          margin: 1rem 0;
          color: var(--p-primary-color);
        }

        .solution {
          line-height: 1.6;
        }
      }
    }
  }

  .domains-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;

    .domain-card {
      .domain-content {
        text-align: center;

        .domain-icon {
          font-size: 3rem;
          color: var(--p-primary-color);
          margin-bottom: 1rem;
        }

        .domain-title {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 1rem;
        }

        .domain-description {
          color: var(--text-color-secondary);
          line-height: 1.6;
          margin-bottom: 1.5rem;
        }

        .domain-tools {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          justify-content: center;
        }
      }
    }
  }

  .workflow-steps {
    .workflow-step {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 2rem;
      align-items: center;
      margin-bottom: 4rem;

      &.reverse {
        grid-template-columns: auto 1fr auto;
        
        .step-content {
          order: 2;
          text-align: right;
        }
        
        .step-visual {
          order: 1;
        }
        
        .step-number {
          order: 3;
        }
      }

      .step-number {
        width: 4rem;
        height: 4rem;
        border-radius: 50%;
        background: var(--p-primary-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 600;
      }

      .step-content {
        .step-title {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 1rem;
        }

        .step-description {
          color: var(--text-color-secondary);
          line-height: 1.6;
        }
      }

      .step-visual {
        width: 300px;
        height: 200px;
        border-radius: 0.5rem;
        overflow: hidden;
        background: var(--p-surface-c);
      }
    }
  }

  .cta-section {
    padding: 4rem 2rem;
    max-width: 800px;
    margin: 0 auto;

    .cta-card {
      background: linear-gradient(135deg, var(--p-primary-color), var(--p-blue-600));
      color: white;
      text-align: center;

      .cta-content {
        padding: 2rem;

        .cta-title {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 1rem;
        }

        .cta-description {
          font-size: 1.125rem;
          opacity: 0.9;
          margin-bottom: 2rem;
        }

        .primary-cta {
          background: white;
          color: var(--p-primary-color);
          border: none;
          
          i {
            margin-left: 0.5rem;
          }
        }

        .cta-note {
          margin-top: 1rem;
          opacity: 0.8;
          font-size: 0.875rem;
        }
      }
    }
  }
}

.placeholder-image {
  position: relative;
  background: var(--p-surface-c);
  display: flex;
  align-items: center;
  justify-content: center;
  
  .placeholder-content {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    color: var(--text-color-secondary);
    text-align: center;
    padding: 2rem;
    width: 100%;
    height: 100%;

    .placeholder-icon {
      font-size: 3rem;
      margin-bottom: 1rem;
      color: var(--p-primary-color);
    }

    span {
      font-weight: 500;
      font-size: 1.125rem;
      margin-bottom: 0.5rem;
    }

    .placeholder-alt {
      font-size: 0.875rem;
      color: var(--text-color-secondary);
      margin: 0;
      opacity: 0.8;
    }
  }

  &:hover .placeholder-content {
    background: var(--p-surface-d);
    
    .placeholder-icon {
      color: var(--p-primary-600);
      transform: scale(1.1);
    }
  }
}

.splash-footer {
  background: var(--p-surface-b);
  border-top: 1px solid var(--p-surface-border);
  
  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 4rem 2rem 2rem;
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 2rem;

    .footer-section {
      .footer-brand {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;

        h3 {
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--p-primary-color);
          margin: 0;
        }
      }

      .footer-description {
        color: var(--text-color-secondary);
        line-height: 1.6;
      }

      .footer-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--p-text-color);
      }

      .footer-links {
        list-style: none;
        padding: 0;
        margin: 0;

        li {
          margin-bottom: 0.5rem;

          a {
            color: var(--text-color-secondary);
            text-decoration: none;
            transition: color 0.2s;

            &:hover {
              color: var(--p-primary-color);
            }
          }
        }
      }
    }
  }

  .footer-bottom {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    border-top: 1px solid var(--p-surface-border);
    text-align: center;
    color: var(--text-color-secondary);
  }
}

@media (max-width: 768px) {
  .splash-header .header-nav {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .hero-section {
    grid-template-columns: 1fr !important;
    text-align: center;
    gap: 2rem !important;

    .hero-content .hero-title {
      font-size: 2.5rem !important;
    }
  }

  .workflow-steps .workflow-step {
    grid-template-columns: 1fr !important;
    text-align: center;

    &.reverse .step-content {
      text-align: center !important;
    }

    .step-visual {
      width: 100% !important;
      max-width: 300px;
      margin: 0 auto;
    }
  }

  .splash-footer .footer-content {
    grid-template-columns: 1fr !important;
    gap: 2rem;
  }
}
</style>