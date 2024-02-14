<template>
    <Fieldset
        legend="Message"
        class="custom-message"
    >
        <AutoComplete
            class="message-input"
            placeholder="Message Type"
            dropdown
            v-model="messageType"
            inputId="custom-message-input"
            :suggestions="messageOptions"
            @complete="search"
            dropdown-mode="blank"
            dropdownClass="ac-button"
        />

        <br />

        <div class="code">
            <Codemirror
                :tab-size="2"
                :extensions="codeExtensions"
                language="javascript"
                v-model="messageContent"
            />
        </div>

        <br />

        <Button
            icon="pi pi-bolt"
            size="small"
            @click="sendMessage"
            label="Send"
            iconPos="right"
        />
    </Fieldset>

</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, computed, inject } from "vue";
import { Codemirror } from "vue-codemirror";
import { oneDark } from '@codemirror/theme-one-dark';
import Button from 'primevue/button';
import AutoComplete from 'primevue/autocomplete';
import Fieldset from 'primevue/fieldset';


const props = defineProps([
    "session",
    "theme",
    "intercepts"
]);

const showToast = inject('show_toast');

const emit = defineEmits([
    "select-cell",
    "run-cell",
    "update-context-info",
]);

const codeExtensions = computed(() => {
    const ext = [];

    if (props.theme === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

const messageType = ref<string>();
const messageContent = ref<string>("{\n}");
const messageOptions = ref(props.intercepts);

const sendMessage = () => {
    const future = props.session.sendBeakerMessage(
        messageType.value,
        JSON.parse(messageContent.value),
    );
    future.done.then(() => {
        showToast('Success', 'Message processed.');
    });
};

const search = (event) => {
    messageOptions.value = event.query ?
        props.intercepts.filter((item) => item.includes(event.query))
        : props.intercepts;
};

</script>


<style lang="scss">

.p-autocomplete-items {
    .p-autocomplete-empty-message {
        padding-left: 1rem;
    }
}

.custom-message {
    .p-fieldset-content {
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-evenly;
        align-items: center;
    }
    .p-autocomplete-input {
        height: 2rem;
    }
}

.message-input {
    width: 100%;
}

.code {
    border: 1px solid var(--surface-b);
    flex: 1;
    width: 100%;
}

.ac-button {
    &.p-button {
        height: 2rem;
    }
}


</style>
