<template>
    <div id="intelligenceInformation">
        <FormSection :label="`Intelligence Information`" :Index="`0`">
        <div class="row">
            <div class="col-lg-6">
                <textarea
                 v-model="intelligenceText"
                 style="width:100%"
                />
            </div>
            <div class="col-lg-2" v-if="saving">
                <div v-if="show_spinner"><i class='fa fa-2x fa-spinner fa-spin'></i></div>
            </div>
            <div class="col-lg-2" v-else>
                <input type="button" @click.prevent="saveIntelligence" class="btn btn-primary" value="Save"/>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <filefield 
                ref="intelligence_information" 
                name="intelligence-information-file" 
                :isRepeatable="true" 
                :documentActionUrl="documentActionUrl"  
                />
            </div>
        </div>
        </FormSection>

    </div>
</template>
<script>
    import $ from 'jquery'
    import Vue from 'vue'
    import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
    import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
    import FormSection from "@/components/forms/section_toggle.vue";
    import filefield from '@/components/common/compliance_file.vue';
    //import CreateLegalCaseModal from "./create_legal_case_modal.vue";
    
    export default {
        name: 'IntelligenceInformation',
        data() {
            let vm = this;
            return {
                intelligenceText: "",
                saving: false,
            }
        },
        props: {
            entity_id:{
                type: Number,
                required: true
            },
            entity_type:{
                type: String,
                required: true
            },
        },

        beforeRouteEnter: function(to, from, next) {
            next(async (vm) => {
                // await vm.loadCurrentUser({ url: `/api/my_compliance_user_details` });
            });
        },
        /*
        created: async function() {
            // Status choices
            let returned_status_choices = await cache_helper.getSetCacheList(
                'LegalCase_StatusChoices', 
                '/api/legal_case/status_choices'
                );
            
            Object.assign(this.statusChoices, returned_status_choices);
            this.statusChoices.splice(0, 0, {id: 'all', display: 'All'});

        },
        */
        components: {
            FormSection,
            filefield,
        },
        computed: {
            documentActionUrl: function() {
                let url = '';
                if (this.entity_type === 'org') {
                    url =  helpers.add_endpoint_join(
                    api_endpoints.organisations,
                    this.entity_id + "/process_intelligence_document/"
                    )
                } else if (this.entity_type === 'person') {
                    url =  helpers.add_endpoint_join(
                    api_endpoints.users,
                    this.entity_id + "/process_intelligence_document/"
                    )
                }
                return url;
            },
            saveIntelligenceUrl: function() {
                let url = '';
                if (this.entity_type === 'org') {
                    url =  helpers.add_endpoint_join(
                    api_endpoints.organisations,
                    this.entity_id + "/save_intelligence_text/"
                    )
                } else if (this.entity_type === 'person') {
                    url =  helpers.add_endpoint_join(
                    api_endpoints.users,
                    this.entity_id + "/save_intelligence_text/"
                    )
                }
                return url;
            },

        },
        methods: {
            /*
            ...mapActions('legalCaseStore', {
                saveInspection: "saveLegalCase",
            }),
            */
            saveIntelligence: function() {
                //console.log("save")
                this.saving=true;
                this.$nextTick(async () => {
                    await Vue.http.post(this.saveIntelligenceUrl, {'intelligence_text': this.intelligenceText});
                });
                this.saving=false;
            }
        },
        mounted: async function () {
            let vm = this;
            $('a[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                }, 100);
            });
            this.$nextTick(async () => {
                let url = '';
                if (this.entity_type === 'org') {
                    url =  helpers.add_endpoint_join(
                    api_endpoints.organisations,
                    this.entity_id + "/get_intelligence_text/"
                    )
                } else if (this.entity_type === 'person') {
                    url =  helpers.add_endpoint_join(
                    api_endpoints.users,
                    this.entity_id + "/get_intelligence_text/"
                    )
                }
                console.log(url)
                const response = await Vue.http.get(url);
                console.log(response)
                this.intelligenceText = response.body.intelligence_text;
            });
        }
    }
</script>
