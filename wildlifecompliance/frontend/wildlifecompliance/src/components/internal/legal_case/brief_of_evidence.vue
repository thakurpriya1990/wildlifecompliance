<template lang="html">
        <div class="col-md-9">
            <div class="row">
                            <FormSection :formCollapse="false" label="Statement of Facts">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">Statement of facts
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.statement_of_facts" />
                                    </label>
                                </div></div>
                            </FormSection>
                            <FormSection :formCollapse="false" label="Case Information Form">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.victim_impact_statement_taken" />
                                    Victim impact statement to be taken?
                                    </label>
                                    <label v-if="briefOfEvidence.victim_impact_statement_taken" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.victim_impact_statement_taken_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.statements_pending" />
                                    Witness (including expert statements) still to be taken?
                                    </label>
                                    <label v-if="briefOfEvidence.statements_pending" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.statements_pending_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.vulnerable_hostile_witnesses" />
                                    Vulnerable / hostile witnesses?
                                    </label>
                                    <label v-if="briefOfEvidence.vulnerable_hostile_witnesses" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.vulnerable_hostile_witnesses_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.witness_refusing_statement" />
                                    Witnesses refusing to make statements?
                                    </label>
                                    <label v-if="briefOfEvidence.witness_refusing_statement" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.witness_refusing_statement_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.problems_needs_prosecution_witnesses" />
                                    Specific problems / needs of prosecution witnesses, e.g. interpreters?
                                    </label>
                                    <label v-if="briefOfEvidence.problems_needs_prosecution_witnesses" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.problems_needs_prosecution_witnesses" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.accused_bad_character" />
                                    History of bad character / propensity (similar fact) evidence involving accused?
                                    </label>
                                    <label v-if="briefOfEvidence.accused_bad_character" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.accused_bad_character_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.further_persons_interviews_pending" />
                                    Further persons (witness or suspect) to be interviewed?
                                    </label>
                                    <label v-if="briefOfEvidence.further_persons_interviews_pending" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.further_persons_interviews_pending_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.other_interviews" />
                                    Other persons whose details do not appear on this brief who have been interviewed?
                                    </label>
                                    <label v-if="briefOfEvidence.other_interviews" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.other_interviews_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.relevant_persons_pending_charges" />
                                    Other relevant persons charged or yet to be charged?
                                    </label>
                                    <label v-if="briefOfEvidence.relevant_persons_pending_charges" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.relevant_persons_pending_charges_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.other_persons_receiving_sanction_outcome" />
                                    Others receiving Infringement / Warning arising out of the same incident?
                                    </label>
                                    <label v-if="briefOfEvidence.other_persons_receiving_sanction_outcome" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.other_persons_receiving_sanction_outcome_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.local_public_interest" />
                                    Matters of local / public interest?
                                    </label>
                                    <label v-if="briefOfEvidence.local_public_interest" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.local_public_interest_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.applications_orders_requests" />
                                    Other applications / orders on conviction requests?
                                    </label>
                                    <label v-if="briefOfEvidence.applications_orders_requests" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.applications_orders_requests_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.applications_orders_required" />
                                    Are there any other applications / orders on conviction required?
                                    </label>
                                    <label v-if="briefOfEvidence.applications_orders_required" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.applications_orders_required_details" />
                                    </label>
                                    <label class="col-sm-10">
                                    <input :onclick="readonlyBriefOfEvidence" type="checkbox" data-parsley-required v-model="briefOfEvidence.other_legal_matters" />
                                    Is there any statutory notice, DEC licence, ministerial statement or policy etc. re the matter, premise or person subject to this brief?
                                    </label>
                                    <label v-if="briefOfEvidence.other_legal_matters" class="col-sm-10">Details
                                        <textarea :readonly="readonlyForm" class="form-control location_address_field" v-model="briefOfEvidence.other_legal_matters_details" />
                                    </label>
                                </div></div>
                            </FormSection>
                            <FormSection :formCollapse="false" label="Offences, Offenders and Records of Interview" treeHeight="yes">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <TreeSelect 
                                    ref="record_of_interview_tree" 
                                    :value="boeRoiTicked" 
                                    :options="boeRoiOptions" 
                                    :default-expand-level="Infinity" 
                                    :disabled="false"
                                    multiple
                                    value-consists-of="LEAF_PRIORITY"
                                    @input="setBoeRoiTicked"
                                    />
                                </div></div>
                            </FormSection>
                            <FormSection :formCollapse="false" label="Witness Statements, Officer Statements, Expert Statements" treeHeight="yes">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <TreeSelect 
                                    ref="other_statements_tree" 
                                    :value="boeOtherStatementsTicked" 
                                    :options="boeOtherStatementsOptions" 
                                    :default-expand-level="Infinity" 
                                    :disabled="false"
                                    multiple
                                    value-consists-of="LEAF_PRIORITY"
                                    @input="setBoeOtherStatementsTicked"
                                    alwaysOpen
                                    :searchable="false"
                                    />
                                </div></div>
                            </FormSection>
                            <FormSection id="physical-artifacts-tree" :formCollapse="false" label="List of Exhibits, Sensitive Unused and Non-Sensitive Unused Materials" treeHeight="yes">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <label class="col-sm-10">Select the objects to be included on the list of exhibits
                                        <div class="row" v-for="artifact in physicalArtifactsUsed">
                                            <input class="col-sm-1" type="checkbox" :value="artifact.id" v-model="physicalArtifactsUsedTicked">
                                            <label class="col-sm-4">{{ artifact.label }}</label>
                                        </div>
                                    </label>
                                    <label class="col-sm-10">Select the objects to be included on the sensitive unused list of materials
                                        <div class="row" v-for="artifact in physicalArtifactsSensitiveUnused">
                                            <input class="col-sm-1" :id="'tickbox_' + artifact.id" type="checkbox" :value="artifact.id" v-model="physicalArtifactsSensitiveUnusedTicked">
                                            <label class="col-sm-4">{{ artifact.label }}</label>
                                            <textarea 
                                                class="form-control col-sm-6" 
                                                :value="artifact.reason_sensitive_non_disclosable" 
                                                :id="'reason_' + artifact.id"
                                                @input="setPhysicalArtifactSensitiveUnusedReason"
                                                />
                                        </div>
                                    </label>
                                    <label class="col-sm-10">Select the objects to be included on the non-sensitive unused list of materials
                                        <div class="row" v-for="artifact in physicalArtifactsNonSensitiveUnused">
                                            <input class="col-sm-1" type="checkbox" :value="artifact.id" v-model="physicalArtifactsNonSensitiveUnusedTicked">
                                            <label class="col-sm-4">{{ artifact.label }}</label>
                                        </div>
                                    </label>
                                </div></div>
                            </FormSection>
                            <FormSection :formCollapse="false" label="List of Photographic, Video and Sound Exhibits" treeHeight="yes">
                                <div class="col-sm-12 form-group"><div class="row">
                                    <TreeSelect 
                                    ref="document_artifacts_tree" 
                                    :value="boeDocumentArtifactsTicked" 
                                    :options="boeDocumentArtifactsOptions" 
                                    :default-expand-level="Infinity" 
                                    :disabled="false"
                                    multiple
                                    value-consists-of="LEAF_PRIORITY"
                                    @input="setBoeDocumentArtifactsTicked"
                                    alwaysOpen
                                    :searchable="false"
                                    />
                                </div></div>
                            </FormSection>
                            <FormSection :formCollapse="false" label="Additional Documents">
                                <div class="col-sm-12 form-group"><div class="row">
                                </div></div>
                            </FormSection>
            </div>
        </div>
</template>
<script>
import Vue from "vue";
import FormSection from "@/components/forms/section_toggle.vue";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import _ from 'lodash';
import TreeSelect from '@riophae/vue-treeselect'
import '@riophae/vue-treeselect/dist/vue-treeselect.css'


export default {
    name: "ViewBriefOfEvidence",
    data: function() {
        return {
            //boeRoiTicked: [],
            //boeRoiOptions: [],
            //boeOtherStatementsOptions: [],
            uuid: 0,
            briefOfEvidence: {},
            physicalArtifacts: [],
            physicalArtifactsNonSensitiveUnused: [],
            physicalArtifactsSensitiveUnused: [],
            physicalArtifactsUsed: [],
            physicalArtifactsNonSensitiveUnusedTicked: [],
            physicalArtifactsSensitiveUnusedTicked: [],
            physicalArtifactsSensitiveUnusedReason: [],
            physicalArtifactsUsedTicked: [],
      };
  },
  components: {
    FormSection,
    TreeSelect,
  },
  computed: {
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
    }),
    csrf_token: function() {
      return helpers.getCookie("csrftoken");
    },
      /*
    briefOfEvidence: function() {
        let brief = []
        if (this.legal_case && this.legal_case.brief_of_evidence) {
            brief = this.legal_case.brief_of_evidence;
        }
        return brief;
    },
    */

    readonlyForm: function() {
        let readonly = true
        if (this.legal_case && this.legal_case.id) {
            readonly = !this.legal_case.can_user_action;
        }
        return readonly
    },
    readonlyBriefOfEvidence: function() {
        let readonly = true
        if (this.legal_case && this.legal_case.id) {
            readonly = !this.legal_case.can_user_action;
        }
        return readonly
    },
    canUserAction: function() {
        let return_val = false
        if (this.legal_case && this.legal_case.id) {
            return_val = this.legal_case.can_user_action;
        }
        return return_val
    },
    boeRoiTicked: function() {
        let ticked = []
        if (this.legal_case && this.legal_case.boe_roi_ticked) {
            for (let id of this.legal_case.boe_roi_ticked) {
                ticked.push(id)
            }
        }
        return ticked;
    },
    boeOtherStatementsTicked: function() {
        let ticked = []
        if (this.legal_case && this.legal_case.boe_other_statements_ticked) {
            for (let id of this.legal_case.boe_other_statements_ticked) {
                ticked.push(id)
            }
        }
        return ticked;
    },
    boeOtherStatementsOptions: function() {
        let options = [];
        if (this.legal_case && this.legal_case.boe_other_statements_options) {
            options = this.legal_case.boe_other_statements_options;
        }
        return options;
    },
    boeRoiOptions: function() {
        let options = [];
        if (this.legal_case && this.legal_case.boe_roi_options) {
            options = this.legal_case.boe_roi_options;
        }
        return options;
    },
    boePhysicalArtifactsTicked: function() {
        let ticked = []
        if (this.legal_case && this.legal_case.boe_physical_artifacts_ticked) {
            for (let id of this.legal_case.boe_physical_artifacts_ticked) {
                ticked.push(id)
            }
        }
        return ticked;
    },
    boePhysicalArtifactsOptions: function() {
        let options = [];
        if (this.legal_case && this.legal_case.boe_physical_artifacts_options) {
            options = this.legal_case.boe_physical_artifacts_options;
        }
        return options;
    },
    boeDocumentArtifactsTicked: function() {
        let ticked = []
        if (this.legal_case && this.legal_case.boe_document_artifacts_ticked) {
            for (let id of this.legal_case.boe_document_artifacts_ticked) {
                ticked.push(id)
            }
        }
        return ticked;
    },
    boeDocumentArtifactsOptions: function() {
        let options = [];
        if (this.legal_case && this.legal_case.boe_document_artifacts_options) {
            options = this.legal_case.boe_document_artifacts_options;
        }
        return options;
    },

  },
  filters: {
    formatDate: function(data) {
      return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
    }
  },
  methods: {
    ...mapActions('legalCaseStore', {
      loadLegalCase: 'loadLegalCase',
      saveLegalCase: 'saveLegalCase',
      setLegalCase: 'setLegalCase',
      setBoeRoiTicked: 'setBoeRoiTicked',
      setBoeOtherStatementsTicked: 'setBoeOtherStatementsTicked',
      setBoePhysicalArtifactsTicked: 'setBoePhysicalArtifactsTicked',
      setBoeDocumentArtifactsTicked: 'setBoeDocumentArtifactsTicked',
      setPhysicalArtifactSensitiveUnusedReason: 'setPhysicalArtifactSensitiveUnusedReason',
    }),
    /*
    setPhysicalArtifactSensitiveUnusedReason: function(artifact) {
        console.log(artifact)
        this.set
    },
    */
    setPhysicalArtifactsUsed: function(artifact) {
        console.log(artifact)
    },
    setPhysicalArtifactDetails: function(elemId, fieldValue) {
        let physical_artifact_id = elemId.replace("boe_physical_artifact_", "");
        let fieldUpdated = false;
        for (let artifact of this.physicalArtifacts) {
            if (artifact.physical_artifact_id === physical_artifact_id) {
                artifact.details = fieldValue;
                fieldUpdated = true;
            } 
        }
        if (!fieldUpdated) {
            this.physicalArtifacts.push({
                "physical_artifact_id": physical_artifact_id,
                "details": fieldValue,
            });
        }
    },
    addEventListeners: function() {
      let vm = this;
      let physicalArtifactsTree = $('#physical-artifacts-tree :input');
      //let physicalArtifactsTree = $("#physical-artifacts-tree");
      //let physicalArtifactsTree = $(".boe_physical_artifacts_textarea");
      //let physicalArtifactsTree = $(":textarea");
      //console.log(physicalArtifactsTree);
      physicalArtifactsTree.on(
          'input', 
          (e) => {
              //console.log(e)
              this.setPhysicalArtifactDetails(e.target.id, e.target.value);
          });
        /*
      physicalArtifactsTree.on(
          'paste', 
          (e) => {
              console.log("plain text only");
              // cancel paste
              e.preventDefault();
              // get text representation of clipboard
              let text = (e.originalEvent || e).clipboardData.getData('text/plain');
              let transformedText = text.replace(/\n/g,'<br/>')
              console.log(transformedText);
              // insert text manually
              document.execCommand("insertHTML", false, transformedText);
              //this.setPhysicalArtifactDetails(e.target.id, transformedText);
          });
        */
    },

  },
  created: async function() {
      if (this.legal_case && this.legal_case.brief_of_evidence) {
          Object.assign(this.briefOfEvidence, this.legal_case.brief_of_evidence);
      }
      if (this.legal_case.boe_physical_artifacts_non_sensitive_unused_options &&
          this.legal_case.boe_physical_artifacts_non_sensitive_unused_options.length > 0) {
          for (let artifact of this.legal_case.boe_physical_artifacts_non_sensitive_unused_options) {
              let cloned_artifact = _.cloneDeep(artifact);
              this.physicalArtifactsNonSensitiveUnused.push(artifact)
              if (artifact.ticked) {
                  this.physicalArtifactsNonSensitiveUnusedTicked.push(artifact.id)
              }
            }
      }
      if (this.legal_case.boe_physical_artifacts_sensitive_unused_options &&
          this.legal_case.boe_physical_artifacts_sensitive_unused_options.length > 0) {
          for (let artifact of this.legal_case.boe_physical_artifacts_sensitive_unused_options) {
              let cloned_artifact = _.cloneDeep(artifact);
              this.physicalArtifactsSensitiveUnused.push(artifact)
              if (artifact.ticked) {
                  this.physicalArtifactsSensitiveUnusedTicked.push(artifact.id)
              }
          }
      }
      if (this.legal_case.boe_physical_artifacts_used_options &&
          this.legal_case.boe_physical_artifacts_used_options.length > 0) {
          for (let artifact of this.legal_case.boe_physical_artifacts_used_options) {
              let cloned_artifact = _.cloneDeep(artifact);
              this.physicalArtifactsUsed.push(artifact)
              if (artifact.ticked) {
                  this.physicalArtifactsUsedTicked.push(artifact.id)
              }
          }
      }

  },
  mounted: function() {
      this.$nextTick(() => {
          this.addEventListeners();
          $('.vue-treeselect__control').css("display", "none");
        });
  },
};
</script>

<style lang="css">
.action-button {
    margin-top: 5px;
}
.new-row-button {
    margin-bottom: 5px;
    margin-right: 13px;
}
#close-button {
  margin-bottom: 50px;
}
.awesomplete {
    width: 100% !important;
}
.nav>li>a:focus, .nav>li>a:hover {
  text-decoration: none;
  background-color: #eee;
}
.nav-item {
  background-color: hsla(0, 0%, 78%, .8) !important;
  margin-bottom: 2px;
}
.inline-datatable {
  overflow-wrap: break-word;
}
</style>
