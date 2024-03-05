<template>
    <div class="execute-action-container">
        <AutoComplete
            class="action-name-input"
            placeholder="Action Name"
            dropdown
            v-model="actionType"
            :suggestions="actionOptions"
            @complete="search"
            @item-select="actionSelected"
            dropdownClass="ac-button"
        />

        <div class="docs">
            <div v-if="selectedActionName">
                <span style="font-weight: bold">{{ selectedActionName }}</span><br/><br/><span>{{ actionDocs }}</span>
            </div>
            <div v-else>
                Select an action to see the docstring...
            </div>
        </div>

        <div class="code">
            Action Payload
            <Codemirror
                :tab-size="2"
                :extensions="codeExtensions"
                language="javascript"
                v-model="actionPayload"
            />
        </div>

        <Button
            icon="pi pi-bolt"
            size="small"
            @click="executeAction"
            label="Send"
            iconPos="right"
        />
        <h3>Results:</h3>

        <Fieldset
            legend="Reply"
            :toggleable="true"
        >
            <VueJsonPretty v-if="reply" :data="reply"/>
        </Fieldset>

        <Fieldset
            legend="Response (Optional)"
            :toggleable="true"
        >
            <VueJsonPretty v-if="response" :data="response"/>
        </Fieldset>

        <Fieldset
            legend="Raw Messages (Debug)"
            :toggleable="true"
            :collapsed="true"
        >
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
        </Fieldset>

    </div>

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


const props = defineProps([
    "actions",
    "rawMessages",
]);

const session = inject('session');

const showToast = inject('show_toast');
const theme = inject('theme');

const codeExtensions = computed(() => {
    const ext = [];

    if (theme.value === 'dark') {
        ext.push(oneDark);
    }
    return ext;

});

const actionType = ref<string>();
const actionPayload = ref<string>("{\n}");
const actionOptions = ref([]);
const actionDocs = ref<string|undefined>();
const selectedActionName = ref<string|undefined>()
const messageNum = ref(1)
const messageId = ref<string|undefined>(undefined);
const response = ref<any>();
const result = ref<any>();
const reply = ref<any>();

const executeAction = () => {
    messageId.value = `beaker-custom-${actionType.value}-${messageNum.value}`;
    messageNum.value += 1;
    const future = session.executeAction(
        actionType.value,
        JSON.parse(actionPayload.value),
        messageId.value,
    );
    future.onResponse = async (msg: messages.IIOPubMessage) => {
        console.log("I'm here!", msg);
        response.value = msg;
    };
    future.onReply = async (msg: messages.IExecuteReply) => {
        reply.value = msg;
    }
    future.done.then(() => {
        showToast({title: 'Success', detail: 'Message processed.'});
    });
};

const allMessageOptions = computed(() => {
    return Object.keys(props.actions);
});

const search = (event: any) => {
    actionOptions.value = event.query ?
        allMessageOptions.value.filter((item) => item.includes(event.query)) :
        Object.keys(props.actions);
};

const actionSelected = (event: any) => {
    selectedActionName.value = event.value;
    const selectedAction = props.actions[event.value];
    if (selectedAction === undefined) {
        return;
    }
    actionPayload.value = selectedAction.default_payload;
    actionDocs.value = selectedAction.docs;
}

const logEntries = computed(() => {
    if (!messageId.value) {
        return [];
    }
    return props.rawMessages.filter((item) => {return (item.body.header?.msg_id === messageId.value || item.body.parent_header?.msg_id === messageId.value)});
});

</script>


<style lang="scss">

.execute-action-container {
    & > *{
        margin-bottom: 1rem;
    }
}

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

.action-name-input {
    width: 100%;
}

.code {
    border: 1px solid var(--surface-b);
    flex: 1;
    width: 100%;
}

.docs {
    white-space: pre-wrap;

}

</style>
