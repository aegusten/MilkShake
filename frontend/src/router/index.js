import { createRouter, createWebHistory } from 'vue-router';
import OrderPage from '../views/OrderPage.vue';
import AdminPage from '../views/AdminPage.vue';

const routes = [
  { path: '/order', component: OrderPage },
  { path: '/admin', component: AdminPage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
