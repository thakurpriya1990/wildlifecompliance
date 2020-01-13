<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row col-sm-12">

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left">Reason</label>
                        </div>
                        <div class="col-sm-7">
                            <select v-if="amendment_request_reasons" class="form-control" v-model="amendment_request_reason">
                                <option v-for="item in amendment_request_reasons" :value="item.reason" :key="item.id">
                                    {{ item.reason }}
                                </option>
                            </select>
                        </div>
                    </div></div>

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left">Details</label>
                        </div>
                        <div class="col-sm-7">
                            <textarea class="form-control" placeholder="add reason" id="reason" v-model="details"/>
                        </div>
                    </div></div>

                </div>

            </div>
            <div slot="footer">
                <div v-if="errorResponse" class="form-group">
                    <div class="row">
                        <div class="col-sm-12">
                            <strong>
                                <span style="white-space: pre;" v-html="errorResponse"></span>
                            </strong>
                        </div>
                    </div>
                </div>
                <button type="button" v-if="processingDetails" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else-if="fieldsFilled" class="btn btn-default" @click="ok">Ok</button>
                <button type="button" v-else disabled class="btn btn-default">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
import Vue from "vue";
import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    name: "AmendmentRequestRemediationAction",
    data: function() {
        return {
            processingDetails: false,
            isModalOpen: false,
            errorResponse: '',
            amendment_request_reason: '',
            amendment_request_reasons: [],
            details: '',
        }
    },
    components: {
      modal,
    },
    props:{
        remediation_action_id: {
            type: Number,
            default: 0,
        },
    },
    computed: {
       // ...mapGetters('sanctionOutcomeStore', {
       //     sanction_outcome: "sanction_outcome",
       // }),
        modalTitle: function() {
            return 'Request Amendment'
        },
        fieldsFilled: function() {
            let filled = true;

            return filled;
        }
    },
    mounted: function () {
        this.$nextTick(() => {
            this.addEventListeners();
        });
    },
    created: async function() {
        this.constructOptionsReasons();
    },
    methods: {
        ...mapActions({
            loadAllocatedGroup: 'loadAllocatedGroup',  // defined in store/modules/user.js
        }),
        addEventListeners: function () {

        },
        constructOptionsReasons: async function() {
            let get_url = '/api/sanction_outcome/reasons/'
            let res = await Vue.http.get(get_url, {});
            console.log('res.body');
            console.log(res.body);
            this.amendment_request_reasons = res.body;
        },
        ok: async function () {
            try {
                console.log('ok');
                this.processingDetails = true;
                const res = await this.sendData();
                this.$emit('remediation_action_updated', res.body);
                this.close();
            } catch (err){
                this.processError(err);
            } finally {
                this.processingDetails = false;
            }
        },
        processError: async function(err) {
            let errorText = '';
            if (err.body.non_field_errors) {
                // When non field errors raised
                for (let i=0; i<err.body.non_field_errors.length; i++){
                    errorText += err.body.non_field_errors[i] + '<br />';
                }
            } else if(Array.isArray(err.body)) {
                // When general errors raised
                for (let i=0; i<err.body.length; i++){
                    errorText += err.body[i] + '<br />';
                }
            } else {
                // When field errors raised
                for (let field_name in err.body){
                    if (err.body.hasOwnProperty(field_name)){
                        errorText += field_name + ': ';
                        for (let j=0; j<err.body[field_name].length; j++){
                            errorText += err.body[field_name][j] + '<br />';
                        }
                    }
                }
            }
            this.errorResponse = errorText;
        },
        cancel: async function() {
            this.isModalOpen = false;
            this.close();
        },
        close: function () {
            let vm = this;
            this.isModalOpen = false;
        },
        sendData: async function () {
            console.log('sendData');
            let get_url = '/api/remediation_action/' + this.remediation_action_id + '/request_amendment/'
            let payload = {
                'reason': this.amendment_request_reason,
                'details': this.details,
                'remediation_action_id': this.remediation_action_id
            }
            console.log(payload);
            let res = await Vue.http.post(get_url, payload);
            return res
        },
    },
}
</script>

<style>
.case_number_1 {
    width: 3em;
    text-align: center;
    display: inline-block;
}
.case_number_2 {
    width: 8em;
    text-align: center;
    display: inline-block;
}
</style>


