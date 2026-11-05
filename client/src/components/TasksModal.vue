<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-scrim" @click="close">
      <div class="modal-panel tasks-panel" role="dialog" aria-modal="true" aria-labelledby="tasks-modal-title" @click.stop>
        <div class="modal-head">
          <h3 id="tasks-modal-title" class="modal-heading">{{ t('tasks.title') }}</h3>
          <button class="modal-x" :aria-label="t('profileDetails.close')" @click="close">&times;</button>
        </div>

        <div class="modal-content">
          <!-- Add Task Form -->
          <div class="task-form">
            <div class="field">
              <label for="task-title">{{ t('tasks.taskTitle') }}</label>
              <input
                id="task-title"
                v-model="newTask.title"
                type="text"
                :placeholder="t('tasks.taskTitlePlaceholder')"
                class="input"
                @keyup.enter="handleAddTask"
              />
            </div>

            <div class="form-row">
              <div class="field">
                <label for="task-priority">{{ t('tasks.priority') }}</label>
                <select id="task-priority" v-model="newTask.priority" class="select">
                  <option value="high">{{ t('priority.high') }}</option>
                  <option value="medium">{{ t('priority.medium') }}</option>
                  <option value="low">{{ t('priority.low') }}</option>
                </select>
              </div>

              <div class="field">
                <label for="task-due-date">{{ t('tasks.dueDate') }}</label>
                <input id="task-due-date" v-model="newTask.dueDate" type="date" class="input" />
              </div>

              <button
                class="btn btn--primary"
                :disabled="!newTask.title.trim() || !newTask.dueDate"
                @click="handleAddTask"
              >
                {{ t('tasks.addTask') }}
              </button>
            </div>
          </div>

          <!-- Tasks List -->
          <div v-if="sortedTasks.length === 0" class="empty">
            {{ t('tasks.noTasks') }}
          </div>

          <ul v-else class="tasks-list">
            <li
              v-for="task in sortedTasks"
              :key="task.id"
              class="task-item"
              :class="[`priority-${task.priority}`, { completed: task.status === 'completed' }]"
            >
              <input
                type="checkbox"
                :checked="task.status === 'completed'"
                :aria-label="task.title"
                class="task-checkbox"
                @change="$emit('toggle-task', task.id)"
              />
              <div class="task-main">
                <span class="task-title" @click="$emit('toggle-task', task.id)">{{ task.title }}</span>
                <div class="task-meta">
                  <span class="tag" :class="priorityTag(task.priority)">{{ translatePriority(task.priority) }}</span>
                  <span class="mono muted">{{ formatDueDate(task.dueDate) }}</span>
                  <span class="tag task-status" :class="statusTag(task.dueDate, task.status)">
                    {{ getStatusText(task.dueDate, task.status) }}
                  </span>
                </div>
              </div>
              <button
                class="btn btn--sm btn--icon"
                title="Delete task"
                aria-label="Delete task"
                @click="$emit('delete-task', task.id)"
              >
                &times;
              </button>
            </li>
          </ul>
        </div>

        <div class="modal-foot">
          <button class="btn" @click="close">{{ t('profileDetails.close') }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'TasksModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    tasks: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'add-task', 'delete-task', 'toggle-task'],
  setup(props, { emit }) {
    const { t, currentLocale } = useI18n()
    const newTask = ref({
      title: '',
      priority: 'medium',
      dueDate: ''
    })

    const sortedTasks = computed(() => {
      // Don't sort - just return tasks in their current order (newest first)
      return [...props.tasks]
    })

    const close = () => {
      emit('close')
    }

    const handleAddTask = () => {
      if (newTask.value.title.trim() && newTask.value.dueDate) {
        emit('add-task', {
          title: newTask.value.title.trim(),
          priority: newTask.value.priority,
          dueDate: newTask.value.dueDate
        })
        newTask.value = {
          title: '',
          priority: 'medium',
          dueDate: ''
        }
      }
    }

    const formatDueDate = (dateString) => {
      const date = new Date(dateString)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const dueDate = new Date(date)
      dueDate.setHours(0, 0, 0, 0)

      const diffTime = dueDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const isJapanese = currentLocale.value === 'ja'

      if (diffDays === 0) return isJapanese ? '今日' : 'today'
      if (diffDays === 1) return isJapanese ? '明日' : 'tomorrow'
      if (diffDays === -1) return isJapanese ? '昨日' : 'yesterday'
      if (diffDays < 0) return isJapanese ? `${Math.abs(diffDays)}日前` : `${Math.abs(diffDays)} days ago`
      if (diffDays < 7) return isJapanese ? `${diffDays}日後` : `in ${diffDays} days`

      const locale = isJapanese ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
      })
    }

    const getStatusClass = (dueDate, status) => {
      if (status === 'completed') return 'completed'

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const due = new Date(dueDate)
      due.setHours(0, 0, 0, 0)

      const diffTime = due - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) return 'overdue'
      if (diffDays <= 1) return 'urgent'
      return 'upcoming'
    }

    const getStatusText = (dueDate, status) => {
      const isJapanese = currentLocale.value === 'ja'

      if (status === 'completed') return isJapanese ? '完了' : 'Completed'

      const statusClass = getStatusClass(dueDate, status)
      if (statusClass === 'overdue') return isJapanese ? '期限超過' : 'Overdue'
      if (statusClass === 'urgent') return isJapanese ? 'もうすぐ期限' : 'Due Soon'
      return isJapanese ? '予定' : 'Upcoming'
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    const priorityTag = (priority) => {
      const map = { high: 'tag--bad', medium: 'tag--warn', low: 'tag--info' }
      return map[priority] || ''
    }

    const statusTag = (dueDate, status) => {
      const map = { completed: 'tag--ok', overdue: 'tag--bad', urgent: 'tag--warn', upcoming: 'tag--info' }
      return map[getStatusClass(dueDate, status)]
    }

    return {
      t,
      newTask,
      sortedTasks,
      close,
      handleAddTask,
      formatDueDate,
      getStatusClass,
      getStatusText,
      priorityTag,
      statusTag,
      translatePriority
    }
  }
}
</script>


<style scoped>
.tasks-panel {
  max-width: 56rem;
}

.task-form {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding-bottom: var(--s-4);
  margin-bottom: var(--s-4);
  border-bottom: var(--line);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: end;
  gap: var(--s-3);
}

.tasks-list {
  list-style: none;
}

.task-item {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  padding: var(--s-3) 0 var(--s-3) var(--s-3);
  border-bottom: var(--hair);
  border-left: 3px solid var(--rule-strong);
}

.task-item.priority-high {
  border-left-color: var(--bad);
}

.task-item.priority-medium {
  border-left-color: var(--warn);
}

.task-item.priority-low {
  border-left-color: var(--info);
}

.task-checkbox {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--ink);
}

.task-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--s-1);
  min-width: 0;
}

.task-title {
  cursor: pointer;
  user-select: none;
  font-weight: 600;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--ink-3);
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-3);
  font-size: var(--fs-sm);
}

.task-status {
  margin-left: auto;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
