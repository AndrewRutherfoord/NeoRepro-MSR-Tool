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
                <v-list-item title="Toggle Theme" prepend-icon="mdi-theme-light-dark" @click="toggleTheme"></v-list-item>
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
        label: "Jobs",
        icon: "mdi-clipboard-list-outline",
        routeName: "jobs-list"
    },
]


const theme = useTheme()

function toggleTheme() {
    theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

</script>