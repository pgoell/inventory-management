<template>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <svg width="14" height="14" viewBox="0 0 14 14"><path d="M2 2h4v4H2zM8 2h4v4H8zM2 8h4v4H2z" fill="#fff" /><path d="M8 8h4v4H8z" fill="#6f93ff" /></svg>
        </div>
        <div>
          <div class="brand-name">{{ t('nav.companyName') }}</div>
          <div class="brand-sub">{{ t('nav.subtitle') }}</div>
        </div>
      </div>

      <nav class="nav" aria-label="Main">
        <div class="nav-label">{{ t('nav.groupOperations') }}</div>
        <router-link to="/">
          <svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="2" width="5" height="5" rx="1" /><rect x="9" y="2" width="5" height="5" rx="1" /><rect x="2" y="9" width="5" height="5" rx="1" /><rect x="9" y="9" width="5" height="5" rx="1" /></svg>
          {{ t('nav.overview') }}
        </router-link>
        <router-link to="/inventory">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 5l6-3 6 3v6l-6 3-6-3z" /><path d="M2 5l6 3 6-3M8 8v6" /></svg>
          {{ t('nav.inventory') }}
        </router-link>
        <router-link to="/orders">
          <svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="2" width="10" height="12" rx="1" /><path d="M6 5h4M6 8h4M6 11h2" /></svg>
          {{ t('nav.orders') }}
        </router-link>
        <router-link to="/backlog">
          <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" /><path d="M8 4.5V8l2.5 1.5" /></svg>
          {{ t('nav.backlog') }}
        </router-link>
        <router-link to="/spending">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 13h12M4 10v3M8 6v7M12 3v10" /></svg>
          {{ t('nav.finance') }}
        </router-link>
        <div class="nav-label">{{ t('nav.groupPlanning') }}</div>
        <router-link to="/demand">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 12l4-4 3 2 5-6" /><path d="M10 4h4v4" /></svg>
          {{ t('nav.demandForecast') }}
        </router-link>
        <router-link to="/restocking">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8a6 6 0 0 1 10.5-4M14 8a6 6 0 0 1-10.5 4" /><path d="M12.5 1.5V4H10M3.5 14.5V12H6" /></svg>
          {{ t('nav.restocking') }}
        </router-link>
        <router-link to="/reports">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2h5l3 3v9H4z" /><path d="M9 2v3h3M6 9h4M6 11.5h4" /></svg>
          {{ t('nav.reports') }}
        </router-link>
      </nav>

      <div class="side-foot">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="main">
      <div class="topbar">
        <div class="crumbs">
          {{ crumb.group }} / <b>{{ crumb.page }}</b>
        </div>
        <FilterBar v-if="$route.path !== '/restocking'" />
      </div>
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()

    const crumbs = {
      '/': ['groupOperations', 'overview'],
      '/inventory': ['groupOperations', 'inventory'],
      '/orders': ['groupOperations', 'orders'],
      '/backlog': ['groupOperations', 'backlog'],
      '/spending': ['groupOperations', 'finance'],
      '/demand': ['groupPlanning', 'demandForecast'],
      '/restocking': ['groupPlanning', 'restocking'],
      '/reports': ['groupPlanning', 'reports']
    }
    const crumb = computed(() => {
      const [group, page] = crumbs[route.path] || [null, null]
      return {
        group: group ? t(`nav.${group}`) : '',
        page: page ? t(`nav.${page}`) : ''
      }
    })
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      crumb,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>
