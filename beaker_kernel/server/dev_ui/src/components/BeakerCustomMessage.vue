<template>
    <div :class="{'custom-message-container': true, 'expanded': props.expanded}">
        <div>
            <input v-model="messageType" placeholder="Message Type"/>
            <div class="message-content-container">
                <Codemirror
                    :tab-size="2"
                    language="javascript"
                    v-model="messageContent"
                />
            </div>
            <button @click="sendMessage">Send</button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref } from "vue";
import { Codemirror } from "vue-codemirror";

const props = defineProps([
    "session",
    "expanded",
]);

const query = ref("");
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


<style>
.custom-message-container {
    /* padding: 0.5em; */
    height: 0px;
    overflow: hidden;
    /* min-height: 300px; */
    /* margin-top: -100%; */
    transition: all 0s;
    display: hidden;
}

.custom-message-container.expanded {
    border: 1px solid darkgray;
    height: auto;
    padding: 0.5em;
    display: block;
}

.message-content-container {
    /* display: inline; */
    width: 80%;
    border: 1px solid lightgray;
}


</style>
