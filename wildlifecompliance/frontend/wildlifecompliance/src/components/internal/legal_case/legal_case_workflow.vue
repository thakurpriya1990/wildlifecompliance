<template lang="html">
    <div id="LegalCaseWorkflow">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
          <div class="container-fluid">
            <div v-if="workflow_type==='brief_of_evidence'" class="row">
                <strong>Are you sure you want to generate the Brief of Evidence?
                    <br>( This will make the Case read-only and no further changes can be made)
                </strong>
            </div>
            <div v-else-if="workflow_type==='prosecution_brief'" class="row">
                <strong>Are you sure you want to generate the Prosecution Brief?
                </strong>
            </div>
            <div v-else-if="workflow_type==='back_to_case'" class="row">
                <strong>Are you sure you want to re-open the Case?
                </strong>
            </div>
            <div v-else class="row">
                <div v-if="workflow_type==='approve_brief_of_evidence'" class="form-group">
                      <div class="row">
                          <div class="col-sm-9">
                              <strong>
                                  This will forward the Case for possible legal action
                              </strong>
                          </div>
                      </div>
                </div>
                <div class="col-sm-12">
                        <div class="form-group">
                          <div class="row">
                              <div class="col-sm-3">
                                  <label class="control-label pull-left" for="details">Details</label>
                              </div>
            			      <div class="col-sm-6">
                                  <textarea class="form-control" placeholder="add details" id="details" v-model="workflowDetails"/>
                              </div>
                          </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label pull-left"  for="Name">Attachments</label>
                                </div>
            			        <div class="col-sm-9">
                                    <filefield ref="comms_log_file" name="comms-log-file" :isRepeatable="true" :documentActionUrl="legal_case.commsLogsDocumentUrl"/>
                                </div>
                            </div>
                        </div>
                </div>
            </div>

          </div>
            <div slot="footer">
                <div v-if="errorResponse" class="form-group">
                    <div class="row">
                        <div class="col-sm-12">
                            <strong>Error: {{ errorResponse }}</strong>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-default" @click="ok">Ok</button>
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

export default {
    name: "LegalCaseWorking",
    data: function() {
      return {
            officers: [],
            isModalOpen: false,
            processingDetails: false,
            form: null,
            workflowDetails: '',
            errorResponse: "",
            documentActionUrl: '',
            //allocatedGroup: [],
            allocated_group_id: null,
            saveAndExit: false,
            modalTitle: '',
      }
    },
    components: {
      modal,
      filefield,
    },
    props:{
          workflow_type: {
              type: String,
              default: '',
          },
    },
    computed: {
      ...mapGetters('legalCaseStore', {
        legal_case: "legal_case",
      }),
        /*
      modalTitle: function() {
          if (this.workflow_type === 'close') {
              return "Close Legal Case";
          } else if (this.workflow_type === 'brief_of_evidence') {
              return "Generate the Brief of Evidence";
          } else if (this.workflow_type === 'prosecution_brief') {
              return "Generate the Prosecution Brief";
          } else if (this.workflow_type === 'send_to_manager') {
              return "Send to Manager for approval";
          } else if (this.workflow_type === 'back_to_case') {
              return "Re-open the Case";
          } else if (this.workflow_type === 'back_to_officer') {
              return "Return to Officer";
          } else if (this.workflow_type === 'approve_brief_of_evidence') {
              return "Approve the Brief of Evidence";
          } else if (this.workflow_type === 'send_to_prosecution_council') {
              return "Send To Prosecution Council";
          } else if (this.workflow_type === 'back_to_prosecution_coordinator') {
              return "Back to Prosecution Coordinator";
          } else if (this.workflow_type === 'endorse_prosecution_brief') {
              return "Endorse Prosecution Brief";
          } else if (this.workflow_type === 'approve_for_court') {
              return "Approve for Court";
          } else if (this.workflow_type === 'back_to_prosecution_council') {
              return "Back to Prosecution Council";
          }
      },
      */
    },
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
      ...mapActions('legalCaseStore', {
          saveLegalCase: 'saveLegalCase',
          loadLegalCase: 'loadLegalCase',
          setLegalCase: 'setLegalCase',
      }),
      ok: async function () {
          const response = await this.sendData();
          console.log(response);
          if (response.ok) {
              this.close();
              if (this.saveAndExit) {
                  this.$router.push({ name: 'internal-legal-case-dash' });
              } else {
                  this.$router.go();
                  //window.location.reload(true);
              }
          }
      },
      cancel: async function() {
          if (this.$refs.comms_log_file) {
              await this.$refs.comms_log_file.cancel();
          }
          this.isModalOpen = false;
          this.close();
      },
      close: function () {
          let vm = this;
          this.isModalOpen = false;
      },
      sendData: async function() {
          let post_url = '/api/legal_case/' + this.legal_case.id + '/workflow_action/'
          
          let payload = new FormData();
          payload.append('details', this.workflowDetails);
          if (this.$refs.comms_log) {
              this.$refs.comms_log_file.commsLogId ? payload.append('legal_case_comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
          }
          this.workflow_type ? payload.append('workflow_type', this.workflow_type) : null;
          if (this.$parent) {
              await this.$parent.save({internalFlag: true})
          }
          // save workflow modal
          try {
              let res = await Vue.http.post(post_url, payload);
              console.log(res);
              if (res.ok) {
                  return res
              }
          } catch(err) {
              this.errorResponse = err.statusText;
          }

      },
    },
    mounted: async function() {
        this.$nextTick(() => {
        });
    },
    created: function() {
        if (this.workflow_type === 'close') {
            this.modalTitle = "Close Legal Case";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'brief_of_evidence') {
            this.modalTitle = "Generate the Brief of Evidence";
        } else if (this.workflow_type === 'prosecution_brief') {
            this.modalTitle = "Generate the Prosecution Brief";
        } else if (this.workflow_type === 'send_to_manager') {
            this.modalTitle = "Send to Manager for approval";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'back_to_case') {
            this.modalTitle = "Re-open the Case";
        } else if (this.workflow_type === 'back_to_officer') {
            this.modalTitle = "Return to Officer";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'approve_brief_of_evidence') {
            this.modalTitle = "Approve the Brief of Evidence";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'send_to_prosecution_council') {
            this.modalTitle = "Send To Prosecution Council";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'back_to_prosecution_coordinator') {
            this.modalTitle = "Back to Prosecution Coordinator";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'endorse_prosecution_brief') {
            this.modalTitle = "Endorse Prosecution Brief";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'approve_for_court') {
            this.modalTitle = "Approve for Court";
            this.saveAndExit = true;
        } else if (this.workflow_type === 'back_to_prosecution_council') {
            this.modalTitle = "Back to Prosecution Council";
            this.saveAndExit = true;
        }
    }
};
</script>

<style lang="css">
.btn-file {
    position: relative;
    overflow: hidden;
}
.btn-file input[type=file] {
    position: absolute;
    top: 0;
    right: 0;
    min-width: 100%;
    min-height: 100%;
    font-size: 100px;
    text-align: right;
    filter: alpha(opacity=0);
    opacity: 0;
    outline: none;
    background: white;
    cursor: inherit;
    display: block;
}
.top-buffer{margin-top: 5px;}
.top-buffer-2x{margin-top: 10px;}
</style>
