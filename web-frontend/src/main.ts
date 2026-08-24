import { createApp } from "vue"

import App from "./App.vue"
import ErrorNotice from "./components/ErrorNotice.vue"
import "./styles/base.css"

createApp(App).component("ErrorNotice", ErrorNotice).mount("#app")
