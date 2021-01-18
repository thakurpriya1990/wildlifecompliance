<template lang="html">
    <div>
        <div class="form-group">
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
		<ckeditor v-model="value" :config="editorConfig" :readonly="readonly" class="form-control" :name="name" :required="isRequired" ></ckeditor>
        </div>
    </div>
</template>

<script>
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapActions } from 'vuex';

import Vue from 'vue';
Vue.use( CKEditor  );

export default {
    props:["type","name","id", "field_data","isRequired","help_text","label","readonly", "help_text_url"],
    components: {CommentBlock, HelpText, HelpTextUrl},
    data(){
        let vm = this;
        return {
            //editorData: '<p>Content of the editor.</p>',
            editorConfig: {
                // The configuration of the editor.
                toolbar: [
                    [ '-', 'Bold', 'Italic' ],
                    [ 'Format' ],
                    [ 'NumberedList', 'BulletedList' ],
                    [ 'Table' ],
                ],
                format_tags: 'p;h1;h2;h3;h4;h5;h6;div',
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
    input {
        box-shadow:none;
    }
</style>
