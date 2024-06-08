import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import { install as VueMonacoEditorPlugin } from '@guolao/vue-monaco-editor'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'bootstrap-icons/font/bootstrap-icons.css'
// import "bootstrap-icons"

import axios from 'axios'

axios.defaults.baseURL = 'http://127.0.0.1:8000/'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueMonacoEditorPlugin, {
  paths: {
    // The recommended CDN config
    vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.43.0/min/vs'
  }
})
app.mount('#app')
