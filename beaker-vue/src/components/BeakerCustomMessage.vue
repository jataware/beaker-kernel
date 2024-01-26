<template>
    <Fieldset
        legend="Message"
        :class="{'custom-message-container': true, 'expanded': props.expanded}"
    >
        <div class="code">
            <Codemirror
                :tab-size="2"
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
import { defineProps, defineEmits, ref } from "vue";
import { Codemirror } from "vue-codemirror";
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
// import Panel from 'primevue/panel';
import InputGroup from 'primevue/inputgroup';
import Fieldset from 'primevue/fieldset';


const props = defineProps([
    "session",
    "expanded",
]);

// const query = ref("");
const emit = defineEmits([
    "select-cell",
    "run-cell",
    "update-context-info",
]);

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
.custom-message-container {
    // overflow: hidden;
    // display: hidden;
}

.custom-message-container.expanded {
    // border: 1px solid darkgray;
    // height: auto;
    // padding: 0.5em;
    // display: block;
}

.message-content-container {
    /* display: inline; */
    // border: 1px solid lightgray;
}

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
