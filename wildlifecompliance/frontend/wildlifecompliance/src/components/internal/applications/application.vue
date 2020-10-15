<template lang="html">
    <div v-if="isApplicationLoaded" class="container" id="internalApplication">
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
                                {{ application.processing_status.name }}<br/>
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
                            <div class="col-sm-12 top-buffer-s" v-show="showAssignToApprover" >
                                <strong>Assigned Approver</strong><br/>
                                <div class="form-group">
                                    <template>
                                        <select ref="assigned_approver" class="form-control" v-model="selectedActivity.assigned_approver" >
                                            <option v-for="member in selectedActivity.issuing_officers" :value="member.id" v-bind:key="member.id">{{member.first_name}} {{member.last_name}}</option>
                                        </select>
                                        <a @click.prevent="makeMeApprover()" class="actionBtn pull-right">Assign to me</a>
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
                                        <a class="actionBtn" v-if="!showingApplication || !this.unfinishedActivities.length" @click.prevent="toggleApplication({show: true, showFinalised: true})">Show Application</a>
                                        <a class="actionBtn" v-else @click.prevent="toggleApplication({show: false})">Hide Application</a>
                                    </div>
                                </div>
                            </template>
                            <template v-if="isFinalised">
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
                                    <div v-if="canReturnToConditions" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="returnToOfficerConditions()">Return to Officer - Conditions</button>                                   
                                        </div>
                                    </div>   
                                    <div v-if="!applicationIsDraft && canRequestAmendment" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="amendmentRequest()">Request Amendment</button><br/>
                                        </div>
                                    </div>                            
                                    <div v-if="canIssueDecline" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="toggleIssue()">Issue/Decline</button>
                                            <!-- v-if="!userIsAssignedOfficer" was removed to enforce permission at group membership only. -->
                                            <!-- button v-else disabled class="btn btn-primary top-buffer-s col-xs-12">Issue/Decline       -->
                                        </div>
                                    </div>
                                    <div v-show="showAssessmentConditionButton" class="row">
                                        <div class="col-sm-12">
                                            <button v-if="showSpinner" disabled type="button" class="btn btn-primary top-buffer-s col-xs-12" ><i class="fa fa-spinner fa-spin"/>Assessments &amp; Conditions</button>
                                            <button v-else class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="togglesendtoAssessor()">Assessments &amp; Conditions</button><br/>
                                        </div>
                                    </div>
                                </template>
                                <template v-else>
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <strong>Action</strong><br/>
                                        </div>
                                    </div>
                                    <div v-if="isSendingToAssessor || isOfficerConditions || isofficerfinalisation" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="toggleApplication({show: true})">Back to Application</button><br/>
                                        </div>
                                    </div>
                                    <div v-if="canProposeIssueOrDecline && isSendingToAssessor || isOfficerConditions" class="row">
                                        <div class="col-sm-12">
                                            <button class="btn btn-primary top-buffer-s col-xs-12" @click.prevent="proposedLicence()">Propose Issue</button>
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
                    <IssueLicence :application="application" :licence_activity_tab="selected_activity_tab_id"/>
                </template>

                <ApplicationAssessments v-if="isSendingToAssessor || isOfficerConditions" />

                <template v-if="applicationDetailsVisible && showingApplication">
                    <div>
                    <ul class="nav nav-pills mb-3" id="tabs-main">
                        <li class="nav-item"><a ref="applicantTab" class="nav-link" data-toggle="pill" :href="'#'+applicantTab">Applicant</a></li>
                        <li class="nav-item"><a ref="applicationTab" class="nav-link" data-toggle="pill" :href="'#'+applicationTab">Application</a></li>
                    </ul>
                    <div class="tab-content">
                    <div :id="applicantTab" class="tab-pane fade in active">

                    <div class="col-md-12">
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
                                <div v-if="applicantType == 'proxy' && application.proxy_applicant.identification && application.proxy_applicant.identification.file" class="panel-body panel-collapse collapse" :id="identificationBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Identification</label>
                                            <div class="col-sm-8">
                                                <img width="100%" name="applicantIdentification" v-bind:src="application.proxy_applicant.identification.file" />
                                            </div>
                                          </div>
                                      </form>
                                </div>
                                <div v-if="applicantType == 'submitter' && application.submitter.identification && application.submitter.identification.file" class="panel-body panel-collapse collapse" :id="identificationBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Identification</label>
                                            <div class="col-sm-8">
                                                <img width="100%" name="applicantIdentification" v-bind:src="application.submitter.identification.file" />
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
                                        <label for="" class="col-sm-3 control-label">Phone (work)</label>
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
                                        <label for="" class="col-sm-3 control-label">Phone (work)</label>
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
                                        <button v-if="isCharacterCheckAccepted"  class="btn btn-primary">Reset</button>
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
                <div :id="applicationTab" class="tab-pane fade">
                    <div class="col-md-12">
                        <div class="row">
                            <form :action="application_form_url" method="post" name="new_application" enctype="multipart/form-data">
                                <Application form_width="inherit" :withSectionsSelector="false" v-if="isApplicationLoaded">
                                    <input type="hidden" name="csrfmiddlewaretoken" :value="csrf_token"/>
                                    <input type='hidden' name="schema" :value="JSON.stringify(application)" />
                                    <input type='hidden' name="application_id" :value="1" />
                                    <input type='hidden' id="selected_activity_tab_id" v-model="selected_activity_tab_id" />
                                    <div v-if="showNavBarBottom" class="row" style="margin-bottom:50px;">
                                        <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                                            <div class="navbar-inner">
                                                <div class="container">
                                                    <p class="pull-right" style="margin-top:5px;">
                                                        <span style="margin-right: 5px; font-size: 18px; display: block;" v-if="updatedFee" >
                                                            <strong>Updated application fee: {{adjusted_application_fee | toCurrency}}</strong>
                                                            <strong>licence fee: {{application.licence_fee | toCurrency}}</strong>
                                                        </span>   
                                                        <button v-if="showSpinner" type="button" class="btn btn-primary" ><i class="fa fa-spinner fa-spin"/>Saving</button>                                                    
                                                        <button v-else="!applicationIsDraft && canSaveApplication" class="btn btn-primary" @click.prevent="save()">Save Changes</button>
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
                                    <strong>Decision: {{ activity.decision_action }}</strong><br/>
                                    <strong>Start date: {{ activity.start_date | formatDateNoTime }}</strong><br/>
                                    <strong>Expiry date: {{ activity.expiry_date | formatDateNoTime }}</strong>                                    
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
    <ProposedLicence ref="proposed_licence" @refreshFromResponse="refreshFromResponse"></ProposedLicence>

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
            detailsBody: 'detailsBody'+vm._uid,
            identificationBody: 'identificationBody'+vm._uid,
            addressBody: 'addressBody'+vm._uid,
            contactsBody: 'contactsBody'+vm._uid,
            checksBody: 'checksBody'+vm._uid,
            decisionBody: 'decisionBody'+vm._uid,
            isSendingToAssessor: false,
            assessorGroup:{},
            "selectedAssessor":{},
            "loading": [],
            form: null,
            // activity_data:[],
            contacts_table_initialised: false,
            initialisedSelects: false,
            showingApplication:true,
            isOfficerConditions:false,
            isofficerfinalisation:false,
            contacts_table_id: vm._uid+'contacts-table',
            application_assessor_datatable:vm._uid+'assessment-table',
            spinner: false,
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
            adjusted_application_fee: 0,
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
            'application_workflow_state',
        ]),
        applicationDetailsVisible: function() {
            return !this.isSendingToAssessor && !this.isofficerfinalisation && this.unfinishedActivities.length && !this.isOfficerConditions;
        },
        applicationIsDraft: function(){
            return this.application.processing_status.id == 'draft';
        },
        selectedActivity: function(){
            // Function that returns an Application Selected Activity.
            if (this.selected_activity_tab_id == null || this.selected_activity_tab_id<1) {

                this.initFirstTab()     // Each Tab is a Licence Activity.
            }
            return this.application.activities.find(activity => {

                return activity.licence_activity === this.selected_activity_tab_id                
            })
        },
        canIssueDecline: function(){
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
            return true;
        },
        canSaveApplication: function() {
            // Assessors can save the Assessor Comments field.
            if(this.selected_activity_tab_id &&
                this.userHasRole('assessor', this.selected_activity_tab_id) &&
                this.selectedActivity.processing_status.id == 'with_assessor') {
                    return true;
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
            return this.canIssueDecline;
        },
        canProposeIssueOrDecline: function(){
            let auth_activity = this.canAssignOfficerFor(this.selected_activity_tab_id);

            let proposal = auth_activity && auth_activity.is_with_officer && this.licence_type_data.activity.find(activity => {
                    return activity.id === this.selected_activity_tab_id
                        && activity.processing_status.name.match(/with officer/gi) // FIXME: required because of temporary status set below.
                });                                                                // processing_status.id not related to processing_status.name

            if (this.application_workflow_state){
                // presentation frontend state is incomplete.
                proposal = false;
            }

            // officer can Issue or Decline without conditions so set temporary status.
            return proposal ? proposal.processing_status.id = 'with_officer_conditions' : false;
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
            return this.application.id_check_status.id == 'accepted';
        },
        isIdNotChecked: function(){
            return this.application.id_check_status.id == 'not_checked';
        },
        isIdCheckRequested: function(){
            return this.application.id_check_status.id == 'awaiting_update';
        },
        isIdCheckUpdated: function(){
            return this.application.id_check_status.id == 'updated';
        },
        isCharacterCheckAccepted: function(){
            return this.application.character_check_status.id == 'accepted';
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
            return (this.adjusted_application_fee !== 0 || this.application.licence_fee !== 0) ? true : false
        },
        showNavBarBottom: function() {
            return this.canReturnToConditions || (!this.applicationIsDraft && this.canSaveApplication)
        },
        showAssignToOfficer: function(){
            return this.showingApplication && this.canAssignOfficerFor(this.selectedActivity.licence_activity)
        },
        showAssignToApprover: function(){
            return this.showingApplication && this.canAssignApproverFor(this.selectedActivity.licence_activity)
        },
        showAssessmentConditionButton: function() {

            return this.showingApplication 
                && !this.applicationIsDraft 
                && (this.hasRole('licensing_officer') || this.hasRole('issuing_officer'))

        },
        showFinalDecision: function() {
            if (['awaiting_payment'].includes(this.application.processing_status.id)) { // prevent processing for outstanding payments.
                this.toggleApplication({show: false})
                this.isSendingToAssessor=false
            }
            return (!this.showingApplication || !this.unfinishedActivities.length) && !this.isSendingToAssessor && !this.canIssueDecline
        },
        showSpinner: function() {
            return this.spinner
        },
        showReturnCheckButton: function() {
            return this.application.is_return_check_accept ? false : true
        }
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
        ]),
        eventListeners: function(){
            let vm = this;
            $("[data-target!=''][data-target]").off("click").on("click", function (e) {
                vm.setActivityTab({
                    id: parseInt($(this).data('target').replace('#', ''), 10),
                    name: $(this).text()
                });
            });
            this.initFirstTab();
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
            const tab = $('#tabs-section li:first-child a')[0];
            if(tab) {
                tab.click();
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
            var selectedTabTitle = $("#tabs-section li.active");
            this.$refs.proposed_licence.propose_issue.licence_activity_id=this.selected_activity_tab_id;
            this.$refs.proposed_licence.propose_issue.licence_activity_name=selectedTabTitle.text();
            this.$refs.proposed_licence.isModalOpen = true;
            this.$refs.proposed_licence.preloadLastActivity();
        },
        toggleIssue: async function(){
            this.showingApplication = false;
            this.isSendingToAssessor=false;
            this.isOfficerConditions=false;

            this.isofficerfinalisation=true;
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
                        vm.setApplication(response.body);
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
                        vm.setApplication(response.body);
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
                        vm.setApplication(response.body);
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
                        vm.setApplication(response.body);
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
                        vm.setApplication(response.body);
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
                        vm.setApplication(response.body);
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        amendmentRequest: async function(){
            let vm = this;
            let is_saved = await vm.save_wo();

            if (is_saved){
                vm.$refs.amendment_request.amendment.text = '';
                vm.$refs.amendment_request.isModalOpen = true;
            }

        },
        togglesendtoAssessor: async function(){
            this.spinner = true
            await this.assessmentData({ url: `/api/application/${this.application.id}/assessment_data.json` }).then( async response => {
                this.spinner = false;   
                $('#tabs-main li').removeClass('active');
                this.isSendingToAssessor = !this.isSendingToAssessor;
                this.showingApplication = false;

            },(error)=>{
                swal(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
        save: async function(props = { showNotification: true }) {
            this.spinner = true;
            const { showNotification } = props;
            // await this.saveFormData({ url: this.form_data_comments_url }).then( async response => {

                await this.saveFormData({ url: this.form_data_application_url }).then(response => {
                    this.spinner = false;   
                    showNotification && swal(
                        'Saved',
                        'Your application has been saved',
                        'success'
                    )     
                }, error => {
                    console.log('Failed to save Application: ', error);
                    swal(
                        'Application Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            // }, error => {
            //     console.log('Failed to save comments: ', error);
            //     this.spinner = false;
            //     swal(
            //         'Application Error',
            //         helpers.apiVueResourceError(error),
            //         'error'
            //     )
            // });
        },
        save_wo: async function() {
            await this.save({ showNotification: false });
            return true
        },
        toggleApplication: function({show=false, showFinalised=false}){

            this.showingApplication = show;
            if(this.isSendingToAssessor){
                this.isSendingToAssessor = !show;
            }
            if(this.isOfficerConditions){
                this.isOfficerConditions = !show;
            }
            if(this.isofficerfinalisation){
                this.isofficerfinalisation = !show;
            }
            this.toggleFinalisedTabs(showFinalised);
            setTimeout(() => {
                const firstTab = $('#tabs-main li a')[1];
                if(firstTab != null) {
                    firstTab.click();
                }
                this.initFirstTab(true);
            }, 50);
            !showFinalised && this.load({ url: `/api/application/${this.application.id}/internal_application.json` });
        },
        toggleConditions:function(){
            this.showingApplication = false;
            this.isSendingToAssessor=false;
            this.isOfficerConditions=false;
        },
        returnToOfficerConditions: async function(){

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
        toggleOfficerConditions: async function(){
            let is_saved = await this.save_wo();
            this.showingApplication = false;
            this.isSendingToAssessor=false;

            this.isOfficerConditions=true;
        },
        updateAssignedOfficerSelect:function(){
            let vm = this;
            $(vm.$refs.assigned_officer).val(vm.selectedActivity.assigned_officer);
            $(vm.$refs.assigned_officer).trigger('change');
        },
        assignToMe: async function(){
            let vm = this;
            const data = {
                "activity_id" : this.selectedActivity.licence_activity,
            }
            await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/assign_to_me')),JSON.stringify(data),{
                emulateJSON:true

            }).then((response) => {
                this.refreshFromResponse(response);
                vm.updateAssignedOfficerSelect();
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
                    this.refreshFromResponse(response);
                    this.updateAssignedOfficerSelect();
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
                    this.refreshFromResponse(response);
                    this.updateAssignedOfficerSelect();
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
                    this.refreshFromResponse(response);
                    this.updateAssignedApproverSelect();
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
                    this.refreshFromResponse(response);
                    this.updateAssignedOfficerSelect();
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
            const data = {
                "activity_id" : this.selectedActivity.licence_activity,
            }
            await vm.$http.post(helpers.add_endpoint_json(api_endpoints.applications,(vm.application.id+'/make_me_activity_approver')),JSON.stringify(data),{
                emulateJSON:true

            }).then((response) => {
                this.refreshFromResponse(response);
                this.updateAssignedApproverSelect();

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
        }
    },
    mounted: function() {
        // console.log(this.application)
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
            vm.eventListeners();
        });
        if ((this.application.application_type.id=='amend_activity') // licence activity amendments.
        || (this.application.customer_status.id=='amendment_required' || this.application.customer_status.id=='under_review')) { // requested amendments.
            // fees can be adjusted by officer from selected components for requested amendments.
            // this.adjusted_application_fee = this.application.application_fee - this.application.adjusted_paid_amount
        } else {
            // no adjustments for new applications.
            // this.adjusted_application_fee = this.application.application_fee
        }
        this.adjusted_application_fee = this.application.application_fee
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
