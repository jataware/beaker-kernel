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

        <!-- <Card style="height: 6em;"> -->
        <div>
            <Panel
                class="log-panel"
                :class="{odd: index % 2 !== 0}"
                :data-index="logEntry.timestamp"
                v-for="(logEntry,index) in logEntries" :key="`${logEntry.type}-${logEntry.timestamp}`"
                :header="logEntry.type"
                >
                <vue-json-pretty
                    :data="logEntry.body"
                    :deep="2"
                    showLength
                    showIcon
                    :showDoubleQuotes="true"
                    :showLineNumber="false"
                />
            </Panel>
        </div>
        <!-- </Card> -->

    </Fieldset>

</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, computed, inject } from "vue";
import * as messages from '@jupyterlab/services/lib/kernel/messages';
import { IBeakerIOPubMessage } from 'beaker-kernel/notebook';
import { Codemirror } from "vue-codemirror";
import { oneDark } from '@codemirror/theme-one-dark';
import Button from 'primevue/button';
import AutoComplete from 'primevue/autocomplete';
import Fieldset from 'primevue/fieldset';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import Panel from 'primevue/panel';
import Card from 'primevue/card';


const props = defineProps([
    "session",
    "intercepts",
    "rawMessages",
]);

const showToast = inject('show_toast');
const theme = inject('theme');

const emit = defineEmits([
    "select-cell",
    "run-cell",
    "update-context-info",
]);

const codeExtensions = computed(() => {
    const ext = [];

    if (theme.value === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

const messageType = ref<string>();
const messageNum = ref(1)
const messageContent = ref<string>("{\n}");
const messageOptions = ref([]);
// const messageMessages = ref<object[]>([]);
const messageId = ref<string|undefined>(undefined);

const sendMessage = () => {
    messageId.value = `beaker-custom-${messageType.value}-${messageNum.value}`;
    messageNum.value += 1;
    const future = props.session.sendBeakerMessage(
        messageType.value,
        JSON.parse(messageContent.value),
        messageId.value,
    );
    future.done.then(() => {
        showToast({title: 'Success', detail: 'Message processed.'});
    });
};

const allMessageOptions = computed(() => {
    return Object.keys(props.intercepts);
});

const search = (event: any) => {
    messageOptions.value = event.query ?
        allMessageOptions.value.filter((item) => item.includes(event.query)) :
        Object.keys(props.intercepts);
};

const logEntries = computed(() => {
    if (!messageId.value) {
        return [];
    }
    return props.rawMessages.filter((item) => {return (item.body.header.msg_id === messageId.value || item.body.parent_header.msg_id === messageId.value)});
});

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
