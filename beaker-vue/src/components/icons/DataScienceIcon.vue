<template>
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- grid of binary numbers with data visualization elements -->
    <defs>
      <pattern id="binaryGrid" x="0" y="0" width="4" height="4" patternUnits="userSpaceOnUse">
        <rect width="4" height="4" fill="transparent"/>
        <text x="2" y="3" font-size="2" text-anchor="middle" fill="currentColor" opacity="0.4">1</text>
      </pattern>
    </defs>
    
    <!-- background binary grid -->
    <rect x="2" y="2" width="20" height="20" fill="url(#binaryGrid)"/>
    
    <!-- binary numbers scattered -->
    <text x="3" y="5" font-size="2.5" fill="currentColor" opacity="0.6">0</text>
    <text x="7" y="4" font-size="2.5" fill="currentColor" opacity="0.5">1</text>
    <text x="11" y="6" font-size="2.5" fill="currentColor" opacity="0.4">0</text>
    <text x="15" y="4" font-size="2.5" fill="currentColor" opacity="0.6">1</text>
    <text x="19" y="5" font-size="2.5" fill="currentColor" opacity="0.5">0</text>
    
    <text x="4" y="9" font-size="2.5" fill="currentColor" opacity="0.5">1</text>
    <text x="8" y="8" font-size="2.5" fill="currentColor" opacity="0.6">0</text>
    <text x="16" y="9" font-size="2.5" fill="currentColor" opacity="0.4">1</text>
    <text x="20" y="8" font-size="2.5" fill="currentColor" opacity="0.6">0</text>
    
    <!-- data visualization chart overlay -->
    <path d="M4 16 L8 12 L12 14 L16 10 L20 11" 
          stroke="currentColor" 
          stroke-width="2" 
          fill="none" 
          opacity="0.8"/>
    
    <!-- data points -->
    <circle cx="4" cy="16" r="1.5" fill="currentColor" opacity="0.9"/>
    <circle cx="8" cy="12" r="1.5" fill="currentColor" opacity="0.9"/>
    <circle cx="12" cy="14" r="1.5" fill="currentColor" opacity="0.9"/>
    <circle cx="16" cy="10" r="1.5" fill="currentColor" opacity="0.9"/>
    <circle cx="20" cy="11" r="1.5" fill="currentColor" opacity="0.9"/>
    
    <text x="3" y="20" font-size="2.5" fill="currentColor" opacity="0.4">1</text>
    <text x="7" y="19" font-size="2.5" fill="currentColor" opacity="0.5">0</text>
    <text x="11" y="21" font-size="2.5" fill="currentColor" opacity="0.6">1</text>
    <text x="15" y="19" font-size="2.5" fill="currentColor" opacity="0.4">0</text>
    <text x="19" y="20" font-size="2.5" fill="currentColor" opacity="0.5">1</text>
  </svg>
</template>