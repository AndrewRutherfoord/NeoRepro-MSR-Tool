<template>
    <v-navigation-drawer expand-on-hover rail>
        <!-- <v-list>
            <v-list-item prepend-avatar="https://randomuser.me/api/portraits/women/85.jpg"
                subtitle="sandra_a88@gmailcom" title="Sandra Adams"></v-list-item>
        </v-list> -->


        <v-list density="compact" nav>
            <v-list-item v-for="route in routes" :key="route.routeName" :prepend-icon="route.icon" :title="route.label"
                :to="{ name: route.routeName }"></v-list-item>
        </v-list>
        <v-divider></v-divider>
        <template v-slot:append>
            <v-list density="compact" nav>
                <!-- <v-list-item title="Notifications" prepend-icon="mdi-message" :to="{ name: 'notifications' }">
                    <template v-slot:prepend>
                        <v-badge color="error" content="6"><v-icon>mdi-message</v-icon></v-badge>
                    </template>
                </v-list-item> -->
                <v-list-item title="Toggle Theme" prepend-icon="mdi-theme-light-dark"
                    @click="toggleTheme"></v-list-item>
            </v-list>
        </template>
    </v-navigation-drawer>
</template>

<script lang="ts" setup>
import { useTheme } from 'vuetify'

const routes = [
    {
        label: "Home",
        icon: "mdi-home",
        routeName: "home"
    },
    {
        label: "Editor",
        icon: "mdi-code-braces",
        routeName: "editor"
    },
    {
        label: "Manage DB",
        icon: "mdi-database",
        routeName: "manage-database"
    },
    {
        label: "Query Neo4j",
        icon: "mdi-database-search",
        routeName: "query"
    },
    {
        label: "Jobs",
        icon: "mdi-clipboard-list-outline",
        routeName: "jobs-list"
    },
]


const theme = useTheme()

function toggleTheme() {
    theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

function showNotifications() {
    console.log("show notifications")
}

</script>