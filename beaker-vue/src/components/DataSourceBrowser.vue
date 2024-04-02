<template>
  <div class="load-datasets">
    <h4>
      Load Data Sources
    </h4>

    <IconField class="search-field">
      <InputIcon class="pi pi-search"> </InputIcon>
      <InputText class="search-field-input" placeholder="Search Datasets" />
    </IconField>

    <div class="datasources">
      <Button outlined v-for="source in datasources" severity="info" class="datasource-button" :key="source"
        :label="source" />
      <Button icon="pi pi-plus" class="datasource-button" label="Add Source" />
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed } from "vue";

import InputText from "primevue/inputtext";
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import Button from 'primevue/button';

const datasources = [
  "Genomics Data Commons (GDC)",
  "Cancer Research Data Commons (CRDC)",
  "Proteomics Data Commons (PDC)",
  "Clinical and Translational Data Commons (CTDC)",
  "Imaging Data Commons (IDC)",
  "Cancer Data Service (CDS)",
];

</script>

<style lang="scss">
.load-datasets {
  position: relative;
  width: 20rem;

  h4 {
    margin-top: 0;
    padding-top: 0;
  }
}

.search-field {
  width: 20rem;
}

.search-field-input {
  width: 20rem;

  &::placeholder {
    color: var(--gray-400);
  }
}

.datasources {
  margin-top: 0.5rem;
}

.datasource-button {
  width: 100%;
  margin: 0.25rem 0;


  &.p-button {
    display: flex;
    justify-content: center;

    // .p-button-label {
    //   // flex: 1 1 auto;
    //   flex: 1;
    // }
    // .p-button-icon {
    //   flex: 1;
    // }

    // background: var(--primary-100);
    // border: var(--primary-200);
  }
}
</style>
