<template>
    <div v-if="isReturnsLoaded">
        <div v-if="visibleRequests.length" class="row" style="color:red;">
            <div class="col-lg-12 pull-right">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title" style="color:red;">An amendment has been requested for this Return
                            <a class="panelClicker" :href="'#'+returnsAmendBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="returnsAmendBody">
                                <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                            </a>
                        </h3>
                    </div>
                    <div class="panel-body panel-collapse collapse in" :id="returnsAmendBody">
                        <div v-for="(a, a_idx) in visibleRequests" v-bind:key="`ret_amend_${a_idx}`">
                            <p v-if="a.text"><b>Details:</b>
                                <div v-for="(t, t_idx) in splitText(a.text)" v-bind:key="`ret_text_${t_idx}`">{{t}}<br></div>
                            <p/> 
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>


<script>
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex'
import { splitText } from "@/utils/helpers.js";

export default {
  name:'returns-amendment-details',
  data: function() {
    let vm = this;
    return {
        returnsAmendBody: 'returnsAmendBody'+vm._uid,
    }
  },
  props:{
  },
  computed: {
    ...mapGetters([
        'isReturnsLoaded',
        'returns',
    ]),
    isVisible: function() {
        return true;
    },
    visibleRequests: function() {
        return this.returns.amendment_requests;
    }
  },
  methods: {
    splitText: splitText
  },
}
</script>
