import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue'
import ElementPlus from 'element-plus';
import DataManager from './components/DataManager.vue'; 
import SupportTools from './components/SupportTools.vue';
import UserSetting from './components/UserSetting.vue';
import LoginView from './components/LoginView.vue';
import SetPassword from './components/SetPassword.vue';
import RegisterUser from './components/RegisterUser.vue';
import EnReader from './components/translate/EnReader.vue';
import WordManager from './components/translate/WordManager.vue';
import ArticleManager from './components/translate/ArticleManager.vue';
import 'element-plus/theme-chalk/index.css';
import '@fortawesome/fontawesome-free/css/all.min.css';
import { createI18n } from 'vue-i18n'; 
import enMessages from '../_locales/en/messages.json';
import zhCNMessages from '../_locales/zh_CN/messages.json';
import config from './components/config';

const messages = {
  en: enMessages,
  zh_CN: zhCNMessages
};

const i18n = createI18n({
  locale: getLocale(),
  messages,
});

function getLocale() {
  const locale = config.langCode || 'en';
  if (locale.includes('zh')) {
    return 'zh_CN';
  }
  return locale;
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DataManager },
    { path: '/data', component: DataManager },
    { path: '/support_tools', component: SupportTools },
    { path: '/login', component: LoginView },
    { path: '/user_setting', component: UserSetting },
    { path: '/set_password', component: SetPassword },
    { path: '/register', component: RegisterUser},
    { path: '/enreader', component: EnReader},
    { path: '/word_manager', component: WordManager},
    { path: '/article_manager', component: ArticleManager}
  ]
});

router.beforeEach((to, from, next) => {
  if (localStorage.getItem('token') === null) {
    if (to.path !== '/login' && to.path !== '/set_password') {
      next({
        path: '/login',
        query: to.query
      })      
    } else {
      next()
    }
  } else {
    next()
  }
})

const app = createApp(App);
app.use(i18n); // 使用 i18n
app.component('DataManager', DataManager);
app.component('SupportTools', SupportTools);
app.component('LoginView', LoginView);
app.component('SetPassword', SetPassword);
app.component('RegisterUser', RegisterUser);
app.component('UserSetting', UserSetting);
app.component('EnReader', EnReader);
app.component('WordManager', WordManager);
app.component('ArticleManager', ArticleManager);
app.use(ElementPlus);
app.use(router);
app.mount('#app');
