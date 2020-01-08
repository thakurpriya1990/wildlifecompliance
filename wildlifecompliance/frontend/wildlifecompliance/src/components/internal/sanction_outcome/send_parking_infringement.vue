<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row col-sm-12">

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left">Recipient</label>
                        </div>
                        <div class="col-sm-7">
                            {{ recipient_details }}
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

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left"  for="Name">Attachments</label>
                        </div>
                        <div class="col-sm-9">
                            <filefield ref="comms_log_file" name="comms-log-file" :isRepeatable="true" :documentActionUrl="sanction_outcome.commsLogsDocumentUrl" />
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
import filefield from '@/components/common/compliance_file.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import "jquery-ui/ui/widgets/draggable.js";

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
        filefield,
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
        },
        recipient_details: function() {
            let details = '';
            if (this.sanction_outcome){
                if (this.sanction_outcome.driver){
                    details = 'Driver: ' + this.sanction_outcome.driver.email;
                } else if (this.sanction_outcome.registration_holder){
                    details = 'Registration holder' + this.sanction_outcome.registration_holder.email;
                } else if (this.sanction_outcome.offender){
                    details = this.sanction_outcome.offender.person.email;
                }
            }
            return details;
        }
    },
    mounted: function () {
        this.$nextTick(() => {
            this.addEventListeners();
            this.makeModalsDraggable();
        });
    },
    methods: {
        ...mapActions({
            loadAllocatedGroup: 'loadAllocatedGroup',  // defined in store/modules/user.js
        }),
        addEventListeners: function () {

        },
        makeModalsDraggable: function(){
            this.elem_modal = $('.modal > .modal-dialog');
            for (let i=0; i<this.elem_modal.length; i++){
                $(this.elem_modal[i]).draggable();
            }
        },
        ok: async function () {
            try {
                this.processingDetails = true;
                const response = await this.sendData();
                this.close();
                this.$parent.loadSanctionOutcome({ sanction_outcome_id: this.$parent.sanction_outcome.id });
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
            await this.$refs.comms_log_file.cancel();
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
            this.$refs.comms_log_file.commsLogId ? payload.append('comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
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


