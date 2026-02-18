<template>
  <aside class="sidebar">
    <nav>
      <ul class="menu">
        <template v-for="menu in menus" :key="menu.id">
          <li v-if="menu.is_category" class="menu-category">{{ menu.name }}</li>
          <li v-else-if="menu.path">
            <router-link :to="menu.path" class="menu-item" active-class="active">
              {{ menu.name }}
            </router-link>
          </li>
          <template v-if="menu.children && menu.children.length > 0">
            <li v-for="child in menu.children" :key="child.id">
              <router-link :to="child.path" class="menu-item" active-class="active">
                {{ child.name }}
              </router-link>
            </li>
          </template>
        </template>
      </ul>
    </nav>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const menus = ref([])

onMounted(() => fetchMenus())

async function fetchMenus() {
  try {
    const res = await api.get('/menus/tree')
    menus.value = res.data
  } catch (e) {
    console.error('Failed to fetch menus:', e)
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 60px;
  left: 0;
  bottom: 0;
  width: 220px;
  background: #2c3e50;
  padding: 10px 0;
  overflow-y: auto;
}

.menu {
  list-style: none;
}

.menu-category {
  padding: 12px 20px 8px 20px;
  color: #f59e0b;
  font-size: 14px;
  font-weight: 700;
  text-transform: none;
  letter-spacing: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: 8px;
}

.menu-item {
  display: block;
  padding: 10px 20px 10px 25px;
  color: #bdc3c7;
  text-decoration: none;
  font-size: 13px;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.menu-item.active {
  background: rgba(74, 144, 217, 0.2);
  color: white;
  border-left-color: #4a90d9;
}
</style>
