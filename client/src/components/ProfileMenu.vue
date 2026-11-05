<template>
  <div class="profile-menu">
    <button
      class="profile-button"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <div class="avatar">
        {{ getInitials(currentUser.name) }}
      </div>
      <span class="profile-name">{{ currentUser.name }}</span>
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
      <div class="dropdown-header">
        <div class="avatar-large">
          {{ getInitials(currentUser.name) }}
        </div>
        <div class="user-info">
          <div class="user-name">{{ currentUser.name }}</div>
          <div class="user-email">{{ currentUser.email }}</div>
        </div>
      </div>

      <div class="menu-sep"></div>

      <button
        class="menu-item"
        @mousedown.prevent="showProfileDetails"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 9C10.6569 9 12 7.65685 12 6C12 4.34315 10.6569 3 9 3C7.34315 3 6 4.34315 6 6C6 7.65685 7.34315 9 9 9Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M15 15C15 12.7909 12.3137 11 9 11C5.68629 11 3 12.7909 3 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        {{ t('profile.profileDetails') }}
      </button>

      <button
        class="menu-item"
        @mousedown.prevent="showTasks"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M15 3H3C2.44772 3 2 3.44772 2 4V14C2 14.5523 2.44772 15 3 15H15C15.5523 15 16 14.5523 16 14V4C16 3.44772 15.5523 3 15 3Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M6 7L8 9L12 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('profile.myTasks') }}
        <span v-if="pendingTaskCount > 0" class="task-badge">{{ pendingTaskCount }}</span>
      </button>

      <div class="menu-sep"></div>

      <button
        class="menu-item logout"
        @mousedown.prevent="handleLogout"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M7 15H4C3.44772 15 3 14.5523 3 14V4C3 3.44772 3.44772 3 4 3H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M11 12L15 9M15 9L11 6M15 9H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('profile.logout') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, logout, getInitials } = useAuth()
const { t } = useI18n()

const isDropdownOpen = ref(false)
const emit = defineEmits(['show-profile-details', 'show-tasks'])

const pendingTaskCount = computed(() => {
  return currentUser.value.tasks.filter(task => task.status === 'pending').length
})

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const showProfileDetails = () => {
  isDropdownOpen.value = false
  emit('show-profile-details')
}

const showTasks = () => {
  isDropdownOpen.value = false
  emit('show-tasks')
}

const handleLogout = () => {
  isDropdownOpen.value = false
  logout()
}
</script>

<style scoped>
.profile-menu {
  position: relative;
}

.popover {
  min-width: 17rem;
}

.profile-button {
  display: flex;
  align-items: center;
  gap: var(--s-2);
  height: 30px;
  padding: 0 var(--s-2) 0 var(--s-1);
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  transition: transform var(--dur-ui) var(--ease-out), border-color var(--dur-ui) ease;
}

.profile-button:active {
  transform: scale(0.97);
}

@media (hover: hover) and (pointer: fine) {
  .profile-button:hover {
    border-color: var(--ink);
  }
}

.avatar,
.avatar-large {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--ink);
  color: var(--paper);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.avatar {
  width: 22px;
  height: 22px;
  font-size: var(--fs-label);
}

.avatar-large {
  width: 40px;
  height: 40px;
  font-size: var(--fs-base);
}

.profile-name {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--ink);
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

.dropdown-header {
  padding: var(--s-4);
  display: flex;
  gap: var(--s-3);
  align-items: center;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-family: var(--font-serif);
  font-weight: 600;
  font-size: var(--fs-md);
  line-height: 1.2;
}

.user-email {
  font-size: var(--fs-sm);
  color: var(--ink-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-item svg {
  width: 16px;
  height: 16px;
  color: var(--ink-3);
  flex-shrink: 0;
}

.menu-item.logout,
.menu-item.logout svg {
  color: var(--bad);
}

.task-badge {
  margin-left: auto;
  min-width: 20px;
  padding: 0 6px;
  background: var(--signal);
  color: var(--ink);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  font-weight: 600;
  text-align: center;
}
</style>
