<template>
    <Fieldset
        legend="Message"
        :class="{'custom-message-container': true, 'expanded': props.expanded}"
    >
        <div class="code">
            <Codemirror
                :tab-size="2"
                :extensions="codeExtensions"
                language="javascript"
                v-model="messageContent"
            />
        </div>

        <br />

        <InputGroup class="type-send">
            <InputText
                size="small"
                v-model="messageType"
                placeholder="Type"
            />
            <Button
                icon="pi pi-bolt"
                size="small"
                @click="sendMessage"
                label="Send"
                iconPos="right"
            />
        </InputGroup>
    </Fieldset>

</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, computed } from "vue";
import { Codemirror } from "vue-codemirror";
import { oneDark } from '@codemirror/theme-one-dark';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import InputGroup from 'primevue/inputgroup';
import Fieldset from 'primevue/fieldset';


const props = defineProps([
    "session",
    "expanded",
    "theme"
]);

// const query = ref("");
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

const sendMessage = () => {
    const future = props.session.sendBeakerMessage(
        messageType.value,
        JSON.parse(messageContent.value),
    );
    future.done.then();
};
</script>


<style lang="scss" scoped>

.type-send {
    width: 60%;

    @media (max-width: 900px) {
        width: 100%;
    }
}

.code {
    border: 1px solid var(--surface-b);
}


</style>
