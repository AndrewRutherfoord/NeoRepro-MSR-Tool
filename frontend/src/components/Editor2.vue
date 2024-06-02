<template>
    <div id="editor" style="height: 300px;"></div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { Uri, editor } from 'monaco-editor/esm/vs/editor/editor.api';
import { configureMonacoYaml } from 'monaco-yaml'
import loader from "@monaco-editor/loader";

const modelUri = Uri.parse('a://b/foo.yaml');

configureMonacoYaml(monaco, {
    enableSchemaRequest: true,
    schemas: [
        {
            // If YAML file is opened matching this glob
            fileMatch: ['**/.prettierrc.*'],
            // Then this schema will be downloaded from the internet and used.
            uri: 'https://json.schemastore.org/prettierrc.json'
        },
        {
            // If YAML file is opened matching this glob
            fileMatch: ['**/person.yaml'],
            // The following schema will be applied
            schema: {
                type: 'object',
                properties: {
                    name: {
                        type: 'string',
                        description: 'The person’s display name'
                    },
                    age: {
                        type: 'integer',
                        description: 'How old is the person in years?'
                    },
                    occupation: {
                        enum: ['Delivery person', 'Software engineer', 'Astronaut']
                    }
                }
            },
            // And the URI will be linked to as the source.
            uri: 'https://github.com/remcohaszing/monaco-yaml#usage'
        }
    ]
})

const defaultValue = 'p1: \n';

let monacoEditor;
export default defineComponent({
    name: 'MonacoEditor',
    props: {
        modelValue: {
            type: String,
            require: false,
            default: defaultValue, // 此处只是为了演示提供默认值，使用的时候要改成需要的值
        },
        schemas: {
            require: false,
            default: defaultSchemas, // 此处只是为了演示提供默认值，使用的时候要改成需要的值
        },
    },
    emits: ['change'],
    watch: {
        modelValue(value) {
            if (monacoEditor) {
                monacoEditor.setValue(value);
            }
        },
    },
    created() {
        if (this.schemas) {
            setDiagnosticsOptions({
                enableSchemaRequest: true,
                hover: true,
                completion: true,
                validate: true,
                format: true,
                schemas: defaultSchemas,
            });
        }
    },
    mounted() {
        loader.init().then((monaco) => {
            monaco.editor.create(document.getElementById('editor'){
                language: 'yaml',
                model: editor.createModel(defaultValue, 'yaml', modelUri),
            });
        })
        monacoEditor = editor.create(document.getElementById('editor'), {
            // Monaco-yaml features should just work if the editor language is set to 'yaml'.
            language: 'yaml',
            model: editor.createModel(defaultValue, 'yaml', modelUri),
        });
        monacoEditor.onDidChangeModelContent(() => {
            this.$emit('change', monacoEditor.getValue());
        });
    },
    beforeUnmount() {
        monacoEditor.dispose();
    },
});
</script>