<template>
  <div :id="divId" class="decapode-graph" @resize="resize"></div>
</template>

<script setup>
import { defineProps, defineEmits, computed, ref, nextTick, inject, onMounted, onBeforeUnmount } from "vue";
import Textarea from 'primevue/textarea';
import cytoscape from "cytoscape";
import { v4 as uuidv4 } from 'uuid';

const props = defineProps([
  "data",
]);

const divId = ref(String(uuidv4()));
const cy = ref();
const layoutConfig = {
  name: 'breadthfirst'
}

const nodes = computed(() => props.data.graph.V.map(e => {return {group: 'nodes', data: {id: e["_id"], color: 'green', ...e.vprops}}}));
const edges = computed(() => props.data.graph.E.map(e => {return {group: 'edges', data: {id: `${e.src}-${e.tgt}`, source: e.src, target: e.tgt, ...e.eprops}}}));

var resizingTimeout = null;
const resize = () => {
  // Since this is somewhat resource intensive, only actually relayout at most every 150ms.
  if (resizingTimeout === null) {
    resizingTimeout = setTimeout(() => {
      cy.value.layout(layoutConfig).run();
      cy.value.fit();
      resizingTimeout = null;
    }, 150);
  }
}

const resizeObserver = new ResizeObserver(resize);

onMounted(() => {
  const el = document.getElementById(divId.value);
  cy.value = cytoscape({
    elements: {
      nodes: nodes.value,
      edges: edges.value,
    },
    container: el,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'shape': 'data(shape)',
          'background-color': 'data(color)',
        },
      },
      {
        selector: 'edge',
        style: {
          'label': 'data(label)',
          'line-style': 'data(style)',
        }
      }
    ],
    layout: layoutConfig,
    wheelSensitivity: 0.1,
  });
  resizeObserver.observe(el);
  cy.value.layout(layoutConfig).run();
  cy.value.fit();
})

onBeforeUnmount(() => {
  console.log("unmounting");
  const el = document.getElementById(divId.value);
  console.log(el);
  if (el) {
    resizeObserver.unobserve(el);
  }
});

</script>

<style lang="scss">

.decapode-graph {
  width: 100%;
  height: 600px;
  background-color: lightgray;
}

</style>
