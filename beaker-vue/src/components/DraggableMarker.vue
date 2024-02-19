<template>
<div class="draggable-wrapper">
    <svg viewBox="0 0 32 32" class="draggable-indicator">
      <circle r="2" cy="4"  cx="2" />
      <circle r="2" cy="14" cx="2" />
      <circle r="2" cy="24" cx="2" />
      <circle r="2" cy="34" cx="2" />

      <circle r="2" cy="4"  cx="10" />
      <circle r="2" cy="14" cx="10" />
      <circle r="2" cy="24" cx="10" />
      <circle r="2" cy="34" cx="10" />

      <circle r="2" cy="4"  cx="18" />
      <circle r="2" cy="14" cx="18" />
      <circle r="2" cy="24" cx="18" />
      <circle r="2" cy="34" cx="18" />
    </svg>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
// top-level wrapper that aligns/pads with the rest of parent layout
.draggable-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  padding: 0.35rem 0.6rem 0 0;
  position: relative;
  cursor: grab;
}

// The direct rectangular container of the dots
.draggable-indicator {
  max-width: 2.5rem;
  height: 3rem;
  padding: 0 0 0.25rem 0.65rem;
  border-radius: 4px;
}

/* individual dots */
.draggable-indicator circle {
	fill:#a38efe88;
  opacity: 0.9;
}
</style>
