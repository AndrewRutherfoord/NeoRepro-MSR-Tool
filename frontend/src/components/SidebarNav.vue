<template>
    <div class="d-flex flex-column flex-shrink-0 p-3 bg-white">
        <!-- <a href="/" class="d-flex align-items-center pb-3 mb-3 link-dark text-decoration-none border-bottom">
            <span class="fs-5 fw-semibold">Graph MSR</span>
        </a> -->
        <ul class="navbar-nav">
            <li class="nav-item">
                <router-link :to="{ name: route.routeName }" class="nav-link active" aria-current="page"
                    v-for="route in routes" :key="route.label">
                    <i :class="route.icon"></i>
                    <span v-show="!collapsed" class="ms-3 me-2">{{ route.label }}</span>
                </router-link>
            </li>
        </ul>
        <ul class="navbar-nav mt-auto">
            <li class="nav-item">
                <button class="nav-link active" @click="toggle">
                    <span v-if="collapsed">
                        <i class="bi bi-chevron-double-right"></i>
                    </span>
                    <span v-else>
                        <i class="bi bi-chevron-double-left"></i> Collapse
                    </span>
                </button>
            </li>
        </ul>

    </div>
</template>

<script lang="ts" setup>
const collapsed = defineModel('collapsed')
const sidebarWidth = defineModel('sidebarWidth')

const MAX_WIDTH = "180px";

const routes = [
    {
        label: "Home",
        icon: "bi bi-house",
        routeName: "home"
    },
    {
        label: "Editor",
        icon: "bi bi-pencil-square",
        routeName: "editor"
    },
    {
        label: "Jobs",
        icon: "bi bi-clipboard-data",
        routeName: "jobs-list"
    },
]

function toggle() {
    collapsed.value = !collapsed.value;
    sidebarWidth.value = !collapsed.value ? "0px" : MAX_WIDTH
}

</script>