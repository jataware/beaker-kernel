<template>
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- DNA double helix structure -->
    <defs>
      <!-- gradient -->
      <linearGradient id="dnaGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="currentColor" stop-opacity="0.8"/>
        <stop offset="100%" stop-color="currentColor" stop-opacity="0.4"/>
      </linearGradient>
    </defs>
    
    <!-- left strand of DNA helix -->
    <path d="M6 2 Q8 6 6 10 Q4 14 6 18 Q8 22 6 24" 
          stroke="currentColor" 
          stroke-width="2.5" 
          fill="none" 
          opacity="0.9"/>
    
    <!-- right strand of DNA helix -->
    <path d="M18 2 Q16 6 18 10 Q20 14 18 18 Q16 22 18 24" 
          stroke="currentColor" 
          stroke-width="2.5" 
          fill="none" 
          opacity="0.9"/>
    
    <line x1="6.5" y1="4" x2="17.5" y2="4" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
    <line x1="7" y1="6" x2="17" y2="6" stroke="currentColor" stroke-width="1.5" opacity="0.6"/>
    <line x1="6.5" y1="8" x2="17.5" y2="8" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
    <line x1="5.5" y1="10" x2="18.5" y2="10" stroke="currentColor" stroke-width="1.5" opacity="0.8"/>
    <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.9"/>
    <line x1="5.5" y1="14" x2="18.5" y2="14" stroke="currentColor" stroke-width="1.5" opacity="0.8"/>
    <line x1="6.5" y1="16" x2="17.5" y2="16" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
    <line x1="7" y1="18" x2="17" y2="18" stroke="currentColor" stroke-width="1.5" opacity="0.6"/>
    <line x1="6.5" y1="20" x2="17.5" y2="20" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
    
    <!-- gene expression indicators -->
    <circle cx="9" cy="5" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="15" cy="7" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="11" cy="9" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="13" cy="11" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="10" cy="13" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="14" cy="15" r="1" fill="currentColor" opacity="0.6"/>
    <circle cx="12" cy="17" r="1" fill="currentColor" opacity="0.6"/>
    
    <!-- molecular structure -->
    <circle cx="9" cy="3" r="0.8" fill="currentColor" opacity="0.5"/>
    <circle cx="15" cy="3" r="0.8" fill="currentColor" opacity="0.5"/>
    <circle cx="12" cy="21" r="0.8" fill="currentColor" opacity="0.5"/>
  </svg>
</template>