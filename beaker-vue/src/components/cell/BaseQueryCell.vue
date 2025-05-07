<template>
  <div class="llm-query-cell">
    <slot name="query"></slot>
    <slot name="events"></slot>
    <slot name="thinking-indicator"></slot>
    <slot name="input-request"></slot>
  </div>
</template>
  
<script setup lang="ts">
import { useBaseQueryCell } from './BaseQueryCell';
</script>