<template lang="html">
    <div id="LegalCaseWorkflow">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
          <div class="container-fluid">
            <div class="row">
                <label class="col-sm-10">
                <input type="checkbox" v-model="selectAll" @change="setSelectAll" />
                Select All
                </label>
                <label class="col-sm-10">
                <input type="checkbox" v-model="includeStatementOfFacts" />
                Statement of Facts
                </label>
                <label class="col-sm-10">
                <input type="checkbox" v-model="includeCaseInformationForm" />
                Case Information Form
                </label>
                <label class="col-sm-10">
                <input type="checkbox" v-model="includeOffencesOffendersRoi" />
                Offences, Offenders and Records of Interview
                </label>
                <label class="col-sm-10">
                <input type="checkbox" v-model="includeWitnessOfficerOtherStatements" />
                Witness Statements, Officer Statements, Expert Statements
                </label>
                <label class="col-sm-10">
                <input type="checkbox" v-model="includePhysicalArtifacts" />
                List of Exhibits, Sensitive Unused and Non-Sensitive Unused Materials
                </label>
                <label class="col-sm-10">
                <input type="checkbox" v-model="includeDocumentArtifacts" />
                List of Photographic Exhibits
                </label>
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

export default {
    name: "GenerateDocument",
    data: function() {
        return {
            isModalOpen: false,
            form: null,
            errorResponse: "",
            selectAll: false,
            includeStatementOfFacts: false,
            includeCaseInformationForm: false,
            includeOffencesOffendersRoi: false,
            includeWitnessOfficerOtherStatements: false,
            includePhysicalArtifacts: false,
            includeDocumentArtifacts: false,
            payload: {},
      }
    },
    components: {
      modal,
    },
    props:{
          document_type: {
              type: String,
              default: '',
          },
    },
    computed: {
      ...mapGetters('legalCaseStore', {
        legal_case: "legal_case",
      }),
      csrf_token: function() {
        return helpers.getCookie("csrftoken");
      },
      modalTitle: function() {
          let title = '';
          if (this.document_type === 'brief_of_evidence') {
              title = "Print Brief of Evidence";
          } else if (this.document_type === 'prosecution_brief') {
              title = "Print Prosecution Brief";
          }
          return title;
      },
    },
    methods: {
      ...mapActions('legalCaseStore', {
          saveLegalCase: 'saveLegalCase',
          loadLegalCase: 'loadLegalCase',
          setLegalCase: 'setLegalCase',
      }),
      setSelectAll: function() {
          if (this.selectAll) {
              this.includeStatementOfFacts = true;
              this.includeCaseInformationForm = true;
              this.includeOffencesOffendersRoi = true;
              this.includeWitnessOfficerOtherStatements = true;
              this.includePhysicalArtifacts = true;
              this.includeDocumentArtifacts = true;
          } else {
              this.includeStatementOfFacts = false;
              this.includeCaseInformationForm = false;
              this.includeOffencesOffendersRoi = false;
              this.includeWitnessOfficerOtherStatements = false;
              this.includePhysicalArtifacts = false;
              this.includeDocumentArtifacts = false;
          }
      },
      ok: async function () {
          let res = await this.sendData();
          if (res) {
              this.close();
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
          try {
              this.payload.document_type = this.document_type;
              this.payload.legal_case_id = this.legal_case.id;
              if (this.includeStatementOfFacts) {
                  this.payload.include_statement_of_facts = this.includeStatementOfFacts;
              }
              if (this.includeCaseInformationForm) {
                  this.payload.include_case_information_form = this.includeCaseInformationForm;
              }
              if (this.includeOffencesOffendersRoi) {
                  this.payload.include_offences_offenders_roi = this.includeOffencesOffendersRoi;
              }
              if (this.includeWitnessOfficerOtherStatements) {
                  this.payload.include_witness_officer_other_statements = this.includeWitnessOfficerOtherStatements;
              }
              if (this.includePhysicalArtifacts) {
                  this.payload.include_physical_artifacts = this.includePhysicalArtifacts;
              }
              if (this.includeDocumentArtifacts) {
                  this.payload.include_document_artifacts = this.includeDocumentArtifacts;
              }
              let post_url = '/api/legal_case/' + this.legal_case.id + '/generate_document/'
              const res = await fetch(
                  post_url, 
                  {
                      method: 'POST', 
                      body: JSON.stringify(this.payload),
                      headers: {
                          'Content-Type': 'application/json',
                          'X-CSRFToken': this.csrf_token,
                      },
                  });
              let buffer = await res.arrayBuffer();
              let file = new Blob([buffer], { type: 'application/pdf' });
              let fileURL = window.URL.createObjectURL(file);
              const elementId = 'generated-document-' + this.legal_case.id;
              let generatedDocument = document.createElement('a');
              generatedDocument.style.display = 'none';
              generatedDocument.href = fileURL;
              generatedDocument.download = this.document_type + '_' + this.legal_case.number + '.pdf';
              document.body.appendChild(generatedDocument);
              generatedDocument.click();
              window.URL.revokeObjectURL(fileURL);
              return true
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
