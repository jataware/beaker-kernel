<template>
  <div class="auth-container">
    <div class="auth-content">
      <div v-if="!submitted">
        <div class="auth-header">
          <div class="auth-header-logo">
            <BeakerLogo />
            <h1 class="auth-title">BeakerHub</h1>
          </div>
          <p class="auth-subtitle">AI-powered Interactive notebook environments</p>
        </div>

        <Card class="auth-card">
          <template #content>
            <div class="form-header">
              <div class="reset-icon">
                <i class="pi pi-key"></i>
              </div>
              <h2 class="form-title">Reset Password</h2>
              <p class="form-subtitle">Enter your email to receive a password reset link</p>
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

              <Button
                type="submit"
                :disabled="!isFormValid || isSubmitting"
                :loading="isSubmitting"
                class="submit-button"
                size="large"
              >
                {{ isSubmitting ? 'Sending...' : 'Send Reset Link' }}
              </Button>
            </form>

            <Divider />

            <div class="back-to-login">
              <span class="back-text">Remember your password? </span>
              <a href="/auth/login" class="back-link-text">Back to Login</a>
            </div>

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
            <i class="pi pi-envelope success-icon"></i>
            <h2 class="success-title">Check Your Email</h2>
            <p class="success-subtitle">We've sent a password reset link to {{ formData.email }}</p>
          </div>

          <Message severity="info" class="success-message">
            <template #messageicon>
              <i class="pi pi-info-circle"></i>
            </template>
            <div>
              <h3 class="message-title">What's Next?</h3>
              <ul class="message-list">
                <li>Check your email for the reset link</li>
                <li>Click the link to create a new password</li>
                <li>The link will expire in 24 hours</li>
              </ul>
            </div>
          </Message>

          <p class="resend-text">
            Didn't receive an email? 
            <button @click="resendEmail" class="resend-link" :disabled="resendCooldown > 0">
              {{ resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend' }}
            </button>
          </p>

          <Button @click="goToLogin" class="continue-button" size="large" severity="secondary">
            Back to Login
          </Button>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Message from 'primevue/message';
import Divider from 'primevue/divider';
import BeakerLogo from '@/components/BeakerLogo.vue';

interface FormData {
  email: string;
}

const formData = ref<FormData>({
  email: ''
});

const isSubmitting = ref(false);
const submitted = ref(false);
const resendCooldown = ref(0);
let resendInterval: number | null = null;

const isFormValid = computed(() => {
  return formData.value.email;
});

const handleSubmit = async () => {
  if (!isFormValid.value) return;

  isSubmitting.value = true;
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  console.log('Reset password data:', formData.value);
  submitted.value = true;
  isSubmitting.value = false;
};

const resendEmail = async () => {
  console.log('Resending reset email to:', formData.value.email);
  
  resendCooldown.value = 30;
  resendInterval = window.setInterval(() => {
    resendCooldown.value--;
    if (resendCooldown.value <= 0 && resendInterval) {
      clearInterval(resendInterval);
      resendInterval = null;
    }
  }, 1000);
};

const goToLogin = () => {
  window.location.href = '/auth/login';
};

onUnmounted(() => {
  if (resendInterval) {
    clearInterval(resendInterval);
  }
});
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
  margin-top: max(1.5rem, 15vh);
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
  font-size: 1.125rem;
  margin-bottom: 0;
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

.reset-icon {
  margin: 0 auto 0.75rem;
  width: 3rem;
  height: 3rem;
  background-color: var(--p-purple-600);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reset-icon i {
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

.submit-button {
  width: 100%;
}

.back-to-login, .signup-link {
  text-align: center;
}

.back-text, .signup-text {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.back-link-text, .signup-link-text {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
}

.back-link-text:hover, .signup-link-text:hover {
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
  color: var(--p-purple-600);
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

.resend-text {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  margin-bottom: 1rem;
}

.resend-link {
  color: var(--p-primary-color);
  background: none;
  border: none;
  text-decoration: underline;
  cursor: pointer;
  font-size: 0.875rem;
}

.resend-link:hover:not(:disabled) {
  color: var(--p-primary-600);
}

.resend-link:disabled {
  color: var(--p-text-muted-color);
  cursor: not-allowed;
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
</style>