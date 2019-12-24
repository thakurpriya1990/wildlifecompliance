<template lang="html">
    <div class="container-fluid">
        <div class="col-sm-12 child-artifact-component">
            <div class="form-group">
                <div class="row">
                    <ul class="nav nav-pills">
                        <li class="nav-item active"><a data-toggle="tab" @click="updateTabSelected('objectTab')" :href="'#'+newTab">New</a></li>
                        <li class="nav-item"><a data-toggle="tab" :href="'#'+existingTab" >Existing</a></li>
                    </ul>
                    <div class="tab-content">
                        <div :id="newTab" class="tab-pane fade in active">
                            <ul class="nav nav-pills">
                                <li :class="objectTabListClass"><a data-toggle="tab" @click="updateTabSelected('objectTab')" :href="'#'+objectTab">Object</a></li>
                                <li :class="detailsTabListClass"><a data-toggle="tab" @click="updateTabSelected('detailsTab')" :href="'#'+detailsTab" >Details</a></li>
                                <li :class="storageTabListClass"><a data-toggle="tab" @click="updateTabSelected('storageTab')" :href="'#'+storageTab" >Storage</a></li>
                                <li :class="disposalTabListClass"><a data-toggle="tab" @click="updateTabSelected('disposalTab')" :href="'#'+disposalTab" >Disposal</a></li>
                            </ul>
                            <div class="tab-content">
                                    <div :id="objectTab" :class="objectTabClass">
                                        <div class="col-sm-12">
                                            <div class="form-group">
                                              <div class="row">
                                                <div class="col-sm-3">
                                                  <label>Physical Type</label>
                                                </div>
                                                <div class="col-sm-6">
                                                  <select class="form-control" v-model="physical_artifact.physical_artifact_type">
                                                    <option  v-for="option in physicalArtifactTypes" :value="option" v-bind:key="option.id">
                                                      {{ option.artifact_type }}
                                                    </option>
                                                  </select>
                                                </div>
                                              </div>
                                            </div>
                                        </div>
                                        <div class="col-sm-12">
                                            <div class="form-group">
                                                <div class="row">
                                                    <div class="col-sm-3">
                                                        <label class="control-label pull-left" for="Name">Seizure Notice</label>
                                                    </div>
                                                    <div class="col-sm-9">
                                                        <filefield
                                                        ref="default_document"
                                                        name="default-document"
                                                        :isRepeatable="true"
                                                        documentActionUrl="temporary_document"
                                                        @update-temp-doc-coll-id="setTemporaryDocumentCollectionId"/>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="form-group">
                                              <div class="row">
                                                <div class="col-sm-3">
                                                  <label>Identifier</label>
                                                </div>
                                                <div class="col-sm-9">
                                                  <input :readonly="readonlyForm" class="form-control" v-model="physical_artifact.identifier"/>
                                                </div>
                                              </div>
                                            </div>
                                            <div class="form-group">
                                              <div class="row">
                                                <div class="col-sm-3">
                                                  <label>Description</label>
                                                </div>
                                                <div class="col-sm-9">
                                                  <textarea :readonly="readonlyForm" class="form-control" v-model="physical_artifact.description"/>
                                                </div>
                                              </div>
                                            </div>
                                            <div class="form-group">
                                                <div class="row">
                                                    <div class="col-sm-3">
                                                        <label>Witness</label>
                                                    </div>
                                                    <div class="col-sm-9">
                                                        <select ref="department_users" class="form-control">
                                                            <option  v-for="option in departmentStaffList" :value="option.pk" v-bind:key="option.pk">
                                                            {{ option.name }} 
                                                            </option>
                                                        </select>
                                                    </div>
                                                    <!--div class="col-sm-9">
                                                        <SearchPersonOrganisation 
                                                        personOnly
                                                        :isEditable="!readonlyForm" 
                                                        classNames="form-control" 
                                                        @entity-selected="entitySelected"
                                                        showCreateUpdate
                                                        ref="physical_artifact_search_person_organisation"
                                                        v-bind:key="updateSearchPersonOrganisationBindId"
                                                        addFullName
                                                        :displayTitle="false"
                                                        domIdHelper="physical_artifact"
                                                        departmentalStaff
                                                        />
                                                    </div-->
                                                </div>
                                            </div>
                                            <div class="form-group">
                                                <div class="row">
                                                    <label class="col-sm-3">Date</label>
                                                    <div class="col-sm-3">
                                                        <div class="input-group date" ref="artifactDatePicker">
                                                            <input :disabled="readonlyForm" type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="physical_artifact.artifact_date" />
                                                            <span class="input-group-addon">
                                                                <span class="glyphicon glyphicon-calendar"></span>
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <label class="col-sm-3">Time</label>
                                                    <div class="col-sm-3">
                                                        <div class="input-group date" ref="artifactTimePicker">
                                                          <input :disabled="readonlyForm" type="text" class="form-control" placeholder="HH:MM" v-model="physical_artifact.artifact_time"/>
                                                          <span class="input-group-addon">
                                                              <span class="glyphicon glyphicon-calendar"></span>
                                                          </span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <!--div :id="detailsTab" class="tab-pane fade in li-top-buffer">
                                        details
                                    </div>
                                    <div :id="storageTab" class="tab-pane fade in li-top-buffer">
                                        storage
                                    </div>
                                    <div :id="disposalTab" class="tab-pane fade in li-top-buffer">
                                        disposal
                                    </div-->
                                    <div :id="detailsTab" :class="detailsTabClass">
                                        details
                                    </div>
                                    <div :id="storageTab" :class="storageTabClass">
                                        storage
                                    </div>
                                    <div :id="disposalTab" :class="disposalTabClass">
                                        disposal
                                    </div>
                            </div>
                        </div>
                        <div :id="existingTab" class="tab-pane fade in li-top-buffer">
                            existing
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</template>
<script>
import Vue from "vue";
//import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import filefield from '@/components/common/compliance_file.vue';
//import { required, minLength, between } from 'vuelidate/lib/validators'
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
import moment from 'moment';
import SearchPersonOrganisation from './search_person_or_organisation'
//require("select2/dist/css/select2.min.css");
//require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    name: "PhysicalArtifactComponent",
    data: function() {
        return {
            uuid: 0,
            newTab: 'newTab'+this._uid,
            existingTab: 'existingTab'+this._uid,
            objectTab: 'objectTab'+this._uid,
            detailsTab: 'detailsTab'+this._uid,
            storageTab: 'storageTab'+this._uid,
            disposalTab: 'disposalTab'+this._uid,
            tabSelected: 'objectTab',
            isModalOpen: false,
            processingDetails: false,
            documentActionUrl: '',
            temporary_physical_collection_id: null,
            physicalArtifactTypes: [],
            departmentStaffList: [],
            selectedCustodian: {},
            entity: {
                id: null,
            },
        }
    },
    components: {
      //modal,
      filefield,
      SearchPersonOrganisation,
    },
    watch: {
        artifactType: {
            handler: function (){
                /*
                if (this.statementVisibilityArray.includes(this.artifactType)) {
                    console.log("statementVisibility true")
                    this.statementVisibility = true;
                }
                */
            },
            deep: true,
        }
    },
    computed: {
        ...mapGetters('physicalArtifactStore', {
            physical_artifact: "physical_artifact",
        }),
        ...mapGetters('legalCaseStore', {
            legal_case: "legal_case",
        }),
        artifactType: function() {
            let aType = ''
            if (this.physical_artifact && this.physical_artifact.physical_artifact_type) {
                aType = this.physical_artifact.physical_artifact_type.artifact_type;
            }
            return aType;
        },
        readonlyForm: function() {
            return false;
        },
        updateSearchPersonOrganisationBindId: function() {
            this.uuid += 1
            return "PhysicalArtifact_SearchPerson_" + this.uuid.toString();
        },
        objectTabSelected: function() {
            let isTab = false;
            if (this.tabSelected === 'objectTab') {
                isTab = true;
            }
            return isTab;
        },
        detailsTabSelected: function() {
            let isTab = false;
            if (this.tabSelected === 'detailsTab') {
                isTab = true;
            }
            return isTab;
        },
        storageTabSelected: function() {
            let isTab = false;
            if (this.tabSelected === 'storageTab') {
                isTab = true;
            }
            return isTab;
        },
        disposalTabSelected: function() {
            let isTab = false;
            if (this.tabSelected === 'disposalTab') {
                isTab = true;
            }
            return isTab;
        },
        objectTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.objectTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        objectTabClass: function() {
            let tabClass = 'li-top-buffer tab-pane fade in';
            if (this.objectTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        detailsTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.detailsTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        detailsTabClass: function() {
            let tabClass = 'li-top-buffer tab-pane fade in';
            if (this.detailsTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        storageTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.storageTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        storageTabClass: function() {
            let tabClass = 'li-top-buffer tab-pane fade in';
            if (this.storageTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        disposalTabListClass: function() {
            let tabClass = 'nav-item';
            if (this.disposalTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
        disposalTabClass: function() {
            let tabClass = 'li-top-buffer tab-pane fade in';
            if (this.disposalTabSelected) {
                tabClass += ' active';
            }
            return tabClass;
        },
    },
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
        ...mapActions('physicalArtifactStore', {
            savePhysicalArtifact: 'savePhysicalArtifact',
            loadPhysicalArtifact: 'loadPhysicalArtifact',
            setPhysicalArtifact: 'setPhysicalArtifact',
        }),
        updateTabSelected: function(tabValue) {
            this.tabSelected = tabValue;
        },
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
        entitySelected: function(entity) {
            console.log(entity);
            Object.assign(this.entity, entity)
        },
        save: async function() {
            if (this.physical_artifact.id) {
                await this.savePhysicalArtifact({ create: false, internal: false });
            } else {
                await this.savePhysicalArtifact({ create: true, internal: false });
            }
        },
        parentSave: async function() {
            //let physicalArtifactEntity = null;
            /*
            if (this.saveButtonEnabled) {
                savedEmailUser = await this.saveData('parentSave')
            } else {
                savedEmailUser = {'ok': true};
            }
            */
            await this.save();
            //this.entity.id = 
            this.$nextTick(() => {
                this.$emit('entity-selected', {
                    id: this.physical_artifact.id,
                    data_type: 'physical_artifact',
                    identifier: this.physical_artifact.identifier,
                    artifact_type: this.artifactType,
                });
            });
            //return physicalArtifactEntity;
        },
        cancel: async function() {
            await this.$refs.default_document.cancel();
        },
        addEventListeners: function() {
            let vm = this;
            let el_fr_date = $(vm.$refs.artifactDatePicker);
            let el_fr_time = $(vm.$refs.artifactTimePicker);

            // "From" field
            el_fr_date.datetimepicker({
            format: "DD/MM/YYYY",
            minDate: "now",
            showClear: true
            });
            el_fr_date.on("dp.change", function(e) {
                console.log(e)
                if (el_fr_date.data("DateTimePicker").date()) {
                  vm.physical_artifact.artifact_date = e.date.format("DD/MM/YYYY");
                } else if (el_fr_date.data("date") === "") {
                  vm.physical_artifact.artifact_date = "";
                }
            });
            el_fr_time.datetimepicker({ format: "LT", showClear: true });
            el_fr_time.on("dp.change", function(e) {
                console.log(e)
                if (el_fr_time.data("DateTimePicker").date()) {
                  vm.physical_artifact.artifact_time = e.date.format("LT");
                } else if (el_fr_time.data("date") === "") {
                  vm.physical_artifact.artifact_time = "";
                }
            });
            // department_users
            $(vm.$refs.department_users).select2({
                    "theme": "bootstrap",
                    allowClear: true,
                    placeholder:""
                }).
                on("select2:select",function (e) {
                    console.log(e)
                    let selected = $(e.currentTarget);
                    let selectedData = selected.val();
                    vm.setSelectedCustodian(selectedData);
                    //let custodianData = e.params.data
                    //console.log(custodianData)
                    //Object.assign(vm.selectedCustodian, custodianData);
                }).
                on("select2:unselect",function (e) {
                    var selected = $(e.currentTarget);
                    vm.selectedCustodian = {}
                });
            
        },
        setSelectedCustodian: function(pk) {
            for (let record of this.departmentStaffList) {
                if (record.pk.toString() === pk) {
                    console.log(record)
                    Object.assign(this.selectedCustodian, record);
                }
            }
        },
        compare: function(a, b) {
            console.log("compare")
            const nameA = a.name.toLowerCase();
            const nameB = b.name.toLowerCase();

            let comparison = 0;
            if (this.bandA > this.bandB) {
                comparison = 1;
            } else if (this.bandA < this.bandB) {
                comparison = -1;
            }
            return comparison;
        },

      //createPhysicalActionUrl: async function(done) {
      //  if (!this.inspection.id) {
      //      // create inspection and update vuex
      //      let returned_inspection = await this.saveInspection({ create: true, internal: true })
      //      await this.loadInspection({inspection_id: returned_inspection.body.id});
      //  }
      //  // populate filefield physical_action_url
      //  this.$refs.comms_log_file.physical_action_url = this.inspection.createInspectionProcessCommsLogsPhysicalUrl;
      //  return done(true);
      //},

    },
    mounted: function() {
      this.$nextTick(async () => {
          this.addEventListeners();
      });
    },
    beforeDestroy: async function() {
        console.log("beforeDestroy")
        await this.setPhysicalArtifact({});
    },
    /*
    destroyed: function() {
        console.log("destroyed")
    },
    */
    created: async function() {
        console.log("created")
        if (this.$route.params.physical_artifact_id) {
            await this.loadPhysicalArtifact({ physical_artifact_id: this.$route.params.physical_artifact_id });
        }
        //await this.loadPhysicalArtifact({ physical_artifact_id: 1 });
        //console.log(this)
        // physical artifact types
        let returned_physical_artifact_types = await cache_helper.getSetCacheList(
          'PhysicalArtifactTypes',
          api_endpoints.physical_artifact_types
          );
        Object.assign(this.physicalArtifactTypes, returned_physical_artifact_types);
        // blank entry allows user to clear selection
        this.physicalArtifactTypes.splice(0, 0,
          {
            id: "",
            artifact_type: "",
            description: "",
          });
        // retrieve department_users from backend cache
        let returned_department_users = await this.$http.get(api_endpoints.department_users)
        Object.assign(this.departmentStaffList, returned_department_users.body)
        this.departmentStaffList.splice(0, 0,
          {
            pk: "",
            name: "",
          });
        /*
        let returned_department_staff = await cache_helper.getSetCacheList(
          'DepartmentStaff',
          //'https://itassets.dbca.wa.gov.au/api/users/fast/?minimal=true'
          api_endpoints.department_users
          );
        //const sorted_department_staff = returned_department_staff.sort(this.compare);
        this.$nextTick(() => {
            //Object.assign(this.departmentStaffList, sorted_department_staff);
            Object.assign(this.departmentStaffList, returned_department_staff);
            // blank entry allows user to clear selection
            this.departmentStaffList.splice(0, 0,
              {
                pk: "",
                name: "",
                //artifact_type: "",
                //description: "",
              });
        });
        */

    },
};
</script>

<style lang="css">
.child-artifact-component {
    margin-top: 20px;
}
.li-top-buffer {
    margin-top: 20px;
}
.tab-content {
  background: white;
}
</style>
