<template>
  <div class="language-switcher">
    <button
      class="language-button"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span class="language-label">{{ localeName }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="popover">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="menu-item"
        :class="{ 'is-active': currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-button {
  display: flex;
  align-items: center;
  gap: var(--s-2);
  width: 100%;
  height: 30px;
  padding: 0 var(--s-2);
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: var(--fs-base);
  color: var(--ink);
  transition: transform var(--dur-press) var(--ease-out), background-color 120ms ease;
}

.language-button:active {
  transform: scale(0.98);
}

@media (hover: hover) and (pointer: fine) {
  .language-button:hover {
    background: color-mix(in srgb, var(--rule) 55%, transparent);
  }
}

.globe-icon,
.chevron {
  flex-shrink: 0;
}

.globe-icon {
  width: 15px;
  height: 15px;
  color: var(--ink-3);
}

.language-label {
  flex: 1;
  text-align: left;
}

.chevron {
  width: 12px;
  height: 12px;
  color: var(--ink-3);
  transition: transform 200ms var(--ease-out);
}

.chevron-open {
  transform: rotate(180deg);
}

/* opens upward from the sidebar foot */
.popover {
  top: auto;
  right: 0;
  bottom: calc(100% + var(--s-1));
  left: 0;
  transform-origin: bottom left;
}

.language-name {
  flex: 1;
}

.check-icon {
  width: 14px;
  height: 14px;
  color: var(--signal-text);
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .language-button {
    width: auto;
  }
  .language-label {
    flex: none;
  }
  .popover {
    top: calc(100% + var(--s-1));
    right: auto;
    bottom: auto;
    min-width: 9rem;
    transform-origin: top left;
  }
}
</style>
