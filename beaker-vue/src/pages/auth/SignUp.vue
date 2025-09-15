<template>
  <div class="auth-container">
    <div class="auth-content">
      <div v-if="!submitted">

        <div class="auth-header">
          <div class="auth-header-logo">
            <BeakerLogo />
            <h1 class="auth-title">BeakerHub</h1>
          </div>
          <p class="auth-subtitle">AI-Powered Interactive Notebook Environments</p>
        </div>

        <Card class="auth-card">
          <template #content>
            <div class="form-header">
              <div class="signup-icon">
                <i class="pi pi-user-plus"></i>
              </div>
              <h2 class="form-title">Sign Up</h2>
              <p class="form-subtitle">Join to get access to BeakerHub</p>
            </div>

            <form @submit.prevent="handleSubmit" class="form-content">

              <div class="form-field">
                <label for="email" class="field-label">Email Address</label>
                <div class="input-wrapper">
                  <InputText
                    id="email"
                    v-model="formData.email"
                    type="email"
                    placeholder="your.email@example.com"
                    class="input-with-icon"
                    required
                  />
                  <i class="pi pi-envelope input-icon"></i>
                </div>
              </div>

              <div class="form-field">
                <label for="useCase" class="field-label">Primary Use Case</label>
                <Select
                  id="useCase"
                  v-model="formData.useCase"
                  :options="useCases"
                  option-label="label"
                  option-value="value"
                  placeholder="Select your primary use case..."
                  class="w-full"
                  required
                />
                <small class="field-help">Help us understand how you plan to use BeakerHub</small>
              </div>

              <div class="form-field">
                <label for="password" class="field-label">Password</label>
                <div class="input-wrapper password-wrapper">
                  <Password
                    id="password"
                    v-model="formData.password"
                    placeholder="Create a password"
                    class="password-input"
                    :feedback="false"
                    toggleMask
                    required
                  />
                  <i class="pi pi-lock password-icon"></i>
                </div>
              </div>

              <div class="form-field">
                <label for="confirmPassword" class="field-label">Confirm Password</label>
                <div class="input-wrapper password-wrapper">
                  <Password
                    id="confirmPassword"
                    v-model="formData.confirmPassword"
                    placeholder="Confirm your password"
                    class="password-input"
                    :feedback="false"
                    toggleMask
                    required
                  />
                  <i class="pi pi-lock password-icon"></i>
                </div>
                <small v-if="passwordMismatch" class="field-error">Passwords do not match</small>
              </div>

              <Button
                type="submit"
                :disabled="!isFormValid || isSubmitting"
                :loading="isSubmitting"
                class="submit-button"
                size="large"
              >
                {{ isSubmitting ? 'Submitting...' : 'Sign Up' }}
              </Button>
            </form>

            <Divider />

            <div class="signin-link">
              <span class="signin-text">Already have access? </span>
              <a href="/auth/login" class="signin-link-text">Log In</a>
            </div>

            <div class="invite-link">
              <span class="invite-text">Have an invitation? </span>
              <a href="/auth/invite" class="invite-link-text">Join by Invite</a>
            </div>

            <div class="hub-link">
              <a href="/hub" class="hub-link-text">← Back to Site</a>
            </div>
          </template>
        </Card>
      </div>

      <Card v-else class="auth-card success-card">
        <template #content>
          <div class="success-header">
            <i class="pi pi-check-circle success-icon"></i>
            <h2 class="success-title">Welcome to BeakerHub!</h2>
            <p class="success-subtitle">Thank you for signing up for our beta program.</p>
          </div>

          <Message severity="info" class="success-message">
            <template #icon>
              <i class="pi pi-info-circle"></i>
            </template>
            <div>
              <h3 class="message-title">What's Next?</h3>
              <ul class="message-list">
                <li>We'll review your application within 24-48 hours</li>
                <li>You'll receive an email with access instructions</li>
              </ul>
            </div>
          </Message>

          <p class="contact-text">
            Questions? Email us at 
            <a href="mailto:support@beakerhub.com" class="contact-link">support@beakerhub.com</a>
          </p>

          <Button @click="goHome" class="continue-button" size="large">
            Continue to BeakerHub
          </Button>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Select from 'primevue/select';
import Button from 'primevue/button';
import Message from 'primevue/message';
import Divider from 'primevue/divider';
import BeakerLogo from '@/components/BeakerHubLogo.vue';

interface FormData {
  email: string;
  useCase: string;
  password: string;
  confirmPassword: string;
}

const formData = ref<FormData>({
  email: '',
  useCase: '',
  password: '',
  confirmPassword: ''
});

const isSubmitting = ref(false);
const submitted = ref(false);

const useCases = [
  { value: 'health-research', label: 'Health & Medical Research' },
  { value: 'environmental-analysis', label: 'Environmental Data Analysis' },
  { value: 'biomedical-discovery', label: 'Biomedical Discovery & Genomics' },
  { value: 'epidemiological-studies', label: 'Epidemiological Studies' },
  { value: 'public-health-policy', label: 'Public Health Policy Research' },
  { value: 'clinical-research', label: 'Clinical Research & Trials' },
  { value: 'pharmaceutical-research', label: 'Pharmaceutical Research' },
  { value: 'academic-teaching', label: 'Academic Teaching & Education' },
  { value: 'other', label: 'Other (please specify in beta feedback)' }
];

const passwordMismatch = computed(() => {
  return formData.value.password && 
         formData.value.confirmPassword && 
         formData.value.password !== formData.value.confirmPassword;
});

const isFormValid = computed(() => {
  return formData.value.email && 
         formData.value.useCase &&
         formData.value.password &&
         formData.value.confirmPassword &&
         !passwordMismatch.value;
});

const handleSubmit = async () => {
  if (!isFormValid.value) return;

  isSubmitting.value = true;
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  console.log('Signup data:', formData.value);
  submitted.value = true;
  isSubmitting.value = false;
};

const goHome = () => {
  window.location.href = '/';
};
</script>

<style scoped>

.auth-container {
  min-height: 100vh;
  background: linear-gradient(to bottom right, 
    color-mix(in srgb, var(--p-primary-50) 20%, white),
    white,
    color-mix(in srgb, var(--p-primary-100) 30%, white)
  );
  display: flex;
  justify-content: center;
  padding: 1rem;
  align-items: start;
}

.auth-content {
  width: 100%;
  max-width: 28rem;
  margin-top: max(1.5rem, 11vh);
}

.auth-header {
  margin-bottom: 1rem;
}

.auth-title {
  font-size: 2.25rem;
  font-weight: bold;
  color: var(--p-text-color);
  margin-top: 0;
  margin-bottom: 0;
}

.auth-subtitle {
  color: var(--p-text-muted-color);
  margin-top: 0.25rem;
  margin-bottom: 0;
  font-size: 1.125rem;
}

.auth-header-logo {
  display: flex;
  align-items: flex-end;
  margin-bottom: 0;
}

.auth-card {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.form-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.signup-icon {
  margin: 0 auto 0.75rem;
  width: 3rem;
  height: 3rem;
  background-color: var(--p-purple-600);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.signup-icon i {
  font-size: 1.5rem;
  color: var(--p-surface-0);
}

.form-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: var(--p-text-color);
}

.form-subtitle {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--p-text-color);
}

.field-help {
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.terms-agreement {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.terms-label {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--p-text-muted-color);
}

.terms-link {
  color: var(--p-primary-color);
  text-decoration: none;
}

.terms-link:hover {
  text-decoration: underline;
}

.submit-button {
  width: 100%;
}

.signin-link {
  text-align: center;
}

.signin-text {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.signin-link-text {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
}

.signin-link-text:hover {
  text-decoration: underline;
}

.invite-link {
  text-align: center;
}

.invite-text {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.invite-link-text {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
}

.invite-link-text:hover {
  text-decoration: underline;
}

.hub-link {
  text-align: center;
  margin-top: 1rem;
}

.hub-link-text {
  color: var(--p-text-muted-color);
  text-decoration: none;
  font-size: 0.875rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.hub-link-text:hover {
  color: var(--p-primary-color);
}

.success-card {
  text-align: center;
}

@media (max-height: 700px) {
  .auth-content {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .auth-header {
    margin-bottom: 1.5rem;
  }
}

@media (max-height: 600px) {
  .auth-content {
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
  }
  
  .auth-header {
    margin-bottom: 1rem;
  }
  
  .form-header {
    margin-bottom: 1rem;
  }
}

@media (max-width: 640px) {
  .auth-title {
    font-size: 2rem;
  }
  
  .auth-container {
    padding: 0.75rem;
  }
}

@media (max-height: 1100px) and (min-height: 800px) {
  .auth-content {
    margin-top: max(1.5rem, 5vh);
  }
}

@media (max-height: 600px) {
  .auth-content {
    margin-top: max(1rem, 5vh);
  }
}

.input-wrapper {
  position: relative;
  width: 100%;
}

.input-with-icon {
  width: 100%;
  padding-left: 2.5rem;
}

.input-icon {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--p-text-muted-color);
  opacity: 0.6;
  pointer-events: none;
  z-index: 1;
}

.password-wrapper {
  position: relative;
  width: 100%;
}

.password-input {
  width: 100%;
}

.password-input :deep(.p-password-input) {
  width: 100%;
  padding-left: 2.5rem;
}

.password-icon {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--p-text-muted-color);
  opacity: 0.6;
  pointer-events: none;
  z-index: 2;
}

.field-error {
  color: var(--p-red-500);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.success-header {
  margin-bottom: 1.5rem;
}

.success-icon {
  font-size: 4rem;
  color: var(--p-green-400);
  margin-bottom: 1rem;
  display: block;
}

.success-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: var(--p-text-color);
}

.success-subtitle {
  color: var(--p-text-muted-color);
}

.success-message {
  text-align: left;
  margin-bottom: 1.5rem;
}

.message-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.message-list {
  font-size: 0.875rem;
  list-style-type: disc;
  list-style-position: inside;
}

.message-list li {
  margin-bottom: 0.25rem;
}

.contact-text {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  margin-bottom: 1rem;
}

.contact-link {
  color: var(--p-primary-color);
  text-decoration: none;
}

.contact-link:hover {
  text-decoration: underline;
}

.continue-button {
  width: 100%;
}

</style>