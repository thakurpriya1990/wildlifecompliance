<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row col-sm-12">

                    <div class="form-group"><div class="row">
                        <label class="col-sm-3">New due date</label>
                        <div class="col-sm-3">
                            <div class="input-group date" ref="newDueDatePicker">
                                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="new_due_date" />
                                <span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>
                            </div>
                        </div>
                        current due date: {{ comingDueDateDisplay }} <br />
                        (New due: {{ extendMinDateDisplay }} --- {{ extendMaxDateDisplay }})
                    </div></div>

                    <div class="form-group"><div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left">Reason</label>
                        </div>
                        <div class="col-sm-7">
                            <textarea class="form-control" placeholder="add reason" id="reason" v-model="reasonForExtension"/>
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
                <button type="button" v-else class="btn btn-default" @click="ok">Ok</button>
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
import filefield from '@/components/common/compliance_file.vue';
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    name: "ExtendPaymentDueDate",
    data: function() {
        return {
            processingDetails: false,
            isModalOpen: false,
            files: [
                    {
                        'file': null,
                        'name': ''
                    }
            ],
            reasonForExtension: '',
            errorResponse: '',

            allocatedGroup: [],
            allocated_group_id: null,

            new_due_date: null,
        }
    },
    components: {
      modal,
      filefield,
    },
    props:{
        due_date_1st: {
            type: String,
            default: '',
        },
        due_date_2nd: {
            type: String,
            default: '',
        },
        due_date_max: {
            type: String,
            default: '',
        },
    },
    computed: {
        ...mapGetters('sanctionOutcomeStore', {
            sanction_outcome: "sanction_outcome",
        }),
        modalTitle: function() {
            return 'Extend payment due date'
        },
        extendMinDateDisplay: function() {
            if (this.comingDueDate){
                let newDate = new Date()
                newDate.setDate(this.comingDueDate.getDate() + 1)
                return (newDate.getDate()) + '/' + (newDate.getMonth() + 1) + '/' + newDate.getFullYear()
            } else {
                return '';
            }
        },
        extendMaxDateDisplay: function() {
            if (this.extendMaxDate){
                return this.extendMaxDate.getDate() + '/' + (this.extendMaxDate.getMonth() + 1) + '/' + this.extendMaxDate.getFullYear()
            } else {
                return '';
            }
        },
        extendMaxDate: function() {
            return new Date(this.due_date_max);
        },
        comingDueDateDisplay: function() {
            if(this.comingDueDate){
                return this.comingDueDate.getDate() + '/' + (this.comingDueDate.getMonth() + 1) + '/' + this.comingDueDate.getFullYear()
            } else {
                return '';
            }
        },
        comingDueDate: function() {
            if (this.due_date_1st && this.due_date_2nd){
                let now = new Date();
                let due_1st = new Date(this.due_date_1st);
                let due_2nd = new Date(this.due_date_2nd);

                if (now <= due_1st){
                    return due_1st;
                } else if (now <= due_2nd){
                    return due_2nd;
                } else {
                    console.warn('This infringement notice is already overdue');
                    return null;  // Already overdue
                }
            } else {
                return null;
            }
        },
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
            let vm = this;
            let el_fr_date = $(vm.$refs.newDueDatePicker);
            let options = { format: "DD/MM/YYYY" };

            if (vm.due_date_max){
                options['maxDate'] = vm.extendMaxDate;
            }
            if (vm.comingDueDate){
                // Copy comingDuDate object
                let coming_due_date = new Date(vm.comingDueDate.getTime());
                // Calculate next day and set it to the datepicker as a minDate
                coming_due_date.setDate(coming_due_date.getDate() + 1);
                options['minDate'] = coming_due_date;
                // Enter a default value to the input box
                vm.new_due_date = coming_due_date.getDate() + '/' + (coming_due_date.getMonth() + 1) + '/' + coming_due_date.getFullYear();
            }

            el_fr_date.datetimepicker(options);

            el_fr_date.on("dp.change", function(e) {
                if (el_fr_date.data("DateTimePicker").date()) {
                    vm.new_due_date = e.date.format("DD/MM/YYYY");
                } else if (el_fr_date.data("date") === "") {
                    vm.new_due_date = null;
                }
            });
        },
        ok: async function () {
            try {
                this.processingDetails = true;
                const response = await this.sendData();
                this.close();
            //    this.$router.push({ name: 'internal-sanction-outcome-dash' });
                console.log(this.$parent)
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
            let file_length = vm.files.length;
            this.files = [];
            for (var i = 0; i < file_length;i++){
                vm.$nextTick(() => {
                    $('.file-row-'+i).remove();
                });
            }
            this.attachAnother();
        },
        sendData: async function () {
            let post_url = '/api/sanction_outcome/' + this.sanction_outcome.id + '/extend_due_date/'
            let payload = new FormData();
            payload.append('reason', this.reasonForExtension);
            this.$refs.comms_log_file.commsLogId ? payload.append('comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
            this.new_due_date ? payload.append('new_due_date', this.new_due_date) : null;

            let res = await Vue.http.post(post_url, payload);
            return res
        },
        uploadFile(target,file_obj){
            let vm = this;
            let _file = null;
            var file_input = $('.'+target)[0];

            if (file_input.files && file_input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(file_input.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = file_input.files[0];
            }
            file_obj.file = _file;
            file_obj.name = _file.name;
        },
        removeFile(index){
            let length = this.files.length;
            $('.file-row-'+index).remove();
            this.files.splice(index,1);
            this.$nextTick(() => {
                length == 1 ? this.attachAnother() : '';
            });
        },
        attachAnother(){
            this.files.push({
                'file': null,
                'name': ''
            })
        },
    },
}
</script>

<style>

</style>


