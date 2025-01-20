import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue'
import ElementPlus from 'element-plus';
import DataManager from './components/manager/DataManager.vue'; 
import ViewMarkdown from './components/manager/ViewMarkdown.vue';
import ChatManager from './components/chat/ChatManager.vue';
import SupportTools from './components/assistive/AssistiveMain.vue';
import SettingMain from './components/settings/SettingMain.vue';
import LoginView from './components/user/LoginView.vue';
import SetPassword from './components/user/SetPassword.vue';
import RegisterUser from './components/user/RegisterUser.vue';
import TranslateMain from './components/translate/TranslateMain.vue';
import WordManager from './components/translate/WordManager.vue';
import ArticleManager from './components/translate/ArticleManager.vue';
import BMManagerMain from './components/bmkeeper/BMManagerMain.vue';
import 'element-plus/theme-chalk/index.css';
import '@fortawesome/fontawesome-free/css/all.min.css';
import { createI18n } from 'vue-i18n'; 
import enMessages from '../_locales/en/messages.json';
import zhCNMessages from '../_locales/zh_CN/messages.json';
import config from './components/support/config';
import './assets/styles/common.css'

const messages = {
  en: enMessages,
  zh_CN: zhCNMessages
};

const i18n = createI18n({
  legacy: false, // set to false to support Composition API
  locale: getLocale(),
  messages,
});

export function getLocale() {
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
    { path: '/view_markdown', component: ViewMarkdown },
    { path: '/chat', component: ChatManager },
    { path: '/support_tools', component: SupportTools },
    { path: '/login', component: LoginView },
    { path: '/user_setting', component: SettingMain },
    { path: '/set_password', component: SetPassword },
    { path: '/register', component: RegisterUser},
    { path: '/translate', component: TranslateMain},
    { path: '/word_manager', component: WordManager},
    { path: '/article_manager', component: ArticleManager},
    { path: '/bm_manager', component: BMManagerMain}
  ]
});

router.beforeEach((to, from, next) => {
  if (localStorage.getItem('token') === null) {
    if (to.path !== '/login' && to.path !== '/set_password' && to.path !== '/register') {
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
app.use(i18n);
app.component('DataManager', DataManager);
app.component('ViewMarkdown', ViewMarkdown);
app.component('ChatManager', ChatManager);
app.component('SupportTools', SupportTools);
app.component('LoginView', LoginView);
app.component('SetPassword', SetPassword);
app.component('RegisterUser', RegisterUser);
app.component('MainSetting', SettingMain);
app.component('TranslateMain', TranslateMain);
app.component('WordManager', WordManager);
app.component('ArticleManager', ArticleManager);
app.component('BMManager', BMManagerMain);
app.use(ElementPlus);
app.use(router);
app.mount('#app');

export default router;
export { i18n };
