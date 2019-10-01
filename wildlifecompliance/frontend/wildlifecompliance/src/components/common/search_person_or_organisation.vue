<template lang="html">
    <div class="">
        <div class="col-sm-12 form-group"><div class="row">
                <label class="col-sm-4">{{ labelTitle }}</label>
                <input :disabled="!isEditable" class="col-sm-1" id="individual" type="radio" v-model="searchType" v-bind:value="`individual`">
                <label class="col-sm-1" for="individual">Person</label>
                <input :disabled="!isEditable" class="col-sm-1" id="organisation" type="radio" v-model="searchType" v-bind:value="`organisation`">
                <label class="col-sm-1" for="organisation">Organisation</label>
        </div></div>
        <div class="form-group"><div class="row">
            <div class="col-sm-12">
                <div class="col-sm-8">
                    <input :id="elemId" :class="classNames" :readonly="!isEditable" ref="search_person_org"/>
                </div>
                <div v-if="showCreateUpdate && searchType === 'individual'" class="col-sm-2">
                    <input :disabled="!isEditable" type="button" class="btn btn-primary" value="Create New Person" @click.prevent="createNewPerson()" />
                    <!--input :disabled="!isEditable" type="button" class="btn btn-primary" value="Create/Update Person" @click.prevent="createUpdatePersonClicked()" /-->
                </div>
                <div v-else-if="showCreateUpdate && searchType === 'organisation'" class="col-sm-2">
                    <input :disabled="!isEditable" type="button" class="btn btn-primary" value="Create/Update Organisation" @click.prevent="createUpdateOrganisationClicked()" />
                </div>
            </div>
        </div></div>
        <!--div class="form-group"><div class="row">
            <div class="col-sm-8" v-if="errorText">
                <strong><span style="white-space: pre;">{{ errorText }}</span></strong>
            </div>
        </div></div-->
        <div class="form-group"><div class="row">
            <div class="col-sm-12" v-if="displayUpdateCreatePerson">
              <updateCreatePerson 
              displayComponent 
              :personToUpdate="entity.id"
              @person-saved="savePerson"
              v-bind:key="updateCreatePersonBindId"
              ref="update_create_person"/>
            </div>
            <div class="col-sm-12" v-if="displayUpdateCreateOrganisation">
              <updateCreateOrganisation displayComponent @organisation-saved=""/>
            </div>
        </div></div>
    </div>
</template>

<script>
import Awesomplete from "awesomplete";
import $ from "jquery";
import "bootstrap/dist/css/bootstrap.css";
import "awesomplete/awesomplete.css";
import updateCreatePerson from '@common-components/update_create_person.vue'
import updateCreateOrganisation from '@common-components/update_create_organisation.vue'

export default {
    name: "search-person-organisation",
    data: function(){
        let vm = this;
        vm.awesomplete_obj = null;

        return {
            //elemId: 'create_new_person_' + vm._uid,
            elemId: this.search_type + vm._uid,
            entity: {
                id: null,
                data_type: null
            },
            //entity_id: null,
            //entity_data_type: null,
            displayUpdateCreatePerson: false,
            displayUpdateCreateOrganisation: false,
            searchType: '',
            errorText: '',

        }
    },
    components: {
        updateCreatePerson,
        updateCreateOrganisation,
    },
    watch: {
        entity: {
            handler: function (){
                if (this.entity.id) {
                    this.$emit('entity-selected', { 
                        id: this.entity.id, 
                        data_type: this.entity.data_type });
                }
                if (this.entity.id && this.entity.data_type === 'individual') {
                    this.displayUpdateCreatePerson = true;
                } else if (this.entity.id && this.entity.data_type === 'organisation') {
                    this.displayUpdateCreateOrganisation = true;
                }
            },
            deep: true
        },
    },
    computed: {
        labelTitle: function() {
            if (this.searchType) {
                return "Search " + this.searchType;
            }
        },
        updateCreatePersonBindId: function() {
            if (this.entity.data_type && this.entity.id) {
                return this.entity.data_type + '_' + this.entity.id
            }
        },
    },
    props: {
        // This prop is not used any more.  Instead elemId in the data is used.
        //elementId: {
        //    required: false
        //},
        classNames: {
            required: false,
            default: 'form-control',
        },
        maxItems: {
            required: false,
            default: 10
        },
        search_type: {
            required: false,
            default: 'individual' // 'individual' or 'organisation'
                                  //  This variable can be changed dynamically, for example, by the selection of radio buttons
        },
        isEditable: {
            required: false,
            default: true
        },
        excludeStaff: {
            type: Boolean,
            required: false,
            default: false,
        },
        showCreateUpdate: {
            type: Boolean,
            required: false,
            default: false,
        },
    },
    methods: {
        createNewPerson: function() {
            this.displayUpdateCreatePerson = !this.displayUpdateCreatePerson;
            this.$nextTick(() => {
                this.$refs.update_create_person.setDefaultPerson();
                this.setInput('');
            });
        },
        removeOrganisation: function() {
            //this.$refs.update_create_person.setDefaultPerson();
        },
        clearInput: function(){
            document.getElementById(this.elemId).value = "";
        },
        setInput: function(person_org_str){
            console.log("setInput")
            document.getElementById(this.elemId).value = person_org_str;
        },
        markMatchedText(original_text, input) {
            let ret_text = original_text.replace(new RegExp(input, "gi"), function( a, b) {
                return "<mark>" + a + "</mark>";
            });
            return ret_text;
        },
        createUpdateOrganisationClicked: function() {
          this.displayUpdateCreateOrganisation = !this.displayUpdateCreateOrganisation;
        },
        savePerson: function(obj) {
            console.log("savePerson")
            console.log(obj);
            if(obj.person){
                this.$emit('entity-selected', {data_type: 'individual', id: obj.person.id});

                // Set fullname and DOB into the input box
                let full_name = [obj.person.first_name, obj.person.last_name].filter(Boolean).join(" ");
                let dob = obj.person.dob ? "DOB:" + obj.person.dob : "DOB: ---";
                let value = [full_name, dob].filter(Boolean).join(", ");
                //this.$refs.search_person_org.setInput(value);
                this.setInput(value);
            } else if (obj.error) {
                console.log(obj.error);
                this.errorText = obj.error;
            } else {
                // Should not reach here
            }
        },
        initAwesomplete: function() {
            let vm = this;

            let element_search = document.getElementById(vm.elemId);
            vm.awesomplete_obj = new Awesomplete(element_search, {
                maxItems: vm.maxItems,
                sort: false,
                filter: () => {
                    return true;
                }, 
                item: function(text, input) {
                    let ret = Awesomplete.ITEM(text, ""); // Not sure how this works but this doesn't add <mark></mark>
                    return ret;
                },
                data: function(item, input) {
                    if (vm.search_type == "individual") {
                        let f_name = item.first_name ? item.first_name : "";
                        let l_name = item.last_name ? item.last_name : "";
            
                        let full_name = [f_name, l_name].filter(Boolean).join(" ");
                        let email = item.email ? "E:" + item.email : "";
                        let p_number = item.phone_number ? "P:" + item.phone_number : "";
                        let m_number = item.mobile_number ? "M:" + item.mobile_number : "";
                        let dob = item.dob ? "DOB:" + item.dob : "DOB: ---";
            
                        let full_name_marked = "<strong>" + vm.markMatchedText(full_name, input) + "</strong>";
                        let email_marked = vm.markMatchedText(email, input);
                        let p_number_marked = vm.markMatchedText(p_number, input);
                        let m_number_marked = vm.markMatchedText(m_number, input);
                        let dob_marked = vm.markMatchedText(dob, input);
            
                        let myLabel = [
                            full_name_marked,
                            email_marked,
                            p_number_marked,
                            m_number_marked,
                            dob_marked
                        ].filter(Boolean).join("<br />");
                        myLabel = "<div data-item-id=" + item.id + ' data-type="individual">' + myLabel + "</div>";
            
                        return {
                            label: myLabel, // Displayed in the list below the search box
                            value: [full_name, dob].filter(Boolean).join(", "), // Inserted into the search box once selected
                            id: item.id
                        };
                    } else {
                        let name = item.name ? item.name : "";
                        let abn = item.abn ? "ABN:" + item.abn : "";
            
                        let name_marked = "<strong>" + vm.markMatchedText(name, input) + "</strong>";
                        let abn_marked = vm.markMatchedText(abn, input);
            
                        let myLabel = [name_marked, abn_marked].filter(Boolean).join("<br />");
                        myLabel = "<div data-item-id=" + item.id + ' data-type="organisation">' + myLabel + "</div>";
            
                        return {
                            label: myLabel,
                            value: [name, abn].filter(Boolean).join(", "),
                            id: item.id
                        };
                    }
                }
            });
            $(element_search)
            .on("keyup", function(ev) {
                var keyCode = ev.keyCode || ev.which;
                if ((48 <= keyCode && keyCode <= 90) || (96 <= keyCode && keyCode <= 105) || keyCode == 8 || keyCode == 46) {
                    console.log(ev.target.value)
                    vm.search_person_or_organisation(ev.target.value);
                    return false;
                }
            })
            .on("awesomplete-selectcomplete", function(ev) {
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            })
            .on("awesomplete-select", function(ev) {
                let origin = $(ev.originalEvent.origin);
                let originTagName = origin[0].tagName;
                if (originTagName != "DIV") {
                    // Assuming origin is a child element of <li>
                    origin = origin.parent();
                }
                let data_item_id = origin[0].getAttribute("data-item-id");
                let data_type = origin[0].getAttribute("data-type");

                // Emit an event so that the parent vue component can subscribe to the event: 'person-selected' 
                // and receive the data user selected.
                // 
                // id is an Emailuser.id when data_type is 'individual' or 
                // an Organisation.id when data_type is 'organisation'
                vm.$nextTick(() => {
                    vm.entity.id = parseInt(data_item_id)
                    vm.entity.data_type = data_type
                    //vm.$emit('entity-selected', { 
                    //    id: this.entity_id, 
                    //    data_type: this.entity_data_type });
                });
                // vm.$emit('entity-selected', { id: data_item_id, data_type: data_type });
            });
        },
        search_person_or_organisation(searchTerm){
            var vm = this;
            let suggest_list_offender = [];
            suggest_list_offender.length = 0;
            vm.awesomplete_obj.list = [];

            /* Cancel all the previous requests */
            if (vm.ajax_for_offender != null) {
                vm.ajax_for_offender.abort();
                vm.ajax_for_offender = null;
            }

            let search_url = "";
            if (vm.search_type == "individual") {
                search_url = "/api/search_user/?search=";
            } else {
                search_url = "/api/search_organisation/?search=";
            }

            vm.ajax_for_offender = $.ajax({
                type: "GET",
                url: search_url + searchTerm + '&exclude_staff=' + vm.excludeStaff,
                success: function(data) {
                    if (data && data.results) {
                        let persons = data.results;
                        let limit = Math.min(vm.maxItems, persons.length);
                        for (var i = 0; i < limit; i++) {
                        suggest_list_offender.push(persons[i]);
                        }
                    }
                    vm.awesomplete_obj.list = suggest_list_offender;
                    vm.awesomplete_obj.evaluate();
                },
                error: function(e) {}
            });
        },
    },
    created: function() {
        this.$nextTick(()=>{
            this.initAwesomplete();
            this.searchType = this.search_type;

            //if (this.inspection.party_inspected === 'individual') {
            //    this.entity.id = this.inspection.individual_inspected_id;
            //    this.entity.data_type = 'individual'
            //} else if (this.inspection.party_inspected === 'organisation') {
            //    this.entity.id = this.inspection.organisation_inspected_id;
            //    this.entity.data_type = 'organisation'
            //}

        });
    },
    //mounted: function() {
    //    this.$nextTick(()=>{
    //        if (this.inspection.party_inspected === 'individual') {
    //            this.entity.id = this.inspection.individual_inspected_id;
    //            this.entity.data_type = 'individual'
    //        } else if (this.inspection.party_inspected === 'organisation') {
    //            this.entity.id = this.inspection.organisation_inspected_id;
    //            this.entity.data_type = 'organisation'
    //        }
    //    });
    //},
}
</script>

<style>
.awesomplete > ul {
    margin-top: 2.5em;
}
.awesomplete > ul > li {
    border-bottom: 1px solid lightgray;
    margin: 5px 10px 5px 10px;
}
</style>
