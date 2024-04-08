<template>
  <div class="load-sources">

    <div class="steps">
      <Breadcrumb :home="stepperHome" :model="stepperItems">
        <template #item="{ item }">
          <span :class="{ 'step-available': currStep > item.code }"
            @click="nextStep(currStep > item.code ? item.code : true)">{{ item.label }}</span>
        </template>
      </Breadcrumb>
    </div>


    <div v-if="currStep === Steps.sources">

      <IconField class="search-field">
        <InputIcon class="pi pi-search"> </InputIcon>
        <InputText class="search-field-input" placeholder="Search Datasources" />
      </IconField>

      <div class="datasources">
        <Card class="source-card" @click="nextStep(source.name)" :key="source.id" v-for="source in sources">
          <template #content>

            <div class="source-card-header">
              <img v-if="source.logo_url" alt="datasource logo" class="source-image" :src="source.logo_url" />
              <span v-else>{{ source.name }} ({{ source.initials }})</span>
            </div>

            <p class="m-0 source-description">
              {{ source.description }}
            </p>
            <div class="source-file-exports" v-if="source?.file_formats?.length">
              <h4>File Exports</h4>
              <ul>
                <li v-for="format in source.file_formats" :key="format">{{ format }}</li>
              </ul>
            </div>
            <div class="source-data-access">
              <h4>Data Access:</h4>
              &nbsp;<span>{{ source.access_type }}</span>
            </div>
          </template>
          <template #footer>
            <div class="flex gap-3 mt-1">
            </div>
          </template>
        </Card>

      </div>
    </div>

    <div class="query" v-else-if="currStep === Steps.query">

      <h2>
        {{ selectedSource }}
      </h2>

      <h3>
        Describe a Dataset to Fetch
      </h3>

      <div class="query-input-container">
        <ContainedTextArea @submit="handleDatasetQuery" v-model="datasetQuery"
          style="flex: 1; margin-right: 0.75rem; max-width: 40rem;" />

      </div>

      <Button @click="handleDatasetQuery" class="query-submit-button" label="Search" />
    </div>

    <div class="processing" v-else-if="currStep === Steps.process">
      <h2>
        Fetching your data
      </h2>

      <div class="loading-progress">
        <ProgressSpinner />
      </div>

    </div>

    <!--
    <Button class="datasource-button">
      <i class="pi pi-plus" style="margin-right: 0.5rem;" />
      <span>
        Add Source
      </span>
    </Button>
    -->
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits, computed, onMounted } from "vue";

import InputText from "primevue/inputtext";
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Breadcrumb from 'primevue/breadcrumb';
// import datasources from '../datasources.ts';
import ContainedTextArea from './ContainedTextArea.vue';
import ProgressSpinner from 'primevue/progressspinner';

const sources = ref([]);
const datasetQuery = ref("");


const Steps = {
  sources: 0,
  query: 1,
  process: 2,
  success: 3
};

const currStep = ref(Steps.sources);

onMounted(() => {

  fetch('http://localhost:8001/api/sources')
    .then(response => {
      return response.json();
    })
    .then(data => {

      // console.log('data', data);

      sources.value = data.sources;
    });

});

const stepperHome = ref({
  label: 'Load Data Sources', code: Steps.sources // change to Sources on step 1+
});
const stepperItems = ref([]);

const selectedSource = ref('');

const codeToStep = {
  0: 'Sources',
  1: 'Query',
  2: 'Process',
  3: 'Success'
};

function nextStep(forceStep) {
  console.log('forceStep', forceStep, typeof forceStep);

  if (Number.isInteger(forceStep)) {
    for (let i = 0; i < currStep.value - forceStep; i++) {
      stepperItems.value.pop();
    }
    currStep.value = forceStep;

    if (forceStep === 0) {
      stepperHome.value.label = 'Load Data Sources';
    }

  } else if (!forceStep || typeof forceStep === 'string') {
    stepperHome.value.label = 'Sources';
    const newStep = currStep.value + 1;
    stepperItems.value.push({ label: codeToStep[newStep], code: newStep });
    currStep.value = newStep;

    if (typeof forceStep === 'string') {
      selectedSource.value = forceStep;
    }
  }
}

function handleDatasetQuery() {
  const newStep = currStep.value + 1;
  stepperItems.value.push({ label: codeToStep[newStep], code: newStep });
  currStep.value = newStep;
}

</script>

<style lang="scss">
.load-sources {
  position: relative;
  display: flex;
  flex-direction: column;
  margin-top: -1rem;

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
  position: relative;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
  grid-gap: 0.75rem;
}

.datasource-button {
  width: 100%;
  margin: 0.25rem 0;

  &.p-button {
    display: flex;
    justify-content: center;
  }
}

.source-card {
  position: relative;
  overflow: hidden;
  width: 100%;
  border: 1px solid var(--surface-400);
  box-shadow: none;
  cursor: pointer;

  &:hover {
    // background: var(--surface-50);
    box-shadow: 0 2px 1px 0px rgba(0, 110, 130, 0.1), 0 1px 1px 0 rgba(0, 110, 130, 0.1), 2px 2px 2px 0 rgba(0, 110, 130, 0.1);
  }

  .p-card-content {
    padding: 0;
  }
}


.source-description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
  overflow: hidden;
  min-height: 4rem;
  color: var(--gray-700);
}

.source-card-header {}

.source-image {
  width: 100%;
}

.source-data-access {
  color: var(--text-color-secondary);

  h4 {
    color: var(--gray-600);
    margin: 0;
    padding: 0;
    display: inline;
  }
}

.source-file-exports {

  color: var(--text-color-secondary);

  ul {
    list-style: none;
    padding: 0.5rem 0;
    // color: var(--text-color-secondary);
    color: var(--gray-600);

    display: inline-flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    margin-block-start: 0px;
    margin-block-end: 0px;
    margin-inline-start: 0px;
    margin-inline-end: 0px;
    padding-inline-start: 0px;

    li {
      padding: 0 0.25rem;
    }
  }

  h4 {
    color: var(--gray-600);
    padding: 0;
    margin: 0;
  }
}

.steps {
  background: none;
  display: flex;

  .p-breadcrumb {
    background: var(--surface-a);
    padding: 1rem 0;
  }

  .p-menuitem {
    font-weight: 400;
    color: var(--text-color-secondary);
    cursor: default;
  }

}

.query,
.processing {
  padding: 0rem 0.5rem 0.5rem 0.5rem;

  h3 {
    margin-block-start: 0;
    margin-block-end: 0;
    font-weight: normal;
  }

  h2 {
    font-weight: 200;
  }
}

.step-available {
  cursor: pointer;
}

.query-submit-button {
  margin-top: 1rem;
}

.loading-progress {
  width: 100%;
  height: 20rem;
  display: flex;
  justify-content: center;
  margin-top: 3rem;

}
</style>
