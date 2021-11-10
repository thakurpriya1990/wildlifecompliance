<!--
Common form component to display an anchored link with a secure redirect to open a new window.
-->
<template lang="html">
    <div><span><a href="#" @click.prevent="post_and_redirect()">{{ link_name }}</a></span></div>
</template>
<script>
import {
  helpers
}
from '@/utils/hooks';
export default {
    name: "securebase-link",
    props:{
        link_data: {
            type: Object,
            required: true
        },
        link_name: {
            type: String,
            required: true
        },
    },
    data:function(){
        return {
        }
    },
    computed: {
        csrf_token: function() {
            return helpers.getCookie('csrftoken')
        },
    },
    methods:{
        post_and_redirect: function() {
            // post to securebase.
            var postFormStr = "<form method='POST' target='_blank' name='securebase-view' action='/securebase-view/'>";
            postFormStr += "<input type='hidden' name='csrfmiddlewaretoken' value='" + this.csrf_token + "'>";
            let link_data_key = Object.keys(this.link_data)[0];
            postFormStr += "<input type='hidden' name='" + link_data_key + "' value='" + this.link_data[link_data_key] + "'>";
            postFormStr += "</form>";
            var formElement = $(postFormStr);
            $('body').append(formElement);
            $(formElement).submit();
        },
    },
}

</script>

<style lang="css">
    input {
        box-shadow:none;
    }
</style>