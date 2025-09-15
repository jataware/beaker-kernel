<template>
  <div class="auth-container">
    <div class="auth-content">
      <div v-if="!loggedIn">
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
              <div class="login-icon">
                <i class="pi pi-sign-in"></i>
              </div>
              <h2 class="form-title">Welcome Back</h2>
              <p class="form-subtitle">Log in to access your BeakerHub workspaces</p>
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
                <label for="password" class="field-label">Password</label>
                <div class="input-wrapper password-wrapper">
                  <Password
                    id="password"
                    v-model="formData.password"
                    placeholder="Enter your password"
                    class="password-input"
                    :feedback="false"
                    toggleMask
                    required
                  />
                  <i class="pi pi-lock password-icon"></i>
                </div>
              </div>

              <div class="forgot-password">
                <a href="/auth/reset" class="forgot-link">Forgot your password?</a>
              </div>

              <Button
                type="submit"
                :disabled="!isFormValid || isSubmitting"
                :loading="isSubmitting"
                class="submit-button"
                size="large"
              >
                {{ isSubmitting ? 'Logging in...' : 'Log In' }}
              </Button>
            </form>

            <Divider />

            <div class="signup-link">
              <span class="signup-text">New to BeakerHub? </span>
              <a href="/auth/signup" class="signup-link-text">Sign Up</a>
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
            <h2 class="success-title">Welcome back!</h2>
            <p class="success-subtitle">You have successfully logged in to BeakerHub.</p>
          </div>

          <Message severity="success" class="success-message">
            <template #icon>
              <i class="pi pi-info-circle"></i>
            </template>
            <div>
              <h3 class="message-title">Getting Started</h3>
              <ul class="message-list">
                <li>Access your previous notebooks and sessions</li>
                <li>Create new computational environments</li>
                <li>Continue your research where you left off</li>
              </ul>
            </div>
          </Message>

          <Button @click="goToDashboard" class="continue-button" size="large">
            Go to Dashboard
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
import Button from 'primevue/button';
import Message from 'primevue/message';
import Divider from 'primevue/divider';
import BeakerLogo from '@/components/BeakerHubLogo.vue';

interface FormData {
  email: string;
  password: string;
}

const formData = ref<FormData>({
  email: '',
  password: ''
});

const isSubmitting = ref(false);
const loggedIn = ref(false);

const isFormValid = computed(() => {
  return formData.value.email && formData.value.password;
});

const handleSubmit = async () => {
  if (!isFormValid.value) return;

  isSubmitting.value = true;
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  console.log('Login data:', formData.value);
  loggedIn.value = true;
  isSubmitting.value = false;
};

const goToDashboard = () => {
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
  margin-top: max(1.5rem, 14vh);
}

.auth-header {
  margin-bottom: 1rem;
}

.auth-title {
  /* margin-bottom: 0.5rem; */

  font-size: 2.25rem;
  font-weight: bold;
  color: var(--p-text-color);
  /* margin-bottom: 0.5rem; */
  margin-top: 0;
  margin-bottom: 0;
}

.auth-subtitle {
  color: var(--p-text-muted-color);
  margin-top: 0.25rem;
  margin-bottom: 0;
  font-size: 1.125rem;
}

.auth-card {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.form-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.login-icon {
  margin: 0 auto 0.75rem;
  width: 3rem;
  height: 3rem;
  background-color: var(--p-purple-600);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-icon i {
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

.forgot-password {
  text-align: right;
  margin-top: -0.5rem;
}

.forgot-link {
  font-size: 0.875rem;
  color: var(--p-primary-color);
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.submit-button {
  width: 100%;
}

.signup-link {
  text-align: center;
}

.signup-text {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.signup-link-text {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
}

.signup-link-text:hover {
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

.continue-button {
  width: 100%;
}

@media (max-width: 640px) {
  .auth-title {
    font-size: 2rem;
  }
  
  .auth-container {
    padding: 0.75rem;
  }
}

@media (max-height: 600px) {
  .auth-content {
    margin-top: max(1rem, 6vh);
  }
}


.auth-header-logo {
  display: flex;
  align-items: flex-end;
  margin-bottom: 0;
 }

</style>