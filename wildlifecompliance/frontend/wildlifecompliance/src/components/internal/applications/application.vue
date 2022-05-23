<template lang="html">
    <div v-if="isApplicationLoaded" class="container" id="internalApplication">
        <div id="error" v-if="missing_fields.length > 0" style="margin: 10px; padding: 5px; color: red; border:1px solid red;">
            <b>Please answer the following mandatory question(s):</b>
            <ul>
                <li v-for="error in missing_fields">
                    {{ error.label }}
                </li>
            </ul>
        </div>
        <div class="row" style="padding-bottom: 50px;">
        <h3>{{ headerLabel }}: {{ application.lodgement_number }}</h3>
        <div class="col-md-3">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" :comms_add_url="comms_add_url" :disable_add_entry="false"/>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                       Submission 
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Submitted by</strong><br/>
                                {{ application.submitter.first_name }} {{ application.submitter.last_name }}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <strong>Lodged on</strong><br/>
                                {{ application.lodgement_date | formatDate}}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <table class="table small-table">
                                    <tr>
                                        <th>Lodgement</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        Workflow 
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Status</strong><br/>
                                {{ application.processing_status.name }} {{hasCurrentLicence?'':'(attn: No Active License)'}} <br/>
                                <div class ="col-sm-12" v-for="item in licence_type_data">
                                    
                                    <div v-for="item1 in item">
                                        <div v-if="item1.name">
                                            <strong>{{item1.name}}: </strong>{{item1.processing_status.name}}
                                        </div>
                                    </div>
                                </div>
                            </div>
                             <div class="col-sm-12 top-buffer-s" v-show="showAssignToOfficer" >
                                <strong>Assigned Officer</strong><br/>
                                <div class="form-group">
                                    <template>
                                        <select ref="assigned_officer" class="form-control" v-model="selectedActivity.assigned_officer">
                                            <option v-for="member in selectedActivity.licensing_officers" :value="member.id" v-bind:key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                        </select>
                                        <a @click.prevent="assignToMe()" class="actionBtn pull-right">Assign to me</a>
                                    </template>
                                </div>
                            </div>
                            <div class="col-sm-12 top-buffer-s" v-show="showAssignToApprover && !application_workflow_state" >
                                <strong>Assigned Approver</strong><br/>
                                <div class="form-group">
                                    <template>
                                        <div>
                                        <select ref="assigned_approver" class="form-control" v-model="selectedActivity.assigned_approver" >
                                            <option v-for="member in selectedActivity.issuing_officers" :value="member.id" v-bind:key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                        </select>
                                        <a @click.prevent="makeMeApprover()" class="actionBtn pull-right">Assign to me</a>
                                        </div>
                                    </template>                                    
                                </div>
                            </div>

                            <template v-if="isFinalised">
                                <div>
                                    <div class="col-sm-12">
                                        <div class="separator"></div>
                                    </div>                                    
                                    <div class="col-sm-12">
                                        <strong>Application</strong><br/>
                                        <a class="actionBtn" v-if="showingApplication && !showingConditions" @click.prevent="toggleApplication({show: false})">Hide Application</a>
                                        <a class="actionBtn" v-else-if="!showingApplication && showingConditions" @click.prevent="toggleConditions({show: false, showFinalised: true})">Hide Conditions</a>
                                        <a class="actionBtn" v-else @click.prevent="toggleApplication({show: true, showFinalised: true})">Show Application</a><br/>
                                        <a class="actionBtn" v-if="(!showingApplication || !this.unfinishedActivities.length) && !showingConditions" @click.prevent="toggleConditions({show: true})">Show Conditions</a>
                                    </div>
                                </div>
                            </template>
                            <template v-if="isFinalised">
                                <div class="col-sm-12">
                                    <div class="separator"></div>
                                </div>
                            </template>
                            <template v-if="(canIssueDecline && approvingApplication && !application_workflow_state) || notOfficerWorkflow">
                                <div>
                                    <div class="col-sm-12">
                                        <div class="separator"></div>
                                    </div>
                                    <div class="col-sm-12" v-if="notOfficerWorkflow">
                                        <strong>Application</strong><br/>
                                        <a class="actionBtn" v-if="!showingApplication && showingConditions" @click.prevent="actionApplicationLink()">Show Application</a>
                                        <a class="actionBtn" v-else-if="showingApplication && !showingConditions" @click.prevent="actionApplicationLink()">Hide Application2</a><br/>
                                    </div>                                    
                                    <div class="col-sm-12" v-else>
                                        <strong>Application</strong><br/>
                                        <a class="actionBtn" v-if="!showingApplication && !showingConditions" @click.prevent="actionApplicationLink()">Show Application</a>
                                        <a class="actionBtn" v-else-if="!showingApplication && showingConditions" @click.prevent="actionConditionLink()">Hide Conditions</a>        
                                        <a class="actionBtn" v-else-if="showingApplication && !showingConditions" @click.prevent="actionApplicationLink()">Hide Application</a><br/>
                                        <a class="actionBtn" v-if="!showingApplication && !showingConditions" @click.prevent="actionConditionLink()">Show Conditions</a>
                                    </div>
                                </div>
                            </template>
                            <template v-if="(canIssueDecline && approvingApplication && !application_workflow_state) || notOfficerWorkflow">
                                <div class="col-sm-12">
                                    <div class="separator"></div>
                                </div>
                            </template>
                              <div class="col-sm-12 top-buffer-s" >
                                <template v-if="showingApplication">
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>   
                                    <div v-show="showRequestAmendmentButton && !application_workflow_state" class="row">
                                        <div class="col-sm-12">
                                            <button v-if="showRequestSpinner && showSpinner" class="btn btn-primary top-buffer-s col-xs-12" ><i class="fa fa-spinner fa-spin"/>Request Amendment</button>
                                            <button v-else-if="!showRequestSpinner && showSpinner" disabled type="button" class="btn btn-primary top-buffer-s col-xs-12" >Request Amendment</button>
                                            <button v-else class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="actionApplicantReturnButton()">Request Amendment</button><br/>
                                        </div>
                                    </div>                            
                                    <!-- <div v-show="showIssueDeclineButton" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="toggleIssue()">Issue/Decline</button>
                                        </div>
                                    </div> -->
                                    <div v-show="showAssessmentConditionButton && !application_workflow_state" class="row">
                                        <div class="col-sm-12">
                                            <button v-if="showConditionSpinner && showSpinner" class="btn btn-primary top-buffer-s col-xs-12" ><i class="fa fa-spinner fa-spin"/>Assessments &amp; Conditions</button>
                                            <button v-else-if="!showConditionSpinner && showSpinner" disabled type="button" class="btn btn-primary top-buffer-s col-xs-12" >Assessments &amp; Conditions</button>
                                            <button v-else class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="actionConditionButton()">Assessments &amp; Conditions</button><br/>
                                        </div>
                                    </div>
                                </template>
                                <template v-else>
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>
                                    <div v-show="showBackToProcessingButton && !application_workflow_state" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="actionApplicationButton()">Back to Processing</button><br/>
                                        </div>
                                    </div>
                                    <div v-if="canReturnToConditions && !application_workflow_state" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="actionOfficerReturnButton()">Return to Officer - Conditions</button>                                   
                                        </div>
                                    </div>
                                    <div v-if="canProposeIssueOrDecline && (isSendingToAssessor || showingConditions) && !application_workflow_state" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="proposedLicence()">Propose Issue</button>
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="proposedDecline()">Propose Decline</button>
                                        </div>
                                    </div>
                                    <div v-if="canProposeToOnlyDecline && (isSendingToAssessor || showingConditions) && !application_workflow_state" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="proposedDecline()">Propose Decline</button>
                                        </div>
                                    </div>  
                                </template>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-1"></div>
        <div class="col-md-8">
            <div class="row">
                <template v-if="canIssueDecline && isofficerfinalisation">
                    <IssueLicence :application="application" :licence_activity_tab="selected_activity_tab_id" @action-tab="actionTabListener" />
                </template>

                <ApplicationAssessments @action-tab="actionTabListener" v-if="isSendingToAssessor || showingConditions" />

                <template v-if="applicationDetailsVisible && showingApplication">
                    <div>
                    <ul class="nav nav-pills mb-3" id="tabs-main" data-tabs="tabs">
                        <li class="nav-item"><a ref="applicantTab" class="nav-link" data-toggle="pill" v-on:click="selectApplicantTab()" :href="'#'+applicantTab">Applicant</a></li>
                        <!-- <li class="nav-item"><a ref="applicationTab" class="nav-link" data-toggle="pill" :href="'#'+applicationTab">Application</a></li> -->
                        <li class="nav-item" v-for="(activity, index) in allCurrentActivities">
                            <a :class="{'nav-link amendment-highlight': application.has_amendment}"
                                data-toggle="pill" v-on:click="selectTab(activity)" :href="'#'+activityTab">{{activity.label}}</a>
                        </li>
                    </ul>
                    <div class="tab-content">
                    <div :id="applicantTab" class="tab-pane fade in active">

                    <div class="col-md-12" v-if="showingApplicant">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Applicant
                                        <a class="panelClicker" :href="'#'+detailsBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="detailsBody">
                                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                                        </a>
                                    </h3> 
                                </div>
                                <div v-if="applicantType == 'org'" class="panel-body panel-collapse collapse in" :id="detailsBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Name</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="application.org_applicant.name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >ABN/ACN</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="application.org_applicant.abn">
                                            </div>
                                          </div>
                                      </form>
                                </div>
                                <div v-if="applicantType == 'proxy'" class="panel-body panel-collapse collapse in" :id="detailsBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Given Name(s)</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="application.proxy_applicant.first_name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Surname</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="application.proxy_applicant.last_name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Date of Birth</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="application.proxy_applicant.dob">
                                            </div>
                                          </div>
                                      </form>
                                </div>
                                <div v-if="applicantType == 'submitter'" class="panel-body panel-collapse collapse in" :id="detailsBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Given Name(s)</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="application.submitter.first_name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Surname</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="application.submitter.last_name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Date of Birth</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="application.submitter.dob">
                                            </div>
                                          </div>
                                      </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-12">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Identification
                                        <a class="panelClicker" :href="'#'+identificationBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="identificationBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3>
                                </div>
                                <div v-if="applicantType == 'org' && application.org_applicant.organisation.identification" class="panel-body panel-collapse collapse" :id="identificationBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Identification</label>
                                            <div class="col-sm-8">
                                                <img width="100%" name="applicantIdentification" v-bind:src="application.org_applicant.organisation.identification" />
                                            </div>
                                          </div>
                                      </form>
                                </div>
                                <div v-if="applicantType == 'proxy' && application.proxy_applicant.identification" class="panel-body panel-collapse collapse" :id="identificationBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Identification</label>
                                            <div class="col-sm-8">
                                                <img width="100%" name="applicantIdentification" v-bind:src="application.proxy_applicant.identification" />
                                            </div>
                                          </div>
                                      </form>
                                </div>
                                <div v-if="applicantType == 'submitter' && application.submitter.identification" class="panel-body panel-collapse collapse" :id="identificationBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Identification</label>
                                            <div class="col-sm-8">
                                                <span class="btn btn-link btn-file pull-left"><SecureBaseLink link_name="Uploaded Photo ID" :link_data="{'customer_id': application.submitter.id}" /></span>
                                            </div>
                                          </div>
                                      </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-12">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Address Details
                                        <a class="panelClicker" :href="'#'+addressBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="addressBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3> 
                                </div>
                                <div v-if="applicantType == 'org' && application.org_applicant.address" class="panel-body panel-collapse collapse" :id="addressBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Street</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="street" placeholder="" v-model="application.org_applicant.address.line1">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="surburb" placeholder="" v-model="application.org_applicant.address.locality">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">State</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="country" placeholder="" v-model="application.org_applicant.address.state">
                                            </div>
                                            <label for="" class="col-sm-2 control-label">Postcode</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="postcode" placeholder="" v-model="application.org_applicant.address.postcode">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Country</label>
                                            <div class="col-sm-4">
                                                <input disabled type="text" class="form-control" name="country" v-model="application.org_applicant.address.country"/>
                                            </div>
                                          </div>
                                       </form>
                                </div>
                                <div v-if="applicantType == 'proxy' && application.proxy_applicant.residential_address" class="panel-body panel-collapse collapse" :id="addressBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Street</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="street" placeholder="" v-model="application.proxy_applicant.residential_address.line1">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="surburb" placeholder="" v-model="application.proxy_applicant.residential_address.locality">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">State</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="country" placeholder="" v-model="application.proxy_applicant.residential_address.state">
                                            </div>
                                            <label for="" class="col-sm-2 control-label">Postcode</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="postcode" placeholder="" v-model="application.proxy_applicant.residential_address.postcode">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Country</label>
                                            <div class="col-sm-4">
                                                <input disabled type="text" class="form-control" name="country" v-model="application.proxy_applicant.residential_address.country"/>
                                            </div>
                                          </div>
                                       </form>
                                </div>
                                <div v-if="applicantType == 'submitter' && application.submitter.residential_address" class="panel-body panel-collapse collapse" :id="addressBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Street</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="street" placeholder="" v-model="application.submitter.residential_address.line1">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="surburb" placeholder="" v-model="application.submitter.residential_address.locality">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">State</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="country" placeholder="" v-model="application.submitter.residential_address.state">
                                            </div>
                                            <label for="" class="col-sm-2 control-label">Postcode</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="postcode" placeholder="" v-model="application.submitter.residential_address.postcode">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Country</label>
                                            <div class="col-sm-4">
                                                <input disabled type="text" class="form-control" name="country" v-model="application.submitter.residential_address.country"/>
                                            </div>
                                          </div>
                                       </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-12">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Contact Details
                                        <a class="panelClicker" :href="'#'+contactsBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="contactsBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3>
                                </div>
                                <div v-if="applicantType == 'org'" class="panel-body panel-collapse collapse" :id="contactsBody">
                                    <table ref="contacts_datatable" :id="contacts_table_id" class="hover table table-striped table-bordered dt-responsive" cellspacing="0" width="100%">
                                    </table>
                                </div>
                                <div v-if="applicantType == 'proxy'" class="panel-body panel-collapse collapse" :id="contactsBody">
                                  <form class="form-horizontal">
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Phone</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantPhoneNumber" placeholder="" v-model="application.proxy_applicant.phone_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Mobile</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantMobileNumber" placeholder="" v-model="application.proxy_applicant.mobile_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Email</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantEmail" placeholder="" v-model="application.proxy_applicant.email">
                                        </div>
                                      </div>
                                  </form>
                                </div>
                                <div v-if="applicantType == 'submitter'" class="panel-body panel-collapse collapse" :id="contactsBody">
                                  <form class="form-horizontal">
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Phone</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantPhoneNumber" placeholder="" v-model="application.submitter.phone_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Mobile</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantMobileNumber" placeholder="" v-model="application.submitter.mobile_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Email</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantEmail" placeholder="" v-model="application.submitter.email">
                                        </div>
                                      </div>
                                  </form>
                                </div>

                            </div>
                        </div>
                    </div>
                    <div class="col-md-12">
                        <div class ="row">
                        <div class="panel panel-default">
                            <div class="panel-heading">
                                <h3 class="panel-title">Check List
                                    <a class="panelClicker" :href="'#'+checksBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="checksBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                    </a>
                                </h3>

                            </div>
                            <div class="panel-body panel-collapse collapse" :id="checksBody">
                                <div class="row">
                                    <div class="col-sm-4">ID Check</div>
                                    <div class="col-sm-4">
                                        <button v-if="isIdNotChecked || isIdCheckUpdated" class="btn btn-primary" @click.prevent="acceptIdRequest()">Accept</button>
                                        <button v-if="isIdCheckAccepted" disabled class="btn btn-light">Accepted</button>
                                        <button v-if="isIdCheckRequested" disabled class="btn btn-light">Awaiting Update</button>
                                    </div>
                                    <div class="col-sm-4">
                                        <button v-if="isIdNotChecked" :disabled="application.proxy_applicant" class="btn btn-primary" @click.prevent="updateIdRequest()">Request Update</button>
                                        <button v-if="isIdCheckUpdated" disabled class="btn btn-light">Request updated</button>
                                        <button v-if="isIdCheckAccepted || isIdCheckRequested"  class="btn btn-primary" @click.prevent="resetIdRequest()">Reset</button>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-4">Character Check</div>
                                    <div class="col-sm-4">
                                        <button v-if="!isCharacterCheckAccepted" class="btn btn-primary" @click.prevent="acceptCharacterRequest()">Accept</button>
                                        <button v-if="isCharacterCheckAccepted" disabled class="btn btn-light">Accepted</button>
                                    </div>
                                    <div class="col-sm-4">
                                        <button v-if="isCharacterCheckAccepted" @click.prevent="resetCharacterRequest()" class="btn btn-primary">Reset</button>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-sm-4">Returns Check</div>
                                    <div class="col-sm-4">
                                        <button v-show="showReturnCheckButton" class="btn btn-primary" @click.prevent="acceptReturnRequest()">Accept</button>
                                        <button v-show="!showReturnCheckButton" disabled class="btn btn-light">Accepted</button>
                                    </div>
                                    <div class="col-sm-4">
                                        <button v-show="!showReturnCheckButton" @click.prevent="resetReturnRequest()" class="btn btn-primary">Reset</button>
                                    </div>
                                </div>
                            </div>


                        </div>
                    </div>


                    </div>
                </div>

                <div :id="activityTab" class="tab-pane fade">
                    <div class="col-md-12">
                        <div class="row">
                            <form :action="application_form_url" method="post" name="new_application" enctype="multipart/form-data">
                                <Application form_width="inherit" :withSectionsSelector="false" v-if="isApplicationLoaded && !showingApplicant">
                                    <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
                                    <input type='hidden' name="schema" :value="JSON.stringify(application)" />
                                    <input type='hidden' name="application_id" :value="1" />
                                    <input type='hidden' id="selected_activity_tab_id" v-model="selected_activity_tab_id" />

                                    <div v-for="(activity, index) in allCurrentActivities">
                                        <AmendmentRequestDetails :activity_id="activity.id" />
                                        <renderer-block
                                            :component="activity"
                                            v-if="activity.id == selected_activity_tab_id"
                                            v-bind:key="`renderer_block_${index}`"
                                            />
                                    </div>
                                    {{ this.$slots.default }}

                                    <div v-if="showNavBarBottom" class="row" style="margin-bottom:50px;">
                                        <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                                            <div class="navbar-inner">
                                                <div class="container">
                                                    <p class="pull-right" style="margin-top:5px;">
                                                        <span style="margin-right: 5px; font-size: 18px; display: block;" v-if="updatedFee" >
                                                            <strong>Updated application fee: {{application.application_fee | toCurrency}}</strong>
                                                            <strong>licence fee: {{application.licence_fee | toCurrency}}</strong>
                                                        </span>
                                                        <button v-if="showSpinner && showRequestSpinner" type="button" disabled class="btn btn-primary" >Save Changes</button> 
                                                        <button v-else-if="showSpinner && !showRequestSpinner" type="button" class="btn btn-primary" ><i class="fa fa-spinner fa-spin"/>Saving</button>                                                    
                                                        <button v-else="!applicationIsDraft && canSaveApplication" class="btn btn-primary" @click.prevent="save_button()">Save Changes</button>
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </Application>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </template>

    <!-- Final Decision display -->
    <div v-show="showFinalDecision">
        <div class="row">
            <div class="col-md-12 alert alert-success" v-if="application.processing_status.name === 'Approved'">
                <p>The licence has been issued and has been emailed to {{ application.applicant }}.</p>
                <p>Licence: <a :href="application.permit" target="_blank" >licence.pdf</a></p>
            </div>
            <div class="col-md-12 alert alert-danger" v-if="application.processing_status.name !== 'Approved'">
                <p>The application is not approved. An update to the status was emailed to {{application.applicant}}</p>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">          
                <div class="row">
                    <div class="panel panel-default">
                        <div class="panel-heading">
                            <h3 class="panel-title">Decision
                                <a class="panelClicker" :href="'#'+decisionBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="decisionBody">
                                    <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                </a>
                            </h3>
                        </div>
                        <div class="panel-body panel-collapse collapse" :id="decisionBody">
                            <div v-for="activity in application.activities.filter(activity => ['issue_refund','issued'].includes(activity.decision_action))">
                                <div class="col-sm-12">
                                    <strong>&nbsp;</strong><br/>
                                    <strong>Licence Activity: {{ activity.activity_name_str }}</strong><br/>
                                    <strong>Decision: {{ activity.processing_status.id === 'declined' ? activity.processing_status.name : activity.decision_action }}</strong><br/>
                                    <strong>Start date: {{ activity.processing_status.id === 'declined' ? '' : activity.start_date | formatDateNoTime }}</strong><br/>
                                    <strong>Expiry date: {{ activity.processing_status.id === 'declined' ? '' : activity.expiry_date | formatDateNoTime }}</strong>                                    
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
    <!-- End of Final Decision Display -->

    </div>
    </div>   
    </div>
    <ProposedDecline ref="proposed_decline" @refreshFromResponse="refreshFromResponse"></ProposedDecline>
    <AmendmentRequest ref="amendment_request" @refreshFromResponse="refreshFromResponse"></AmendmentRequest>
    <ProposedLicence ref="proposed_licence" @refreshFromResponse="refreshFromResponse" :can_view_richtext_src="application.can_view_richtext_src"></ProposedLicence>

    </div>
    <div v-else>
        <br/><br/><br/><br/><br/><br/><br/><br/>
        <div class="col-md-12">
            <center><i class="fa fa-4x fa-spinner fa-spin"/></center>
        </div>
    </div>

</div>
</template>
<script>
import Application from '../../form.vue';
import Vue from 'vue';
import { mapActions, mapGetters } from 'vuex'
import ProposedDecline from './application_proposed_decline.vue';
import AmendmentRequest from './amendment_request.vue';
import ApplicationAssessments from './application_assessments.vue';
import datatable from '@vue-utils/datatable.vue';
import ProposedLicence from './proposed_issuance.vue';
import IssueLicence from './application_issuance.vue';
import CommsLogs from '@common-components/comms_logs.vue';
import AmendmentRequestDetails from '@/components/forms/amendment_request_details.vue';
import SecureBaseLink from '@common-components/securebase_link.vue';
import ResponsiveDatatablesHelper from "@/utils/responsive_datatable_helper.js";
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
export default {
    name: 'InternalApplication',
    data: function() {
        let vm = this;
        return {
            applicantTab: 'applicantTab'+vm._uid,
            applicationTab: 'applicationTab'+vm._uid,
            activityTab: 'activityTab'+vm._uid+'_'+0,
            detailsBody: 'detailsBody'+vm._uid,
            identificationBody: 'identificationBody'+vm._uid,
            addressBody: 'addressBody'+vm._uid,
            contactsBody: 'contactsBody'+vm._uid,
            checksBody: 'checksBody'+vm._uid,
            decisionBody: 'decisionBody'+vm._uid,
            isSendingToAssessor: false,
            notOfficerWorkflow: false,
            assessorGroup:{},
            "selectedAssessor":{},
            "loading": [],
            form: null,
            // activity_data:[],
            contacts_table_initialised: false,
            initialisedSelects: false,
            showingApplication:true,
            showingApplicant:false,
            showingConditions:false,
            isofficerfinalisation:false,
            approvingApplication:false,
            contacts_table_id: vm._uid+'contacts-table',
            application_assessor_datatable:vm._uid+'assessment-table',
            spinner: false,
            request_spinner: false,
            condition_spinner: false,
            contacts_options:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": vm.contactsURL,
                    "dataSrc": ''
                },
                columns: [
                    {
                        title: 'Name',
                        data:'last_name',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {
                        title: 'Phone',
                        data:'phone_number'
                    },
                    {
                        title: 'Mobile',
                        data:'mobile_number'
                    },
                    {
                        title: 'Fax',
                        data:'fax_number'
                    },
                    {
                        title: 'Email',
                        data:'email'
                    },
                  ],
                  processing: true
            },
            contacts_table: null,
            assessors_headers:["Assessor Group","Date Sent","Status","Action"],
            assessors_options:{},
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            comms_url: helpers.add_endpoint_json(api_endpoints.applications,vm.$route.params.application_id+'/comms_log'),
            comms_add_url: helpers.add_endpoint_json(api_endpoints.applications,vm.$route.params.application_id+'/add_comms_log'),
            logs_url: helpers.add_endpoint_json(api_endpoints.applications,vm.$route.params.application_id+'/action_log'),
            panelClickersInitialised: false,
            hasActionedConditionLink: false,
            hasActionedApplicationLink: false,
            hasActionedActivityTab: false,
            missing_fields: [],
        }
    },
    components: {
        Application,
        datatable,
        ProposedDecline,
        AmendmentRequest,
        ApplicationAssessments,
        ProposedLicence,
        IssueLicence,
        CommsLogs,
        AmendmentRequestDetails,
        SecureBaseLink,
    },
    filters: {
        formatDate: function(data){
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss'): '';
        },
        formatDateNoTime: function(data){
            return data ? moment(data).format('DD/MM/YYYY'): '';
        },       
    },
    watch: {
    },
    computed: {
        ...mapGetters([
            'application',
            'original_application',
            'licence_type_data',
            'selected_activity_tab_id',
            'selected_activity_tab_name',
            'hasRole',
            'visibleConditionsFor',
            'checkActivityStatus',
            'isPartiallyFinalised',
            'isFinalised',
            'licenceActivities',
            'isApplicationLoaded',
            'isApplicationActivityVisible',
            'unfinishedActivities',
            'current_user',
            'canAssignApproverFor',
            'canEditAssessmentFor',
            'canRequestAmendmentFor',
            'canAssignOfficerFor',
            'canAssignAssessorFor',
            'id_check_status',
            'character_check_status',
            'return_check_status',
            'hasCurrentLicence',
            'allCurrentActivities',
            'selected_activity_tab_workflow_state',
            'application_workflow_state',
        ]),
        applicationDetailsVisible: function() {

            return !this.isSendingToAssessor && !this.isofficerfinalisation && this.unfinishedActivities.length && !this.showingConditions;
        },
        applicationIsDraft: function(){
            return this.application.processing_status.id == 'draft';
        },
        selectedActivity: function(){
            // Function that returns an Application Selected Activity.
            if (this.selected_activity_tab_id == null || this.selected_activity_tab_id<1) {

                this.initFirstTab()     // Each Tab is a Licence Activity.
            }
            let selected = this.application.activities.find(activity => {

                return activity.licence_activity === this.selected_activity_tab_id                
            })
            return selected;
        },
        canIssueDecline: function(){
            if (this.showingApplicant) {
                return false;
            }

            if (this.selectedActivity.processing_status.id=='awaiting_licence_fee_payment') {
                return false;
            }
            // check user is authorised to issue/allocate for selected activity.
            if (!this.canAssignApproverFor(this.selected_activity_tab_id)) {
                return false;
            };
            // check activity is not assigned to another approver.
            if (this.selectedActivity.assigned_approver != null && parseInt(this.selectedActivity.assigned_approver) !== parseInt(this.current_user.id)) {
                return false;
            };
            // set link/button flags to match the tabs workflow.
            if (this.selectedActivity.processing_status.id=='with_officer_finalisation') {
                this.approvingApplication = true;
                this.showingConditions = !this.showingApplication && !this.isofficerfinalisation;
            }
            return true;
        },
        canSaveApplication: function() {
            // Assessors can save the Assessor Comments field.
            if(this.selected_activity_tab_id &&
                this.userHasRole('assessor', this.selected_activity_tab_id) &&
                this.selectedActivity.processing_status.id == 'with_assessor') {
                    return true;
            }
            let workflow = ['with_officer'].includes(this.selectedActivity.processing_status.id)
            if (!workflow || !this.selectedActivity) {
                return false;
            }

            // Licensing officers can save officer comments.
            return this.canRequestAmendment;
        },
        canRequestAmendment: function(){
            // check activity is not assigned to another officer.
            if (this.selectedActivity.assigned_officer != null && this.selectedActivity.assigned_officer !== this.current_user.id) {
                return false;
            }
            // check activity is not reissued.
            if (this.selectedActivity.decision_action === 'reissue'){
                return false;
            }
            // check authorisation
            return this.canRequestAmendmentFor(this.selected_activity_tab_id);
        },
        canReturnToConditions: function(){
            // required when issuing or declining.
            let can_return = this.canIssueDecline;

            if (!this.showingApplication && this.showingConditions) {
                can_return = false;
            }

            return can_return;
        },
        canProposeIssueOrDecline: function(){
            let auth_activity = this.canAssignOfficerFor(this.selected_activity_tab_id);

            // check activity is not assigned to another officer.
            if (auth_activity && auth_activity.assigned_officer != null && auth_activity.assigned_officer !== this.current_user.id) {
                return false;
            }

            let proposal = auth_activity && auth_activity.is_with_officer && this.licence_type_data.activity.find(activity => {
                    return activity.id === this.selected_activity_tab_id
                        && activity.processing_status.name.match(/with officer/gi) // FIXME: required because of temporary status set below.
                });                                                                // processing_status.id not related to processing_status.name

            //if (this.selected_activity_tab_workflow_state[this.selected_activity_tab_id] || !this.hasCurrentLicence){
            if (this.selected_activity_tab_workflow_state[this.selected_activity_tab_id]){
                // presentation frontend state is incomplete or no valid licence.
                proposal = false;
            }
            // officer can Issue or Decline without conditions so set temporary status.
            return proposal ? proposal.processing_status.id = 'with_officer_conditions' : false;
        },
        canProposeToOnlyDecline: function() {
            let decline_proposal = !this.hasCurrentLicence || this.selected_activity_tab_workflow_state[this.selected_activity_tab_id];

            if (this.selectedActivity.processing_status.id === 'declined') {
                return false;
            }
            if (this.selectedActivity.processing_status.id === 'with_assessor') {
                return false;
            }
            if (this.selectedActivity.processing_status.id === 'draft') {
                return false;
            }

            if (this.canProposeIssueOrDecline) {
                decline_proposal = false;
            }
            return decline_proposal;
        },
        contactsURL: function(){
            return this.application!= null ? helpers.add_endpoint_json(api_endpoints.organisations,this.application.org_applicant.id+'/contacts') : '';
        },
        applicantType: function(){
            return this.$store.getters.applicant_type;
        },
        isLoading: function() {
          return this.loading.length > 0
        },
        csrf_token: function() {
          return helpers.getCookie('csrftoken')
        },
        application_form_url: function() {
          return (this.application) ? `/api/application/${this.application.id}/application_officer_save.json` : '';
        },
        isIdCheckAccepted: function(){
            return this.id_check_status === 'accepted';
        },
        isIdNotChecked: function(){
            return this.id_check_status === 'not_checked';
        },
        isIdCheckRequested: function(){
            return this.id_check_status === 'awaiting_update';
        },
        isIdCheckUpdated: function(){
            return this.id_check_status === 'updated';
        },
        isCharacterCheckAccepted: function(){
            return this.character_check_status === 'accepted';
        },
        userIsAssignedOfficer: function(){
            return this.current_user.id == this.selectedActivity.assigned_officer;
        },
        form_data_comments_url: function() {
            return (this.application) ? `/api/application/${this.application.id}/officer_comments.json` : '';
        },
        form_data_application_url: function() {
            return (this.application) ? `/api/application/${this.application.id}/form_data.json` : '';
        },
        headerLabel: function() {
            switch(this.application.application_type.id) {
                case 'amend_activity':
                    return 'Application - Activity Amendment';
                break;
                case 'renew_activity':
                    return 'Application - Activity Renewal';
                break;
                default:
                    return 'Application'
                break;
            }
        },
        updatedFee: function() {
            return (this.application.application_fee !== 0 || this.application.licence_fee !== 0) ? true : false
        },
        showNavBarBottom: function() {
            // let show = this.canReturnToConditions || (!this.applicationIsDraft && this.canSaveApplication)
            let show = !this.applicationIsDraft && this.canSaveApplication
            return show
        },
        showAssignToOfficer: function(){
            if (this.showingApplicant) {
                return false;
            }

            let workflow_officer = ['with_officer','with_officer_conditions'].includes(this.selectedActivity.processing_status.id)
            if (!workflow_officer) {
                return false;
            }

            return this.isSendingToAssessor || this.showingConditions || this.showingApplication;
        },
        showAssignToApprover: function(){
            let show = !this.showingApplication && this.canAssignApproverFor(this.selectedActivity.licence_activity);

            if (this.showingApplication || this.showingConditions) {
                return false;
            }

            return show;
        },
        showAssessmentConditionButton: function() {
            if (this.showingApplicant) {
                return false;
            }
            let workflow_officer = ['with_officer','with_officer_conditions'].includes(this.selectedActivity.processing_status.id)
            let workflow_assessor = ['with_assessor'].includes(this.selectedActivity.processing_status.id)
            if (!workflow_officer && !workflow_assessor) {
                return false;
            }
            if (workflow_officer && !this.canAssignOfficerFor(this.selectedActivity.licence_activity)) {
                return false;
            }
            if (workflow_assessor) {
                return false;
            }

            return this.showingApplication && !this.applicationIsDraft;
        },
        showIssueDeclineButton: function() {

            if (this.showingApplicant) {
                return false;
            }

            if (this.selectedActivity.processing_status.id=='awaiting_licence_fee_payment') {
                return false;
            }

            // check user is authorised to issue/allocate for selected activity.
            if (!this.canAssignApproverFor(this.selected_activity_tab_id)) {
                return false;
            };
            // check activity is not assigned to another approver.
            if (this.selectedActivity.assigned_approver != null && this.selectedActivity.assigned_approver !== this.current_user.id) {
                return false;
            };

            // check correct workflow.
            if (this.approvingApplication) {
                return false;
            }

            return true;
        },
        showFinalDecisionOriginal: function() {
            let show_final = (!this.showingApplication || !this.unfinishedActivities.length) && !this.isSendingToAssessor && !this.canIssueDecline && !this.showingConditions
            if (['awaiting_payment'].includes(this.application.processing_status.id)) { // prevent processing for outstanding payments.
                this.toggleApplication({show: false})
                this.isSendingToAssessor=false
            }
            if (show_final) {this.showingApplication=false}
            return show_final
        },
        showFinalDecision: function() {
            let show_final=false;

            if(!this.unfinishedActivities.length){
                show_final = (!this.showingApplication || !this.unfinishedActivities.length) && !this.isSendingToAssessor && !this.canIssueDecline && !this.showingConditions
            }
            if (['awaiting_payment'].includes(this.application.processing_status.id)) { // prevent processing for outstanding payments.
                this.toggleApplication({show: false})
                this.isSendingToAssessor=false
            }
            if (show_final) {this.showingApplication=false}
            return show_final
        },
        showSpinner: function() {
            return this.spinner
        },
        showRequestSpinner: function() {
            return this.request_spinner
        },
        showConditionSpinner: function() {
            return this.condition_spinner
        },
        showReturnCheckButton: function() {
            // return this.application.is_return_check_accept ? false : true
            return this.return_check_status !== 'accepted';
        },
        showBackToProcessingButton: function() {
            let show = this.isSendingToAssessor || this.showingConditions;
            if (this.selectedActivity.processing_status.id === 'declined') {
                return false;
            }
            if (this.selectedActivity.processing_status.id === 'with_officer_finalisation') {
                return false;
            }
            if (this.selectedActivity.processing_status.id === 'accepted') {
                return false;
            }
            if (this.selectedActivity.processing_status.id === 'with_assessor') {
                return false;
            }
            if (this.selectedActivity.processing_status.id === 'draft') {
                return false;
            }

            return show
        },
        showRequestAmendmentButton: function() {
            let show = !this.applicationIsDraft && this.canRequestAmendment;

            if (this.selectedActivity.processing_status.id !== 'with_officer') {
                return false;
            }

            if (this.showingApplicant) {
                return false;
            }

            return show
        },
    },
    methods: {
        ...mapActions({
            load: 'loadApplication',
            revert: 'revertApplication',
        }),
        ...mapActions([
            'setOriginalApplication',
            'setApplication',
            'setActivityTab',
            'loadCurrentUser',
            'toggleFinalisedTabs',
            'saveFormData',
            'assessmentData',
            'setIdCheckStatus',
            'setCharacterCheckStatus',
            'setReturnCheckStatus',
            'resetUpdateFeeStatus',
            'setAssessStatus',
            'setLicenceTypeData',
            'setActivityTabWorkflowState',
        ]),
        selectTab: function(component) {
            this.section_tab_id = component.id;
            this.setActivityTab({id: component.id, name: component.label});
            this.showingApplicant = false;
            this.setActivityTabWorkflowState({ tab_id: component.id, bool: !this.selectedActivity.can_propose_purposes} )
            this.actionActivityTab(this.selectedActivity)
        },
        selectApplicantTab: function() {
            this.showingApplicant = true;
        },
        userHasRole: function(role, activity_id) {
            return this.hasRole(role, activity_id);
        },
        getVisibleConditionsFor: function(for_role, processing_status, tab_id) {
            return this.visibleConditionsFor(for_role, processing_status, tab_id);
        },
        initFirstTab: function(force){
            if(this.selected_activity_tab_id && !force) {
                return;
            }
            // const tab = $('#tabs-section li:first-child a')[0];
            const tab = $('#tabs-main li')
            if(tab.length>0) {

                let tabno = 0;
                for(let i=0; i<tab.length; i++){
                    if (tab[i].innerText === this.selected_activity_tab_name) {
                        tabno = i
                    }
                }
                var selected = $('#tabs-main li a')[tabno]

                if (this.showingApplicant) {
                    selected = $('#tabs-main li a')[0]
                }
    
                if (selected) {
                    selected.click();
                }
            }
            else {
                this.licenceActivities().filter(activity => {
                    this.setActivityTab({
                        id: activity.id,
                        name: activity.name
                    });
                })
            }
        },
        initialiseOrgContactTable: function(){
            let vm = this;
            if (vm.application && vm.applicantType == 'org' && !vm.contacts_table_initialised){
                vm.contacts_options.ajax.url = helpers.add_endpoint_json(api_endpoints.organisations,vm.application.org_applicant.id+'/contacts');
                vm.contacts_table = $('#'+vm.contacts_table_id).DataTable(vm.contacts_options);
                vm.contacts_table_initialised = true;
            }
        },
        commaToNewline(s){
            return s.replace(/[,;]/g, '\n');
        },
        proposedDecline: async function(){
            this.$refs.proposed_decline.noActiveLicense = !this.hasCurrentLicence;
            this.$refs.proposed_decline.isModalOpen = true;
        },
        isActivityVisible: function(activity_id) {
            return this.isApplicationActivityVisible({activity_id: activity_id});
        },
        hasActivityStatus: function(status_list, status_count=1, required_role=null) {
            return this.checkActivityStatus(status_list, status_count, required_role);
        },
        proposedLicence: async function(){
            var activity_name=[]
            var selectedTabTitle = $("#tabs-main li.active");
            this.$refs.proposed_licence.propose_issue.licence_activity_id=this.selected_activity_tab_id;
            this.$refs.proposed_licence.propose_issue.licence_activity_name=selectedTabTitle.text();
            this.$refs.proposed_licence.isModalOpen = true;
            this.$refs.proposed_licence.preloadLastActivity();
        },
        toggleIssue: async function(){
            this.showingApplication = false;
           
            if(this.selectedActivity.processing_status.id==='with_assessor') {

                this.approvingApplication=false;
                this.isofficerfinalisation=false;

                this.showingConditions = true;
                this.notOfficerWorkflow=true;
                this.isSendingToAssessor=true;

            } else {

                this.approvingApplication=true;
                this.isofficerfinalisation=true;

                this.showingConditions=false;
                this.notOfficerWorkflow=false;
                this.isSendingToAssessor=false;
            }

            setTimeout(() => {
                let main_tabs = $('#tabs-main li')
                let tabno = 0;
                for(let i=0; i<main_tabs.length; i++){
                    if (main_tabs[i].innerText === this.selected_activity_tab_name) {
                        tabno = i
                    }
                }
                const selected = $('#tabs-main li a')[tabno]
                if(selected != null) {
                    selected.click();
                }
                this.initFirstTab();
            }, 50);

        },
        acceptIdRequest: async function() {
            let vm = this;
            swal({
                title: "Accept ID Check",
                text: "Are you sure you want to accept this ID Check?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/accept_id_check')))
                    .then((response) => {
                        vm.setIdCheckStatus(response.body.id_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        resetIdRequest: async function() {
            let vm = this;
            swal({
                title: "Reset ID Check",
                text: "Are you sure you want to reset this ID Check?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/reset_id_check')))
                    .then((response) => {
                        vm.setIdCheckStatus(response.body.id_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        updateIdRequest: async function() {
            let vm = this;
            swal({
                title: "Request Update ID Check",
                text: "Are you sure you want to request this ID Check update?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/request_id_check')))
                    .then((response) => {
                        vm.setIdCheckStatus(response.body.id_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        acceptCharacterRequest: async function() {
            let vm = this;
            swal({
                title: "Accept Character Check",
                text: "Are you sure you want to accept this Character Check?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/accept_character_check')))
                    .then((response) => {
                        vm.setCharacterCheckStatus(response.body.character_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        resetCharacterRequest: async function() {
            let vm = this;
            swal({
                title: "Reset Character Check",
                text: "Are you sure you want to reset this Character Check?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/reset_character_check')))
                    .then((response) => {
                        vm.setCharacterCheckStatus(response.body.character_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        acceptReturnRequest: async function() {
            let vm = this;
            swal({
                title: "Accept Return Check",
                text: "Are you sure you want to accept this Return Check?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/accept_return_check')))
                    .then((response) => {
                        vm.setReturnCheckStatus(response.body.return_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        resetReturnRequest: async function() {
            let vm = this;
            swal({
                title: "Reset Return Check",
                text: "Are you sure you want to reset this Return Check?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then(async (result) => {
                if (result.value) {
                    await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/reset_return_check')))
                    .then((response) => {
                        vm.setReturnCheckStatus(response.body.return_check_status);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        save: async function(props = { showNotification: true }) {
            this.spinner = true;
            const { showNotification } = props;

            this.missing_fields.length = 0;
            this.highlight_missing_fields();

            await this.saveFormData({ url: this.form_data_application_url }).then(response => {
                // this.spinner = false;
                this.resetUpdateFeeStatus();
                showNotification && swal(
                    'Saved',
                    'Your application has been saved',
                    'success'
                )     
            }, error => {

                if (error.body.hasOwnProperty("missing")){

                    for (const missing_field of error.body.missing) {
                        this.missing_fields.push(missing_field)
                    }
                    this.highlight_missing_fields()
                    var top = ($('#error').offset() || { "top": NaN }).top;
                    $('html, body').animate({
                        scrollTop: top
                    }, 1);
                    return false;
                }
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });

        },
        highlight_missing_fields: function(){
            $('.missing-field').removeClass('missing-field');
            for (const missing_field of this.missing_fields) {
                $(`[name=${missing_field.name}`).addClass('missing-field');
            }
            var top = ($('#error').offset() || { "top": NaN }).top;
            $('html, body').animate({
                scrollTop: top
            }, 1);
        },
        save_button: async function() {
            await this.save()
            this.spinner = false;
        },
        save_wo: async function() {
            await this.save({ showNotification: false });
            return true
        },
        toggleApplicant: function(){
            let show_final = ['approved','declined','partially_approved','awaiting_payment'].includes(this.application.processing_status.id) && !this.unfinishedActivities.length
            if (!this.showingApplication && show_final){
                this.toggleApplication({show: true, showFinalised: true});
            }
            this.showingApplicant=true;
            this.showingApplication=true;

            setTimeout(() => {
                const selected = $('#tabs-main li a')[0]
                if(selected != null) {
                    selected.click();
                }
            }, 50);
        },
        toggleApplication: function({show=false, showFinalised=false}){
            this.showingApplication = show;
            if(this.isSendingToAssessor){
                this.isSendingToAssessor = !show;
            }
            if(this.showingConditions){

                this.showingConditions = !show;

                if(this.selectedActivity.processing_status.id==='with_assessor') {

                    this.notOfficerWorkflow=true;
                }
            }
            if(this.isofficerfinalisation){
                this.approvingApplication = true;
                // this.isofficerfinalisation = !show;
            }
            this.toggleFinalisedTabs(showFinalised);
            setTimeout(() => {
                // const firstTab = $('#tabs-main li a')[0];
                let main_tabs = $('#tabs-main li')
                let tabno = 0;
                for(let i=0; i<main_tabs.length; i++){
                    if (main_tabs[i].innerText === this.selected_activity_tab_name) {
                        tabno = i
                    }
                }
                const selected = $('#tabs-main li a')[tabno]
                if(selected != null) {
                    selected.click();
                }
                this.initFirstTab();
            }, 50);
            !showFinalised && this.load({ url: `/api/application/${this.application.id}/internal_application.json` });
        },
        toggleConditions: async function({show=false, showFinalised=false}){
            this.showingConditions = show;

            if (showFinalised) {
                this.toggleApplication({show: false, showFinalised: showFinalised});
                return
            }

            if (this.showingConditions) {
                this.toggleApplication({show: false})
                this.condition_spinner = true;
                await this.assessmentData({ url: `/api/application/${this.application.id}/assessment_data.json` }).then( async response => {

                    this.condition_spinner = false;
                    this.spinner = false;
                    this.setAssessStatus(false);

                },(error)=>{

                    this.condition_spinner = false;
                    this.spinner = false;
                    console.log(error)
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            } else {
                this.toggleApplication({show: true, showFinalised: true})
            }
        },
        toggleOfficerConditions: async function(){
            this.isSendingToAssessor = !this.isSendingToAssessor;



            this.approvingApplication = false;
            this.isofficerfinalisation = false;

            this.showingApplication = false;


            this.condition_spinner = true;

            if (!this.hasActionedConditionLink && !this.hasActionedApplicationLink) { 

                await this.assessmentData({ url: `/api/application/${this.application.id}/assessment_data.json` }).then( async response => {

                    this.condition_spinner = false;
                    this.spinner = false;
                    this.setAssessStatus(false);

                },(error)=>{

                    this.condition_spinner = false;
                    this.spinner = false;
                    console.log(error)
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }

            this.showingConditions = true;  
        },
        updateAssignedOfficerSelect:function(){
            let vm = this;
            $(vm.$refs.assigned_officer).val(vm.selectedActivity.assigned_officer);
            $(vm.$refs.assigned_officer).trigger('change');
        },
        assignToMe: async function(){
            let vm = this;
            vm.selectedActivity.assigned_officer = vm.current_user.id
            $(vm.$refs.assigned_officer).val(vm.current_user.id);
            $(vm.$refs.assigned_offcier).trigger('change');
            const data = {
                "activity_id" : this.selectedActivity.licence_activity,
            }
            await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/assign_to_me')),JSON.stringify(data),{
                emulateJSON:true

            }).then((response) => {
                // this.refreshFromResponse(response);
                // vm.updateAssignedOfficerSelect();
            }, (error) => {
                vm.revert();
                vm.updateAssignedOfficerSelect();
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
        updateAssignedApproverSelect:function(){
            let vm = this;
            $(vm.$refs.assigned_approver).val(vm.selectedActivity.assigned_approver);
            $(vm.$refs.assigned_approver).trigger('change');
        },
        refreshFromResponse:function(response){
            this.setOriginalApplication(response.body);
            this.setApplication(response.body);
            this.$nextTick(() => {
                this.initialiseAssignedOfficerSelect(true);
                this.updateAssignedOfficerSelect();
            });
        },
        assignOfficer: async function(){
            let vm = this;
            let unassign = true;
            let data = {};
            unassign = vm.selectedActivity.assigned_officer != null && vm.selectedActivity.assigned_officer != 'undefined' ? false: true;
            data = {
                'officer_id': vm.selectedActivity.assigned_officer,
                "activity_id" : this.selectedActivity.licence_activity,
            };
            if (!unassign){
                await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/assign_officer')),JSON.stringify(data),{
                    emulateJSON:true
                }).then((response) => {
                    // this.refreshFromResponse(response);
                    // this.updateAssignedOfficerSelect();
                }, (error) => {
                    this.revert();
                    this.updateAssignedOfficerSelect();
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
            else{
                await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/unassign_officer')),JSON.stringify(data),{
                    emulateJSON:true
                }).then((response) => {
                    // this.refreshFromResponse(response);
                    // this.updateAssignedOfficerSelect();
                }, (error) => {
                    this.revert();
                    this.updateAssignedOfficerSelect();
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
        },
        assignApprover: async function(){
            let vm = this;
            let unassign = true;
            unassign = vm.selectedActivity.assigned_approver == null ? true: false;

            const data = {
                "activity_id" : this.selectedActivity.licence_activity,
                "approver_id" : this.selectedActivity.assigned_approver,
            }

            if (!unassign){
                await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/assign_activity_approver')),JSON.stringify(data),{
                    emulateJSON:true
                }).then((response) => {
                    // this.refreshFromResponse(response);
                    // this.updateAssignedApproverSelect();
                }, (error) => {
                    this.revert();
                    this.updateAssignedApproverSelect();
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
            else{
                await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/unassign_activity_approver')),JSON.stringify(data),{
                    emulateJSON:true
                }).then((response) => {
                    // this.refreshFromResponse(response);
                    // this.updateAssignedOfficerSelect();
                }, (error) => {
                    this.revert();
                    this.updateAssignedOfficerSelect();
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
        },
        makeMeApprover: async function(){
            let vm = this;
            vm.selectedActivity.assigned_approver = vm.current_user.id
            $(vm.$refs.assigned_approver).val(vm.current_user.id);
            $(vm.$refs.assigned_approver).trigger('change');
            const data = {
                "activity_id" : this.selectedActivity.licence_activity,
            }
            await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/make_me_activity_approver')),JSON.stringify(data),{
                emulateJSON:true

            }).then((response) => {
                // this.refreshFromResponse(response);
                // this.updateAssignedApproverSelect();
            }, (error) => {
                this.revert();
                this.updateAssignedApproverSelect();
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
        updateActivityStatus: async function(activity_id, status){
            let vm = this;
            let data = {
                'activity_id' : activity_id,
                'status': status
            }
            await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/update_activity_status')),JSON.stringify(data),{
                emulateJSON:true,
            }).then((response) => {
                this.refreshFromResponse(response);
            }, (error) => {
                this.revert();
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
        initialiseAssignedOfficerSelect: function(reinit=false){
            let vm = this;
            if (reinit){
                $(vm.$refs.assigned_officer).data('select2') ? $(vm.$refs.assigned_officer).select2('destroy'): '';
            }
            // Assigned officer select
            $(vm.$refs.assigned_officer).select2({
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Officer"
            }).
            on("select2:select",function (e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var selected = $(e.currentTarget);
                vm.selectedActivity.assigned_officer = selected.val();
                vm.assignOfficer();
            }).on("select2:unselecting", function(e) {
                var self = $(this);
                setTimeout(() => {
                    self.select2('close');
                }, 0);
            }).on("select2:unselect",function (e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var selected = $(e.currentTarget);
                vm.selectedActivity.assigned_officer = null;
                vm.assignOfficer();
            });
        },
        initialiseAssignedApproverSelect: function(reinit=false){
            let vm = this;
            if (reinit){
                $(vm.$refs.assigned_approver).data('select2') ? $(vm.$refs.assigned_approver).select2('destroy'): '';
            }
            // Assigned approver select
            $(vm.$refs.assigned_approver).select2({
                theme: "bootstrap",
                allowClear: true,
                placeholder: "Select Approver"
            }).
            on("select2:select",function (e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var selected = $(e.currentTarget);
                vm.selectedActivity.assigned_approver = selected.val();
                vm.assignApprover();
            }).on("select2:unselecting", function(e) {
                var self = $(this);
                setTimeout(() => {
                    self.select2('close');
                }, 0);
            }).on("select2:unselect",function (e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                var selected = $(e.currentTarget);
                vm.selectedActivity.assigned_approver = null;
                vm.assignApprover();
            });
        },
        initialiseSelects: function(){
            if (!this.initialisedSelects){
                this.initialisedSelects = true;
                this.initMainTab();
            }
            this.initialiseAssignedOfficerSelect();            
            this.initialiseAssignedApproverSelect();
        },
        initMainTab: function() {
            if(!this.$refs.applicantTab) {
                return;
            }
            this.$refs.applicantTab.click();
            this.initFirstTab(true);
        },
        actionConditionLink: function(){
            this.hasActionedConditionLink = !this.hasActionedConditionLink;
            this.showingConditions = this.hasActionedConditionLink;

            this.hasActionedActivityTab=false;
            this.hasActionedApplicationLink=false;

            if (this.hasActionedConditionLink) {

                this.isofficerfinalisation = false;
                this.toggleOfficerConditions();

            } else if (this.selectedActivity.processing_status.id==='with_officer_finalisation') {

                this.toggleIssue();

            } else {

                this.showingConditions = false;
                this.notOfficerWorkflow=false;
                this.toggleApplication({show: true});

            }
        },
        actionConditionButton: async function(){
            this.approvingApplication = false;
            this.isofficerfinalisation = false;

            this.condition_spinner = true;
            this.spinner = true;
            let is_saved = false;
            
            // if (this.canRequestAmendment) {

            //     is_saved = await this.save_wo();

            // } else {

            //     let authorised = this.canAssignOfficerFor(this.selectedActivity.licence_activity);
            //     let workflow = ['with_officer'].includes(this.selectedActivity.processing_status.id)
            //     if (authorised && workflow) {
            //         this.setLicenceTypeData({'licence_activity_id' : this.selectedActivity.licence_activity, 'workflow': 'assess'})
            //     } 
            //     this.condition_spinner = false;
            //     $('#tabs-main li').removeClass('active');
            //     this.isSendingToAssessor = !this.isSendingToAssessor;
            //     this.showingApplication = false;
            // }


            if (!this.canRequestAmendment) {

                let authorised = this.canAssignOfficerFor(this.selectedActivity.licence_activity);
                let workflow = ['with_officer'].includes(this.selectedActivity.processing_status.id)
                if (authorised && workflow) {
                    this.setLicenceTypeData({'licence_activity_id' : this.selectedActivity.licence_activity, 'workflow': 'assess'})
                } 
                this.condition_spinner = false;
                $('#tabs-main li').removeClass('active');
                this.isSendingToAssessor = !this.isSendingToAssessor;
                this.showingApplication = false;
            } else {    

            // if (is_saved) {

                await this.assessmentData({ url: `/api/application/${this.application.id}/assessment_data_and_save.json` }).then( async response => {
                    this.condition_spinner = false;
                    this.spinner = false;   
                    // $('#tabs-main li').removeClass('active');
                    this.setAssessStatus(false);
                    this.isSendingToAssessor = !this.isSendingToAssessor;
                    this.showingApplication = false;

                },(error)=>{

                    console.log(error)
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });
            }
        },
        actionApplicationButton: async function(){
            let authorised = this.canAssignOfficerFor(this.selectedActivity.licence_activity);
            let workflow = ['with_officer','with_officer_conditions'].includes(this.selectedActivity.processing_status.id)

            if (authorised && workflow) {

                await this.setLicenceTypeData({'licence_activity_id' : this.selectedActivity.licence_activity, 'workflow': 'process'})
            }
            this.toggleApplication({show: true})
        },
        actionApplicationLink: function(){
            this.hasActionedApplicationLink = !this.hasActionedApplicationLink;

            if (!this.showingApplication && this.hasActionedApplicationLink) {

                this.isofficerfinalisation = false;
                this.toggleApplication({show: true, showFinalised: false});

            } else if (this.selectedActivity.processing_status.id==='with_officer_finalisation') {

                this.toggleIssue();

            } else if (this.selectedActivity.processing_status.id==='with_assessor') {

                this.toggleOfficerConditions();

            } else if (this.selectedActivity.processing_status.id==='accepted') {

                this.toggleOfficerConditions();

            } else {

                this.toggleApplication({show: false});

            }
        },
        actionOfficerReturnButton: async function(){
            swal({
                title: 'Return to Officer - Conditions',
                html:`
                    Please provide the reason for returning this licensed activity back to officer for review.
                    <br>This will be emailed to the licensing officer.
                `,
                input: 'text',
                inputAttributes: {
                    autocapitalize: 'off'
                },
                showCancelButton: true,
                confirmButtonText: 'Return',
                }).then(async (result) => {
                    if(!result.value) {
                        return;
                    }
                    const text = result.value;
                    const data = {
                        "activity_id" : this.selectedActivity.licence_activity,
                        "text": text
                    }
                    await this.$http.post(helpers.add_endpoint_json(
                            api_endpoints.applications, (this.application.id+'/return_to_officer')
                        ), JSON.stringify(data)).then((response) => {

                        this.$router.push({name:"internal-dash",});   

                    }, (error) => {
                        this.revert();
                        swal(
                            'Application Error',
                            helpers.apiVueResourceError(error),
                            'error'
                        )
                    });
                })
        },
        actionApplicantReturnButton: async function(){
            let is_saved = await this.save_wo();
            this.spinner = false;

            if (is_saved){

                this.$refs.amendment_request.amendment.text = '';
                this.$refs.amendment_request.isModalOpen = true;
            }
        },
        actionActivityTab: function(workflow) {
            const self = this;
            $("[data-target!=''][data-target]").off("click").on("click", function (e) {
                self.setActivityTab({
                    id: parseInt($(this).data('target').replace('#', ''), 10),
                    name: $(this).text()
                });
            });

            this.notOfficerWorkflow=false;

            if (['Applicant','IssueApplicant'].includes(workflow)) {

                if(!this.showingApplicant){

                    this.approvingApplication=false;
                    this.isofficerfinalisation=false;
                    this.isSendingToAssessor=false;
                    this.showingConditions=false;

                    this.toggleApplicant()
                }

            } else {

                this.showingApplicant=false;

                if (this.isFinalised) {

                    return
                }

                if (workflow.processing_status.name === 'Accepted') {

                    this.notOfficerWorkflow=true;
                    this.approvingApplication=false;
                    this.isofficerfinalisation = false;

                    if (this.showingConditions) {

                        this.showingApplication = false;
                        this.isSendingToAssessor = true;

                    } else if (!this.showingApplication) {

                        this.toggleApplication({show: true})
                        this.isSendingToAssessor = false;
                    }
                }
                if (workflow.processing_status.name === 'With Officer-Conditions') {

                    if (this.approvingApplication && (this.hasActionedConditionLink || this.hasActionedApplicationLink)){

                        this.approvingApplication=false;
                        this.isofficerfinalisation = false;
                        this.isSendingToAssessor = false;
                        this.showingConditions = false;

                    }
                    if (!self.isSendingToAssessor) {

                        self.toggleOfficerConditions()
                    }
                }
                if (workflow.processing_status.name === 'With Approver') {

                    if (!this.isofficerfinalisation && (!this.hasActionedConditionLink && !this.hasActionedApplicationLink)) {

                        //this.toggleIssue(); Orginal code
                        //PA code start
                        if(this.showIssueDeclineButton){//check if user has access to process application
                            this.toggleIssue();
                        }
                        else{//if no access then show application
                            //this.notOfficerWorkflow=true;
                            this.approvingApplication=false;
                            this.isofficerfinalisation = false;

                            if (this.showingConditions) {

                                this.showingApplication = false;
                                //this.isSendingToAssessor = true;

                            } else if (!this.showingApplication) {

                                this.toggleApplication({show: true})
                                this.isSendingToAssessor = true;
                            }
                        }
                        //PA code end
                    }
                    return
                }
                if (workflow.processing_status.name === 'With Officer') {

                    if (this.approvingApplication){

                        this.approvingApplication=false;
                        this.isofficerfinalisation = false;
                        this.isSendingToAssessor = false;
                        this.showingConditions = false;
                    }
                    if (!this.showingApplication) {

                        this.toggleApplication({show: true})
                    }
                }
                if (workflow.processing_status.name === 'With Assessor') {

                    this.notOfficerWorkflow=true;
                    this.approvingApplication=false;
                    this.isofficerfinalisation = false;

                    if (this.showingConditions) {

                        this.showingApplication = false;
                        this.isSendingToAssessor = true;

                    } else if (!this.showingApplication) {
        
                        this.toggleApplication({show: true})
                        this.isSendingToAssessor = false;
                    }
                } 
            }
            this.initFirstTab();
            this.hasActionedActivityTab=true;
            this.hasActionedConditionLink=false;
            this.hasActionedApplicationLink=false;

        },
        actionTabListener: function(e) {
            this.actionActivityTab(e.tab);
        }
    },
    updated: function(){
        let vm = this;
        if (!vm.panelClickersInitialised){
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                },100);
            }); 
            vm.panelClickersInitialised = true;
        }
        this.$nextTick(() => {
            vm.initialiseOrgContactTable();
            vm.initialiseSelects();
            vm.form = document.forms.new_application;
            // vm.eventListeners();
        });
    },
    mounted: function() {
        this.showingApplicant=true;
    },
    beforeRouteEnter: function(to, from, next) {
        next(vm => {
            vm.load({ url: `/api/application/${to.params.application_id}/internal_application.json` }).then(() => {
            });
            vm.loadCurrentUser({ url: `/api/my_user_details` });
        });
    },
    beforeRouteUpdate: function(to, from, next) {
        next(vm => {
            vm.load({ url: `/api/application/${to.params.application_id}.json` }).then(() => {
            });
        });
    }
}

</script>
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
.separator {
    border: 1px solid;
    margin-top: 15px;
    margin-bottom: 10px;
    width: 100%;
}
</style>
<style lang="css">
.select2-container {
    width: inherent !important;
}
</style>
