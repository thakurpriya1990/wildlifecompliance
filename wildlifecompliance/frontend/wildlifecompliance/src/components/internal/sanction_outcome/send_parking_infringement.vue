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
    name: "SendParkingInfringement",
    data: function() {
        return {
            processingDetails: false,
            isModalOpen: false,
            errorResponse: '',

            allocatedGroup: [],
            allocated_group_id: null,
            details: '',
        }
    },
    components: {
      modal,
    },
    computed: {
        ...mapGetters('sanctionOutcomeStore', {
            sanction_outcome: "sanction_outcome",
        }),
        modalTitle: function() {
            return 'Send Parking Infringement'
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
    methods: {
        ...mapActions({
            loadAllocatedGroup: 'loadAllocatedGroup',  // defined in store/modules/user.js
        }),
        addEventListeners: function () {

        },
        ok: async function () {
            try {
                this.processingDetails = true;
                const response = await this.sendData();
                this.close();
                this.$router.push({ name: 'internal-sanction-outcome-dash' });
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
            let post_url = '/api/sanction_outcome/' + this.sanction_outcome.id + '/send_parking_infringement/'
            let payload = new FormData();
            payload.append('details', this.details);
            let res = await Vue.http.post(post_url, payload);
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


