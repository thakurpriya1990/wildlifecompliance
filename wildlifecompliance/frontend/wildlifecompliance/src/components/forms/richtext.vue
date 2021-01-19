<template lang="html">
    <div class="top-buffer bottom-buffer">
            <label :id="id" for="label" class="inline" >{{ label }}</label>
            <template v-if="help_text">
                <HelpText :help_text="help_text" />
            </template>

            <template v-if="help_text_url">
                <HelpTextUrl :help_text_url="help_text_url" />
            </template>

            <CommentBlock 
                :label="label"
                :name="name"
                :field_data="field_data"
                />

                <!--<input :readonly="readonly" :type="type" class="form-control" :name="name" v-model="value" :required="isRequired" />-->
                <!--
		<ckeditor v-model="value" :config="editorConfig" :readonly="readonly" class="form-control" :name="name" :required="isRequired" ></ckeditor>
                <textarea :readonly="readonly" class="form-control" rows="5" :name="name" :required="isRequired" v-model="value"></textarea><br/>
                -->
		<ckeditor v-model="field_data.value" :config="editorConfig" :read-only="readonly" :name="name" :required="isRequired" ></ckeditor>
    </div>
</template>

<script>
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapActions } from 'vuex';

export default {
    props:["type","name","id", "field_data","isRequired","help_text","label","readonly", "help_text_url"],
    components: {CommentBlock, HelpText, HelpTextUrl},
    data(){
        let vm = this;
        return {
            editorConfig: {
                // The configuration of the editor.
                removeButtons: 'Source,About' 
            },
        }
    },
    methods: {
        ...mapActions([
            'setFormValue',
        ]),
    },
    computed: {
    }
}
</script>

<style lang="css">
    .collapse-link-top,.collapse-link-bottom{
        cursor:pointer;
    }
</style>
