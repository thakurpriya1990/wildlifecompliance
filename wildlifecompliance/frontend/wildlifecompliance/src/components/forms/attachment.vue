<template lang="html">
    <div>
        <label :id="id" for="label" class="inline">{{ label }}</label>
        <template v-if="help_text">
            <HelpText :help_text="help_text" />
        </template>

        <template v-if="help_text_url">
            <HelpTextUrl :help_text_url="help_text_url" />
        </template>

        <table>
            <tr v-for="(f,i) in attachments">
                <td :class="'row-'+i">
                    <input type="file" :name="'file-upload-'+i" :data-que="i" :accept="fileTypes" @change="uploadFile" :required="isRequired"/>                    
                </td>
                <td><a title="Remove file" @click="removeAttachment(i)" class="fa fa-trash-o" style="cursor: pointer; color:red;" /></td>

            <span v-if="show_spinner"><i class='fa fa-2x fa-spinner fa-spin'></i></span>    
            </tr>       
        </table>

    </div>
</template>

<script>
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks';
import HelpText from './help_text.vue';
import { mapGetters } from 'vuex';
export default {
    props:{
        application_id: null,
        name:String,
        label:String,
        id:String,
        isRequired:String,
        help_text:String,
        field_data:Object,
        attachments: Array,
        fileTypes:{
            default:function () {
                var file_types = 
                    "image/*," + 
                    "video/*," +
                    "audio/*," +
                    "application/pdf,text/csv,application/msword,application/vnd.ms-excel,application/x-msaccess," +
                    "application/x-7z-compressed,application/x-bzip,application/x-bzip2,application/zip," + 
                    ".dbf,.gdb,.gpx,.prj,.shp,.shx," + 
                    ".json,.kml,.gpx";
                return file_types;
            }
        },
        isRepeatable:Boolean,
        readonly:Boolean,
        docsUrl: String,
    },
    components: {HelpText},
    data:function(){
        return {
            repeat:1,
            show_spinner: false,
            filename:null,
            help_text_url:'',
        }
    },
    computed: {
        csrf_token: function() {
            return helpers.getCookie('csrftoken')
        },
    },

    methods:{
        uploadFile: function (e){
            console.log('upload without')
            let vm = this;
            vm.show_spinner = true;
            let _file = null;

            if (e.target.files && e.target.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(e.target.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = e.target.files[0];
            }
            this.attachments.push(_file)
            vm.show_spinner = false;
            return _file
        },

        removeAttachment(index){
            console.log('removeFile')
            let length = this.attachments.length;
            $('.file-row-'+index).remove();
            this.attachments.splice(index,1);
            this.$nextTick(() => {
                length == 1 ? this.attachAnother() : '';
            });
        },
        attachAnother(){
            console.log('attachAnother')
            this.attachments.push({
                'file': null,
                'name': ''
            })
        },
    },
    mounted:function () {
        let vm = this;
    }
}

</script>

<style lang="css">
    input {
        box-shadow:none;
    }
</style>
