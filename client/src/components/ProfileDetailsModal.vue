<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-scrim" @click="close">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="profile-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="profile-modal-title" class="modal-heading">{{ t('profileDetails.title') }}</h3>
          <button class="modal-x" :aria-label="t('profileDetails.close')" @click="close">&times;</button>
        </div>

        <div class="modal-content">
          <div class="person-head">
            <div class="avatar" aria-hidden="true">{{ getInitials(currentUser.name) }}</div>
            <div>
              <h4 class="person-name">{{ currentUser.name }}</h4>
              <p class="muted">{{ currentUser.jobTitle }}</p>
            </div>
          </div>

          <div class="fields">
            <div class="field-row">
              <span class="label">{{ t('profileDetails.email') }}</span>
              <span>{{ currentUser.email }}</span>
            </div>
            <div class="field-row">
              <span class="label">{{ t('profileDetails.department') }}</span>
              <span>{{ currentUser.department }}</span>
            </div>
            <div class="field-row">
              <span class="label">{{ t('profileDetails.location') }}</span>
              <span>{{ currentUser.location }}</span>
            </div>
            <div class="field-row">
              <span class="label">{{ t('profileDetails.phone') }}</span>
              <span class="mono">{{ currentUser.phone }}</span>
            </div>
            <div class="field-row">
              <span class="label">{{ t('profileDetails.joinDate') }}</span>
              <span>{{ formatDate(currentUser.joinDate) }}</span>
            </div>
            <div class="field-row">
              <span class="label">{{ t('profileDetails.employeeId') }}</span>
              <span class="mono">CC-{{ currentUser.id.toString().padStart(5, '0') }}</span>
            </div>
          </div>
        </div>

        <div class="modal-foot">
          <button class="btn" @click="close">{{ t('profileDetails.close') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, getInitials } = useAuth()
const { t, currentLocale } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.person-head {
  display: flex;
  align-items: center;
  gap: var(--s-4);
  padding-bottom: var(--s-4);
  margin-bottom: var(--s-4);
  border-bottom: var(--hair);
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border: var(--line);
  border-radius: var(--radius);
  background: var(--paper-sunk);
  font-family: var(--font-serif);
  font-size: var(--fs-lg);
  font-weight: 600;
}

.person-name {
  font-size: var(--fs-lg);
}

.fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  column-gap: var(--s-5);
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: var(--s-1);
  padding: var(--s-2) 0;
  border-bottom: var(--hair);
}
</style>
