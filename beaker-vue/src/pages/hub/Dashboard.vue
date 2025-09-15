<template>
  <div class="dashboard-page">
    <div class="dashboard-container">

      <header class="dashboard-header">
        <div class="header-content">
          <div class="logo-section">
            <BeakerLogo />
            <h1 class="brand-title">BeakerHub</h1>
          </div>
          <div class="header-actions">
            <Button 
              text 
              size="small" 
              @click="toggleDarkMode"
              :title="isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            >
              <i :class="isDarkMode ? 'pi pi-sun' : 'pi pi-moon'"></i>
            </Button>
            <Button text size="small" @click="navigateToSettings">Settings</Button>
            <div class="profile-menu">
              <Button 
                text 
                size="small" 
                @click="toggleProfileMenu"
                :title="'User Menu'"
              >
                <i class="pi pi-user"></i>
              </Button>
              <div v-if="showProfileMenu" class="profile-dropdown" @click.stop>
                <div class="profile-menu-item" @click="openProfile">
                  <i class="pi pi-user"></i>
                  <span>Profile</span>
                </div>
                <div class="profile-menu-item" @click="logout">
                  <i class="pi pi-sign-out"></i>
                  <span>Logout</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main class="dashboard-main">
        
        <section class="domain-selection">
          <h2 class="section-title">Create New Session</h2>
          <p class="section-subtitle">
            Choose a domain, then configure and launch a sandboxed environment
          </p>
          
          <div class="domain-cards">
            <Card class="domain-card data-science-card"
              @click.stop="showDomainDetails('data-science')"
              :class="{ expanded: expandedCard === 'data-science' }">
              <template #header>
                <div class="card-header">
                  <div class="domain-icon data-science">
                    <DataScienceIcon />
                  </div>
                  <div class="card-header-content">
                    <h3 class="domain-title">Data Science</h3>
                    <p class="domain-description">
                      Advanced statistical analysis, machine learning, and data visualization 
                      with comprehensive Python data science ecosystem.
                    </p>
                  </div>
                  <!-- <div class="card-actions">
                    <Button 
                      text 
                      size="small" 
                      @click.stop="showDomainDetails('data-science')"
                    >
                      <i class="pi pi-info-circle"></i>
                    </Button>
                    <Button 
                      size="small" 
                      @click.stop="openDomainSelection('data-science')"
                    >
                      Launch
                    </Button>
                  </div> -->
                </div>
              </template>
              <template #content>
                <div class="domain-summary">
                  <div class="summary-item">
                    <span class="summary-label">Languages:</span>
                    <div class="summary-tags">
                      <Tag value="Python" size="small" />
                      <Tag value="R" size="small" />
                      <Tag value="Julia" size="small" />
                    </div>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">Key Tools:</span>
                    <div class="summary-tags">
                      <Tag value="pandas" size="small" />
                      <Tag value="scikit-learn" size="small" />
                      <Tag value="matplotlib" size="small" />
                    </div>
                  </div>
                </div>
              </template>
            </Card>

            
            <Card class="domain-card biomedical-card"
              @click.stop="showDomainDetails('biomedical')"
              :class="{ expanded: expandedCard === 'biomedical' }">
              <template #header>
                <div class="card-header">
                  <div class="domain-icon biomedical">
                    <BiomedicalIcon />
                  </div>
                  <div class="card-header-content">
                    <h3 class="domain-title">Biomedical</h3>
                    <p class="domain-description">
                      Bioinformatics, genomics analysis, and biomedical research 
                      with specialized tools and databases for life sciences.
                    </p>
                  </div>
                  <!-- <div class="card-actions">
                    <Button 
                      text 
                      size="small" 
                      @click.stop="showDomainDetails('biomedical')"
                    >
                      <i class="pi pi-info-circle"></i>
                    </Button>
                    <Button 
                      size="small" 
                      @click.stop="openDomainSelection('biomedical')"
                    >
                      Launch
                    </Button>
                  </div> -->
                </div>
              </template>
              <template #content>
                <div class="domain-summary">
                  <div class="summary-item">
                    <span class="summary-label">Languages:</span>
                    <div class="summary-tags">
                      <Tag value="Python" size="small" />
                    </div>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">Key Tools:</span>
                    <div class="summary-tags">
                      <Tag value="BioPython" size="small" />
                      <Tag value="PyMOL" size="small" />
                      <Tag value="RDKit" size="small" />
                    </div>
                  </div>
                </div>
              </template>
            </Card>

            
            <Card class="domain-card weather-card" 
              @click.stop="showDomainDetails('weather')"
              :class="{ expanded: expandedCard === 'weather' }">
              <template #header>
                <div class="card-header">
                  <div class="domain-icon weather">
                    <WeatherIcon />
                  </div>
                  <div class="card-header-content">
                    <h3 class="domain-title">Weather</h3>
                    <p class="domain-description">
                      Meteorological analysis, climate data processing, and weather forecasting 
                      with specialized atmospheric science tools and APIs.
                    </p>
                  </div>
                  <!-- <div class="card-actions">
                    <Button 
                      text 
                      size="small" 
                      @click.stop="showDomainDetails('weather')"
                    >
                      <i class="pi pi-info-circle"></i>
                    </Button>
                    <Button 
                      size="small" 
                      @click.stop="openDomainSelection('weather')"
                    >
                      Launch
                    </Button>
                  </div> -->
                </div>
              </template>
              <template #content>
                <div class="domain-summary">
                  <div class="summary-item">
                    <span class="summary-label">Languages:</span>
                    <div class="summary-tags">
                      <Tag value="Python" size="small" />
                    </div>
                  </div>
                  <div class="summary-item">
                    <span class="summary-label">Key Tools:</span>
                    <div class="summary-tags">
                      <Tag value="xarray" size="small" />
                      <Tag value="cartopy" size="small" />
                      <Tag value="metpy" size="small" />
                    </div>
                  </div>
                </div>
              </template>
            </Card>
          </div>
        </section>

        
        <section class="resume-sessions">
          <h2 class="section-title">Resume Sessions</h2>
          <p class="section-subtitle">
            Continue working on your previous notebooks
          </p>

          <div class="sessions-list">
            
            <div class="session-row session-data-science">
              <div class="session-preview">
                <img src="/images/beaker-datascience-thumb.png" alt="Session thumbnail" />
              </div>
              <div class="session-info">
                <h3 class="session-title">Cancer genomics from PMC with visualization</h3>
                <p class="session-description">
                  Data analysis of cancer genomics from PMC with visualization modeling
                </p>
                <div class="session-meta">
                  <Tag severity="info" value="Data Science" size="small" />
                  <span class="session-date">2 hours ago</span>
                </div>
              </div>
              <div class="session-actions">
                <Button text size="small" severity="secondary" @click="openSession('session1')">
                  <i class="pi pi-external-link"></i>
                  Open
                </Button>
                <Button text size="small" severity="secondary" @click="cloneSession('session1')">
                  <i class="pi pi-copy"></i>
                  Clone
                </Button>
                <Button text size="small" severity="danger" @click="deleteSession('session1')">
                  <i class="pi pi-trash"></i>
                  Delete
                </Button>
              </div>
            </div>

            
            <div class="session-row session-weather">
              <div class="session-preview">
                <img src="/images/beaker-weather-thumb.png" alt="Session thumbnail" />
              </div>
              <div class="session-info">
                <h3 class="session-title">Air quality analysis with EPA AQS data with time series forecasting and geographic mapping</h3>
                <p class="session-description">
                  Air quality analysis with EPA AQS data with time series forecasting and geographic mapping
                </p>
                <div class="session-meta">
                  <Tag severity="success" value="Weather" size="small" />
                  <span class="session-date">1 day ago</span>
                </div>
              </div>
              <div class="session-actions">
                <Button text size="small" severity="secondary" @click="openSession('session2')">
                  <i class="pi pi-external-link"></i>
                  Open
                </Button>
                <Button text size="small" severity="secondary" @click="cloneSession('session2')">
                  <i class="pi pi-copy"></i>
                  Clone
                </Button>
                <Button text size="small" severity="danger" @click="deleteSession('session2')">
                  <i class="pi pi-trash"></i>
                  Delete
                </Button>
              </div>
            </div>

            
            <div class="session-row session-biomedical">
              <div class="session-preview">
                <img src="/images/beaker-biomedical-thumb.png" alt="Session thumbnail" />
              </div>
              <div class="session-info">
                <h3 class="session-title">Neutron survey data exploration with demographic correlation analysis and health indicators</h3>
                <p class="session-description">
                  Neutron survey data exploration with demographic correlation analysis and health indicators
                </p>
                <div class="session-meta">
                  <Tag severity="warning" value="Biomedical" size="small" />
                  <span class="session-date">3 days ago</span>
                </div>
              </div>
              <div class="session-actions">
                <Button text size="small" severity="secondary" @click="openSession('session3')">
                  <i class="pi pi-external-link"></i>
                  Open
                </Button>
                <Button text size="small" severity="secondary" @click="cloneSession('session3')">
                  <i class="pi pi-copy"></i>
                  Clone
                </Button>
                <Button text size="small" severity="danger" @click="deleteSession('session3')">
                  <i class="pi pi-trash"></i>
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <!-- Footer -->
      <footer class="dashboard-footer">
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
              <li><a href="/">Dashboard</a></li>
              <li><a href="/hub">About BeakerHub</a></li>
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

    
    <Dialog 
      v-model:visible="detailsDialogVisible" 
      modal 
      header="Domain Details"
      :style="{ width: '600px' }"
    >
      <div v-if="selectedDomainDetails" class="domain-details-dialog">
        <div class="dialog-header">
          <h3>{{ selectedDomainDetails.title }}</h3>
          <p>{{ selectedDomainDetails.description }}</p>
        </div>

        <div class="detail-sections">
          <div class="detail-section">
            <h4>Workflows</h4>
            <div class="tags">
              <Tag 
                v-for="workflow in selectedDomainDetails.workflows" 
                :key="workflow"
                :value="workflow" 
                size="small"
              />
            </div>
          </div>

          <div class="detail-section">
            <h4>Integrations</h4>
            <div class="tags">
              <Tag 
                v-for="integration in selectedDomainDetails.integrations" 
                :key="integration"
                :value="integration" 
                size="small"
              />
            </div>
          </div>

          <div class="detail-section">
            <h4>Tools</h4>
            <div class="tags">
              <Tag 
                v-for="tool in selectedDomainDetails.tools" 
                :key="tool"
                :value="tool" 
                size="small"
              />
            </div>
          </div>

          <div class="detail-section">
            <h4>Languages</h4>
            <div class="tags">
              <Tag 
                v-for="language in selectedDomainDetails.languages" 
                :key="language"
                :value="language" 
                size="small"
              />
            </div>
          </div>

          <div class="detail-section">
            <h4>Agent Info</h4>
            <p class="agent-description">{{ selectedDomainDetails.agentInfo }}</p>
          </div>
        </div>

        <div class="dialog-actions">
          <Button @click="detailsDialogVisible = false" text>Close</Button>
          <Button @click="openDomainSelection(selectedDomainDetails.title.toLowerCase().replace(' ', '-')); detailsDialogVisible = false">
            Launch Environment
          </Button>
        </div>
      </div>
    </Dialog>

    
    <Dialog 
      v-model:visible="selectionDialogVisible" 
      modal 
      :header="`Launch ${selectedDomain?.title} Environment`"
      :style="{ width: '500px' }"
    >
      <div v-if="selectedDomain" class="domain-selection-dialog">
        <div class="selection-header">
          <div class="domain-info">
            <div class="domain-icon-large" :class="selectedDomain.key">
              <DataScienceIcon v-if="selectedDomain.key === 'data-science'" />
              <BiomedicalIcon v-else-if="selectedDomain.key === 'biomedical'" />
              <WeatherIcon v-else-if="selectedDomain.key === 'weather'" />
            </div>
            <div>
              <h3>{{ selectedDomain.title }}</h3>
              <p>{{ selectedDomain.description }}</p>
            </div>
          </div>
        </div>

        <div class="selection-options">
          <div class="option-section">
            <h4>Environment Name</h4>
            <input 
              type="text" 
              v-model="environmentName" 
              :placeholder="`My ${selectedDomain.title} Project`"
              class="environment-name-input"
            >
          </div>

          <div class="option-section">
            <h4>Template</h4>
            <div class="template-options">
              <div 
                class="template-option" 
                :class="{ active: selectedTemplate === 'blank' }"
                @click="selectedTemplate = 'blank'"
              >
                <i class="pi pi-file"></i>
                <span>Blank Notebook</span>
              </div>
              <div 
                class="template-option" 
                :class="{ active: selectedTemplate === 'sample' }"
                @click="selectedTemplate = 'sample'"
              >
                <i class="pi pi-code"></i>
                <span>Sample Project</span>
              </div>
            </div>
          </div>

          <div class="option-section">
            <h4>Quick Start</h4>
            <div class="quick-start-options">
              <label class="checkbox-option">
                <input type="checkbox" v-model="includeDataSample">
                <span>Include sample dataset</span>
              </label>
              <label class="checkbox-option">
                <input type="checkbox" v-model="enableGitIntegration">
                <span>Enable Git integration</span>
              </label>
            </div>
          </div>
        </div>

        <div class="dialog-actions">
          <Button @click="selectionDialogVisible = false" text>Cancel</Button>
          <Button @click="createEnvironment" :loading="isCreatingEnvironment">
            <i class="pi pi-play"></i>
            Create Environment
          </Button>
        </div>
      </div>
    </Dialog>

    
    <Dialog 
      v-model:visible="creationDialogVisible" 
      modal 
      header="Creating Your Environment"
      :style="{ width: '400px' }"
      :closable="false"
    >
      <div class="creation-dialog">
        <div class="creation-animation">
          <div class="loading-spinner">
            <i class="pi pi-spin pi-spinner"></i>
          </div>
          <div class="creation-steps">
            <div class="step" :class="{ active: creationStep >= 1, completed: creationStep > 1 }">
              <i class="pi pi-check-circle"></i>
              <span>Setting up sandbox environment</span>
            </div>
            <div class="step" :class="{ active: creationStep >= 2, completed: creationStep > 2 }">
              <i class="pi pi-check-circle"></i>
              <span>Installing domain-specific tools</span>
            </div>
            <div class="step" :class="{ active: creationStep >= 3, completed: creationStep > 3 }">
              <i class="pi pi-check-circle"></i>
              <span>Configuring AI agent</span>
            </div>
            <div class="step" :class="{ active: creationStep >= 4, completed: creationStep > 4 }">
              <i class="pi pi-check-circle"></i>
              <span>Launching notebook interface</span>
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Tag from 'primevue/tag';
import Dialog from 'primevue/dialog';
import BeakerLogo from '../../components/BeakerHubLogo.vue';
import DataScienceIcon from '../../components/icons/DataScienceIcon.vue';
import BiomedicalIcon from '../../components/icons/BiomedicalIcon.vue';
import WeatherIcon from '../../components/icons/WeatherIcon.vue';

const router = useRouter();
const expandedCard = ref<string | null>(null);
const detailsDialogVisible = ref(false);
const selectedDomainDetails = ref<any>(null);

const selectionDialogVisible = ref(false);
const selectedDomain = ref<any>(null);
const environmentName = ref('');
const selectedTemplate = ref('blank');
const includeDataSample = ref(true);
const enableGitIntegration = ref(false);

const creationDialogVisible = ref(false);
const isCreatingEnvironment = ref(false);
const creationStep = ref(0);

const isDarkMode = ref(false);
const showProfileMenu = ref(false);

const domainDetails = {
  'data-science': {
    title: 'Data Science',
    key: 'data-science',
    icon: 'pi pi-chart-bar',
    description: 'Advanced statistical analysis, machine learning, and data visualization with comprehensive Python data science ecosystem.',
    workflows: ['Data Analysis', 'ML Modeling', 'Visualization', 'Statistical Testing'],
    integrations: ['Kaggle', 'Google Colab', 'Hugging Face', 'GitHub'],
    tools: ['pandas', 'scikit-learn', 'matplotlib', 'seaborn', 'numpy', 'scipy'],
    languages: ['Python', 'R', 'Julia'],
    agentInfo: 'Trained on data science methodologies, statistical analysis, and machine learning best practices with access to comprehensive documentation.'
  },
  'biomedical': {
    title: 'Biomedical',
    key: 'biomedical',
    icon: 'pi pi-heart',
    description: 'Bioinformatics, genomics analysis, and biomedical research with specialized tools and databases for life sciences.',
    workflows: ['Genomics', 'Proteomics', 'Drug Discovery', 'Pathway Analysis'],
    integrations: ['NCBI', 'UniProt', 'PDB', 'Ensembl'],
    tools: ['BioPython', 'PyMOL', 'Biopandas', 'RDKit', 'MDAnalysis'],
    languages: ['Python'],
    agentInfo: 'Specialized in bioinformatics workflows, molecular biology, and biomedical data analysis with access to life sciences databases.'
  },
  'weather': {
    title: 'Weather',
    key: 'weather',
    icon: 'pi pi-cloud',
    description: 'Meteorological analysis, climate data processing, and weather forecasting with specialized atmospheric science tools and APIs.',
    workflows: ['Climate Analysis', 'Forecasting', 'Pattern Recognition', 'Atmospheric Modeling'],
    integrations: ['NOAA', 'OpenWeatherMap', 'NASA', 'ECMWF'],
    tools: ['xarray', 'cartopy', 'metpy', 'netCDF4', 'iris'],
    languages: ['Python'],
    agentInfo: 'Expert in meteorological analysis, climate modeling, and atmospheric data processing with weather API integrations.'
  }
};

function openDomainSelection(domain: string) {
  selectedDomain.value = domainDetails[domain as keyof typeof domainDetails];
  environmentName.value = `My ${selectedDomain.value.title} Project`;
  selectionDialogVisible.value = true;
}

function showDomainDetails(domain: string) {
  selectedDomainDetails.value = domainDetails[domain as keyof typeof domainDetails];
  detailsDialogVisible.value = true;
}

async function createEnvironment() {
  isCreatingEnvironment.value = true;
  selectionDialogVisible.value = false;
  creationDialogVisible.value = true;
  creationStep.value = 0;

  
  const steps = [
    { delay: 1000, message: 'Setting up sandbox environment' },
    { delay: 2000, message: 'Installing domain-specific tools' },
    { delay: 1500, message: 'Configuring AI agent' },
    { delay: 1000, message: 'Launching notebook interface' }
  ];

  for (let i = 0; i < steps.length; i++) {
    await new Promise(resolve => setTimeout(resolve, steps[i].delay));
    creationStep.value = i + 1;
  }

  await new Promise(resolve => setTimeout(resolve, 1000));
  creationDialogVisible.value = false;
  isCreatingEnvironment.value = false;
  
  router.push(`/?domain=${selectedDomain.value.key}&name=${encodeURIComponent(environmentName.value)}&template=${selectedTemplate.value}`);
}

function openSession(sessionId: string) {
  router.push(`/?session=${sessionId}`);
}

function cloneSession(sessionId: string) {
  // TODO implement me
  console.log('Cloning session:', sessionId);
}

function deleteSession(sessionId: string) {
  // TODO: implement session deletion with confirmation
  console.log('Deleting session:', sessionId);
}

function navigateToSettings() {
  router.push('/admin');
}

function toggleProfileMenu() {
  showProfileMenu.value = !showProfileMenu.value;
}

function openProfile() {
  showProfileMenu.value = false;
  // TODO implement profile dialog or page
  console.log('Opening profile');
}

function logout() {
  showProfileMenu.value = false;
  // TODO implement logout functionality
  console.log('Logging out');
}

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  const htmlElement = document.documentElement;
  
  if (isDarkMode.value) {
    htmlElement.classList.add('beaker-dark');
  } else {
    htmlElement.classList.remove('beaker-dark');
  }
  
  localStorage.setItem('darkMode', isDarkMode.value.toString());
}

const handleClickOutside = (event: MouseEvent) => {
  const profileMenu = document.querySelector('.profile-menu');
  if (profileMenu && !profileMenu.contains(event.target as Node)) {
    showProfileMenu.value = false;
  }
};

onMounted(() => {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode !== null) {
    isDarkMode.value = savedDarkMode === 'true';
  } else {
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  
  if (isDarkMode.value) {
    document.documentElement.classList.add('beaker-dark');
  }
  
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: linear-gradient(135deg, 
    var(--p-surface-a) 0%, 
    rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.03) 25%,
    rgba(var(--p-blue-500-rgb, 59, 130, 246), 0.02) 50%,
    rgba(var(--p-purple-500-rgb, 168, 85, 247), 0.03) 75%,
    var(--p-surface-a) 100%
  );
  color: var(--p-text-color);
  position: relative;
  
  :global(.beaker-dark) & {
    background: linear-gradient(135deg, 
      var(--p-surface-a) 0%, 
      rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.08) 25%,
      rgba(var(--p-blue-500-rgb, 59, 130, 246), 0.06) 50%,
      rgba(var(--p-purple-500-rgb, 168, 85, 247), 0.08) 75%,
      var(--p-surface-a) 100%
    );
  }
  
  &::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(
      circle at 20% 20%, 
      rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.05) 0%, 
      transparent 50%
    ),
    radial-gradient(
      circle at 80% 80%, 
      rgba(var(--p-blue-500-rgb, 59, 130, 246), 0.04) 0%, 
      transparent 50%
    ),
    radial-gradient(
      circle at 40% 60%, 
      rgba(var(--p-purple-500-rgb, 168, 85, 247), 0.03) 0%, 
      transparent 50%
    );
    pointer-events: none;
    z-index: 0;
  }
  
  > * {
    position: relative;
    z-index: 1;
  }
  
  // defensive styles to prevent external interference
  * {
    box-sizing: border-box;
  }
  button, input, select, textarea {
    font-family: inherit;
    font-size: inherit;
  }
}

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
}

.dashboard-header {
  padding: 2rem 0;
  background: transparent;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.1);
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .logo-section {
      display: flex;
      align-items: center;
      gap: 1rem;
      
      .brand-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--p-primary-color), var(--p-blue-500));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
      }
    }
    
    .header-actions {
      display: flex;
      gap: 1rem;
      align-items: center;
      
      button {
        backdrop-filter: blur(8px);
        border: 1px solid rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.2);
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.1);
          border-color: var(--p-primary-color);
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.3);
        }
      }
      
      .profile-menu {
        position: relative;
        
        .profile-dropdown {
          position: absolute;
          top: calc(100% + 8px);
          right: 0;
          background: var(--p-surface-card);
          border: 1px solid var(--p-surface-border);
          border-radius: 8px;
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
          backdrop-filter: blur(10px);
          min-width: 160px;
          z-index: 1000;
          overflow: hidden;
          
          .profile-menu-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            color: var(--p-text-color);
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.875rem;
            
            &:hover {
              background: rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.1);
              color: var(--p-primary-color);
            }
            
            &:not(:last-child) {
              border-bottom: 1px solid var(--p-surface-border);
            }
            
            i {
              font-size: 1rem;
              opacity: 0.7;
            }
            
            span {
              font-weight: 500;
            }
          }
        }
      }
    }
  }
}

.dashboard-main {
  padding: 3rem 0;
}

.section-title {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, var(--p-text-color) 0%, rgba(var(--p-primary-color-rgb, 99, 102, 241), 0.8) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.section-subtitle {
  font-size: 1.125rem;
  color: var(--text-color-secondary);
  margin-bottom: 3rem;
  opacity: 0.8;
}

.domain-selection {
  margin-bottom: 6rem;
  
  .domain-cards {
    cursor: pointer;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
    
    .domain-card {
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      background: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      overflow: hidden;
      position: relative;
      
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.1) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 0;
      }
      
      &:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        
        &::before {
          opacity: 1;
        }
      }
      
      &.data-science-card {
        .card-header {
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }
        
        &:hover .card-header {
          background: linear-gradient(135deg, 
            #1e293b 0%, 
            #334155 25%, 
            #475569 50%, 
            #64748b 75%, 
            #94a3b8 100%
          );
          background-size: 200% 200%;
          animation: shimmer 2s ease-in-out 1;
          animation-fill-mode: forwards;
          color: white;
          
          .domain-title, .domain-description {
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          
          .domain-icon {
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
            color: #1e293b;
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
          }
          
          .card-actions button:not(.p-button-text) {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            color: #1e293b;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
          }
        }
      }
      
      &.biomedical-card {
        .card-header {
          background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        }
        
        &:hover .card-header {
          background: linear-gradient(135deg, 
            #14532d 0%, 
            #166534 25%, 
            #15803d 50%, 
            #16a34a 75%, 
            #22c55e 100%
          );
          background-size: 200% 200%;
          animation: shimmer 2s ease-in-out 1;
          animation-fill-mode: forwards;
          color: white;
          
          .domain-title, .domain-description {
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          
          .domain-icon {
            background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
            color: #14532d;
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
          }
          
          .card-actions button:not(.p-button-text) {
            background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
            color: #14532d;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
          }
        }
      }
      
      &.weather-card {
        .card-header {
          background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
        }
        
        &:hover .card-header {
          background: linear-gradient(135deg, 
            #3730a3 0%, 
            #4338ca 25%, 
            #4f46e5 50%, 
            #6366f1 75%, 
            #8b5cf6 100%
          );
          background-size: 200% 200%;
          animation: shimmer 2s ease-in-out 1;
          animation-fill-mode: forwards;
          color: white;
          
          .domain-title, .domain-description {
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          
          .domain-icon {
            background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
            color: #3730a3;
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.3);
          }
          
          .card-actions button:not(.p-button-text) {
            background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
            color: #3730a3;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
          }
        }
      }
      
      .card-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.25rem;
        transition: all 0.4s ease;
        position: relative;
        z-index: 1;
        
        .domain-icon {
          width: 3rem;
          height: 3rem;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          flex-shrink: 0;
          
          &.data-science {
            background: linear-gradient(135deg, #1e293b, #475569);
            color: #e2e8f0;
          }
          
          &.biomedical {
            background: linear-gradient(135deg, #14532d, #16a34a);
            color: #dcfce7;
          }
          
          &.weather {
            background: linear-gradient(135deg, #3730a3, #6366f1);
            color: #e0e7ff;
          }
        }
        
        .card-header-content {
          flex: 1;
          
          .domain-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            color: var(--p-text-color);
          }
          
          .domain-description {
            color: var(--text-color-secondary);
            font-size: 0.875rem;
            line-height: 1.4;
            margin: 0;
          }
        }
        
        .card-actions {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }
      }
      
      .domain-summary {
        .summary-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1rem;
          
          .summary-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--p-text-color);
            min-width: 80px;
          }
          
          .summary-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
          }
        }
      }
    }
  }
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
}

.resume-sessions {
  .sessions-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    
    .session-row {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      padding: 1.5rem;
      border-radius: 12px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      backdrop-filter: blur(10px);
      
      &.session-data-science {
        background: linear-gradient(135deg, 
          #1e293b 0%, 
          #334155 25%, 
          #475569 50%, 
          #64748b 75%, 
          #94a3b8 100%
        );
        border: 2px solid #1e293b;
        color: white;
        
        .session-title {
          color: white;
          font-weight: 700;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .session-description, .session-date {
          color: rgba(255, 255, 255, 0.9);
        }
        
        .session-actions button {
          color: white;
          border-color: rgba(255, 255, 255, 0.3);
          
          &:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: white;
            color: white;
          }
          
          &.p-button-danger:hover {
            background: rgba(239, 68, 68, 0.8);
            border-color: #ef4444;
            color: white;
          }
        }
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 40px rgba(30, 41, 59, 0.4);
        }
      }
      
      &.session-biomedical {
        background: linear-gradient(135deg, 
          #14532d 0%, 
          #166534 25%, 
          #15803d 50%, 
          #16a34a 75%, 
          #22c55e 100%
        );
        border: 2px solid #14532d;
        color: white;
        
        .session-title {
          color: white;
          font-weight: 700;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .session-description, .session-date {
          color: rgba(255, 255, 255, 0.9);
        }
        
        .session-actions button {
          color: white;
          border-color: rgba(255, 255, 255, 0.3);
          
          &:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: white;
            color: white;
          }
          
          &.p-button-danger:hover {
            background: rgba(239, 68, 68, 0.8);
            border-color: #ef4444;
            color: white;
          }
        }
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 40px rgba(20, 83, 45, 0.4);
        }
      }
      
      &.session-weather {
        background: linear-gradient(135deg, 
          #3730a3 0%, 
          #4338ca 25%, 
          #4f46e5 50%, 
          #6366f1 75%, 
          #8b5cf6 100%
        );
        border: 2px solid #3730a3;
        color: white;
        
        .session-title {
          color: white;
          font-weight: 700;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .session-description, .session-date {
          color: rgba(255, 255, 255, 0.9);
        }
        
        .session-actions button {
          color: white;
          border-color: rgba(255, 255, 255, 0.3);
          
          &:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: white;
            color: white;
          }
          
          &.p-button-danger:hover {
            background: rgba(239, 68, 68, 0.8);
            border-color: #ef4444;
            color: white;
          }
        }
        
        &:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 40px rgba(55, 48, 163, 0.4);
        }
      }
      
      .session-preview {
        width: 15rem;
        height: 10rem;
        background: rgba(255, 255, 255, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
        overflow: hidden;
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 6px;
        }
        
        .preview-placeholder {
          text-align: center;
          
          i {
            font-size: 1.5rem;
            color: rgba(255, 255, 255, 0.9);
            transition: transform 0.3s ease;
          }
        }
      }
      
      &:hover .session-preview {
        transform: scale(1.05);
        background: rgba(255, 255, 255, 0.3);
        border-color: rgba(255, 255, 255, 0.6);
        
        .preview-placeholder i {
          transform: scale(1.1);
          color: white;
        }
      }
      
      .session-info {
        flex: 1;
        min-width: 0;
        
        .session-title {
          font-size: 1rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          line-height: 1.4;
        }

        :global(.beaker-dark) & {
          .session-title {
            color: var(--p-text-color);
          }
          .session-description {
            color: var(--p-text-color);
          }
        }
        
        .session-description {
          font-size: 0.875rem;
          line-height: 1.4;
          margin-bottom: 0.75rem;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }
        
        .session-meta {
          display: flex;
          align-items: center;
          gap: 1rem;
          
          .session-date {
            font-size: 0.75rem;
            color: var(--text-color-secondary);
          }
        }
      }
      
      .session-actions {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        flex-shrink: 0;
        
        button {
          transition: all 0.2s ease;
          
          &:hover {
            background: var(--p-surface-c);
            transform: translateY(-1px);
          }
          
          &.p-button-secondary:hover {
            background: var(--p-surface-d);
            border-color: var(--p-primary-color);
            color: var(--p-primary-color);
          }
          
          &.p-button-danger:hover {
            background: rgba(239, 68, 68, 0.1);
            border-color: #ef4444;
            color: #ef4444;
          }
        }
      }
    }
  }
}

.domain-selection-dialog {
  .selection-header {
    margin-bottom: 2rem;
    
    .domain-info {
      display: flex;
      align-items: center;
      gap: 1rem;
      
      .domain-icon-large {
        width: 4rem;
        height: 4rem;
        min-width: 4rem;
        min-height: 4rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: white;
        flex-shrink: 0;
        
        &.data-science {
          background: linear-gradient(135deg, #1e293b, #475569);
          color: #e2e8f0;
        }
        
        &.biomedical {
          background: linear-gradient(135deg, #14532d, #16a34a);
          color: #dcfce7;
        }
        
        &.weather {
          background: linear-gradient(135deg, #3730a3, #6366f1);
          color: #e0e7ff;
        }
      }
      
      h3 {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--p-text-color);
      }
      
      p {
        color: var(--text-color-secondary);
        margin: 0;
      }
    }
  }
  
  .selection-options {
    .option-section {
      margin-bottom: 2rem;
      
      h4 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--p-text-color);
        margin-bottom: 1rem;
      }
      
      .environment-name-input {
        width: 100%;
        padding: 0.75rem;
        border: 1px solid var(--p-surface-border);
        border-radius: 0.375rem;
        background: var(--p-surface-a);
        color: var(--p-text-color);
        font-size: 1rem;
        
        &:focus {
          outline: none;
          border-color: var(--p-primary-color);
          box-shadow: 0 0 0 2px rgba(var(--p-primary-color), 0.2);
        }
      }
      
      .template-options {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        
        .template-option {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          border: 1px solid var(--p-surface-border);
          border-radius: 0.375rem;
          background: var(--p-surface-b);
          cursor: pointer;
          transition: all 0.2s ease;
          
          &:hover {
            background: var(--p-surface-c);
          }
          
          &.active {
            border-color: var(--p-primary-color);
            background: rgba(var(--p-primary-color), 0.1);
          }
          
          i {
            font-size: 1.25rem;
            color: var(--p-primary-color);
          }
          
          span {
            font-weight: 500;
            color: var(--p-text-color);
          }
        }
      }
      
      .quick-start-options {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        
        .checkbox-option {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          cursor: pointer;
          
          input[type="checkbox"] {
            width: 1.25rem;
            height: 1.25rem;
            accent-color: var(--p-primary-color);
          }
          
          span {
            color: var(--p-text-color);
          }
        }
      }
    }
  }
  
  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid var(--p-surface-border);
  }
}

.creation-dialog {
  text-align: center;
  
  .creation-animation {
    .loading-spinner {
      margin-bottom: 2rem;
      
      i {
        font-size: 3rem;
        color: var(--p-primary-color);
      }
    }
    
    .creation-steps {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      text-align: left;
      
      .step {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border-radius: 0.375rem;
        background: var(--p-surface-b);
        opacity: 0.5;
        transition: all 0.3s ease;
        
        &.active {
          opacity: 1;
          background: rgba(var(--p-primary-color), 0.1);
          border: 1px solid var(--p-primary-color);
        }
        
        &.completed {
          opacity: 1;
          background: rgba(34, 197, 94, 0.1);
          border: 1px solid #22c55e;
          
          i {
            color: #22c55e;
          }
        }
        
        i {
          font-size: 1.25rem;
          color: var(--p-primary-color);
        }
        
        span {
          font-weight: 500;
          color: var(--p-text-color);
        }
      }
    }
  }
}

.domain-details-dialog {
  .dialog-header {
    margin-bottom: 2rem;
    
    h3 {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 1rem;
      color: var(--p-text-color);
    }
    
    p {
      color: var(--text-color-secondary);
      line-height: 1.6;
    }
  }
  
  .detail-sections {
    .detail-section {
      margin-bottom: 2rem;
      
      h4 {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--p-text-color);
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      
      .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      
      .agent-description {
        color: var(--text-color-secondary);
        line-height: 1.6;
      }
    }
  }
  
  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid var(--p-surface-border);
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 0 1rem;
  }
  
  .dashboard-header .header-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .domain-selection .domain-cards {
    grid-template-columns: 1fr;
  }
  
  .resume-sessions .sessions-list .session-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    
    .session-preview {
      width: 100%;
      height: 120px;
    }
    
    .session-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
}

.dashboard-footer {
  // background: var(--p-surface-b);
  // border-top: 1px solid var(--p-surface-border);
  
  .footer-content {
    max-width: 1400px;
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
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    border-top: 1px solid var(--p-surface-border);
    text-align: center;
    color: var(--text-color-secondary);
  }
}

@media (max-width: 768px) {
  .dashboard-footer .footer-content {
    grid-template-columns: 1fr !important;
    gap: 2rem;
  }
}
</style>