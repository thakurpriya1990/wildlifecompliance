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

            <CommentBlock :label="label" :name="name" :field_data="field_data" />

	    <ckeditor v-model="field_data.value" :config="editorConfig" :read-only="readonly" :name="name" :required="isRequired" ></ckeditor>
        </div>
    </div>
</template>

<script>
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapActions } from 'vuex';

export default {
    props:["type","name","id", "field_data","isRequired","help_text","label","readonly", "help_text_url", "can_view_richtext_src"],
    components: {CommentBlock, HelpText, HelpTextUrl},
    data(){
        let vm = this;
        if (vm.can_view_richtext_src) {
            var remove_buttons = ''
	} else {
            var remove_buttons = 'Source,About'
	}

        return {
            editorConfig: {
                // The configuration of the editor.
                removeButtons: remove_buttons,

		// below line removes toolbar 
                //toolbar: [],

                // remove bottom bar
                removePlugins: 'elementspath',
                resize_enabled: false, 
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
</style>
