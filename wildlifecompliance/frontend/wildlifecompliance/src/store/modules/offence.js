import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import moment from 'moment';

export const offenceStore = {
    namespaced: true,
    state: {
        // offence doesn't have any contents in it.
        // you can call setOffenceEmpty to store default contents
        offence: {}
    },
    getters: {
        offence: state => state.offence,
        offence_latitude(state) {
            if (state.offence.location) {
                if (state.offence.location.geometry) {
                    if (state.offence.location.geometry.coordinates.length > 0) {
                        return state.offence.location.geometry.coordinates[1];
                    } else {return "";}
                } else {return "";}
            } else {return "";}
        },
        offence_longitude(state) {
            if (state.offence.location) {
                if (state.offence.location.geometry) {
                    if (state.offence.location.geometry.coordinates.length > 0) {
                        return state.offence.location.geometry.coordinates[0];
                    } else {return "";}
                } else {return "";}
            } else {return "";}
        },
    },
    mutations: {
        updateAllegedOffenceIds(state, ids) {
            Vue.set(state.offence, 'alleged_offences', ids);
        },
        updateOffenders(state, offenders) {
            Vue.set(state.offence, 'offenders', offenders);
        },
        updateCallEmailId(state, id) {
            state.offence.call_email_id = id;
        },
        updateLegalCaseId(state, id) {
            state.offence.legal_case_id = id;
        },
        updateRegionId(state, id) {
            state.offence.region_id = id;
        },
        updateDistrictId(state, id) {
            state.offence.district_id = id;
        },
        updateAllocatedGroupId(state, id) {
            state.offence.allocated_group_id = id;
        },
        updateInspectionId(state, id) {
            state.offence.inspection_id = id;
        },
        updateOffence(state, offence) {
            if (!offence.location) {
                /* When location is null, set default object */
                offence.location =
                {
                    "type": "Feature",
                    properties: {
                        town_suburb: null,
                        street: null,
                        state: null,
                        postcode: null,
                        country: null,
                    },
                    id: null,
                    geometry: {
                        "type": "Point",
                        "coordinates": [],
                    },
                };
            }
            if (offence.occurrence_date_from) {
                offence.occurrence_date_from = moment(offence.occurrence_date_from, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            if (offence.occurrence_date_to) {
                offence.occurrence_date_to = moment(offence.occurrence_date_to, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            if (offence.occurrence_time_from) {
                offence.occurrence_time_from = moment(offence.occurrence_time_from, 'HH:mm:ss').format('LT');
            }
            if (offence.occurrence_time_to) {
                offence.occurrence_time_to = moment(offence.occurrence_time_to, 'HH:mm:ss').format('LT');
            }
            Vue.set(state, 'offence', offence);
        },
        updateOffenceEmpty(state){
            let offence = {
                id: null,
                call_email_id: null,
                inspection_id: null,
                identifier: '',
                status: 'draft',
                offenders: [],
                alleged_offences: [],
                location: {
                    type: 'Feature',
                    properties: {
                        town_suburb: null,
                        street: null,
                        state: 'WA',
                        postcode: null,
                        country: 'Australia',
                        details: ''
                    },
                    geometry: {
                        'type': 'Point',
                        'coordinates': []
                    }
                },
                occurrence_from_to: true,
                occurrence_date_from: null,
                occurrence_date_to: null,
                occurrence_time_from: null,
                occurrence_time_to: null,
                details: '',
                region_id: null,
                district_id: null,
                assigned_to_id: null,
                allocated_group: [],
                allocated_group_id: null,
                lodgement_number: '',
            };
            Vue.set(state, 'offence', offence);
        },
        updateLocationPoint(state, point) {
            state.offence.location.geometry.coordinates = point;
        },
        updateLocationAddress(state, location_properties) {
            state.offence.location.properties = location_properties;
        },
        updateLocationAddressEmpty(state) {
            state.offence.location.properties.town_suburb = "";
            state.offence.location.properties.street = "";
            state.offence.location.properties.state = "";
            state.offence.location.properties.postcode = "";
            state.offence.location.properties.country = "";
        },
        updateLocationDetailsFieldEmpty(state) {
            state.offence.location.properties.details = "";
        },
        updateAssignedToId(state, assigned_to_id) {
            Vue.set(state.offence, 'assigned_to_id', assigned_to_id);
        },
        updateCanUserAction(state, can_user_action) {
            Vue.set(state.offence, 'can_user_action', can_user_action);
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.offence, 'related_items', related_items);
        },
    },
    actions: {
        async loadOffence({ dispatch, }, { offence_id }) {
            console.log('*** loadOffende ***');
            try {
                if (offence_id) {
                    const returnedOffence = await Vue.http.get(helpers.add_endpoint_json(api_endpoints.offence, offence_id));
                    console.log('*** returnedOffence.body ***')
                    console.log('returnedOffence.body')
                    await dispatch("setOffence", returnedOffence.body);
                } else {
                    dispatch("setOffenceEmpty");
                }
            } catch (err) {
                console.log(err);
            }
        },
        async saveOffence({dispatch, state, commit}, params) {
            //try{
                console.log('params');
                console.log(params);
                // Construct url endpoint
                let fetchUrl = helpers.add_endpoint_join(api_endpoints.offence, state.offence.id + '/');

                // Construct payload to store data to be sent
                let payload = new Object();
                Object.assign(payload, state.offence);

                if (params.fr_date && params.fr_time){
                    let occurrence_datetime_from = moment(params.fr_date + ' ' + params.fr_time, 'DD/MM/YYYY LT');
                    payload.occurrence_datetime_from = occurrence_datetime_from.toDate().toISOString();
                } else {
                    throw new Error('Occurrence date-from and time-from cannot be empty');
                }

                if (payload.occurrence_from_to) {
                    if (params.to_date && params.to_time){
                        let occurrence_datetime_to = moment(params.to_date + ' ' + params.to_time, 'DD/MM/YYYY LT');
                        payload.occurrence_datetime_to = occurrence_datetime_to.toDate().toISOString();
                    } else {
                        throw new Error('Occurrence date-to and time-to cannot be empty');
                    }
                }

               // // Format date
               // if (payload.occurrence_date_from) {
               //     payload.occurrence_date_from = moment(payload.occurrence_date_from, 'DD/MM/YYYY').format('YYYY-MM-DD');
               // }
               // if (payload.occurrence_date_to) {
               //     payload.occurrence_date_to = moment(payload.occurrence_date_to, 'DD/MM/YYYY').format('YYYY-MM-DD');
               // }
               // // Format time
               // if (payload.occurrence_time_from) {
               //     payload.occurrence_time_from = moment(payload.occurrence_time_from, 'LT').format('HH:mm');
               // }
               // if (payload.occurrence_time_to) {
               //     payload.occurrence_time_to = moment(payload.occurrence_time_to, 'LT').format('HH:mm');
               // }

                console.log('payload offence');
                console.log(payload);

                payload.status = 'open'

                // Send data to the server
                const savedOffence = await Vue.http.put(fetchUrl, payload);

                // Restore returned data into the stre
                commit("updateOffence", savedOffence.body);

                // Display message
           //     await swal("Saved", "The record has been saved", "success");

                // Return the saved data just in case needed
                return savedOffence;
          //  } catch (err) {
          //      console.log('catch(err) in offence.js');

          //      if (err.body.non_field_errors){
          //          await swal("Error", err.body.non_field_errors[0], "error");
          //      } else {
          //          await swal("Error", "There was an error saving the record", "error");
          //      }
          //  }
        },
        async createOffence({dispatch, state}){
            console.log('createOffence');
            let fetchUrl = '/api/offence/';

            let payload = new Object();
            Object.assign(payload, state.offence);

            if (payload.occurrence_date_from && payload.occurrence_time_from){
                let occurrence_datetime_from = moment(payload.occurrence_date_from + ' ' + payload.occurrence_time_from, 'DD/MM/YYYY LT');
                payload.occurrence_datetime_from = occurrence_datetime_from.toDate().toISOString();
            } else {
                throw new Error('Occurrence date-from and time-from cannot be empty');
            }

            if (payload.occurrence_from_to) {
                if (payload.occurrence_date_to && payload.occurrence_time_to){
                    let occurrence_datetime_to = moment(payload.occurrence_date_to + ' ' + payload.occurrence_time_to, 'DD/MM/YYYY LT');
                    payload.occurrence_datetime_to = occurrence_datetime_to.toDate().toISOString();
                } else {
                    throw new Error('Occurrence date-to and time-to cannot be empty');
                }
            }

            console.log('payload');
            console.log(payload);

            const savedOffence = await Vue.http.post(fetchUrl, payload);
            await dispatch("setOffence", savedOffence.body);
            return savedOffence;
        },
        setOffence({ commit, }, offence) {
            commit("updateOffence", offence);
        },
        setOffenceEmpty({ commit, }){
            commit("updateOffenceEmpty");
        },
        setLocationPoint({ commit, }, point) {
            commit("updateLocationPoint", point);
        },
        setLocationAddress({ commit, }, location_properties) {
            commit("updateLocationAddress", location_properties);
        },
        setLocationAddressEmpty({ commit, }) {
            commit("updateLocationAddressEmpty");
        },
        setLocationDetailsFieldEmpty({ commit, }) {
            commit("updateLocationDetailsFieldEmpty");
        },
        setAllegedOffenceIds({ commit, }, ids){
            commit("updateAllegedOffenceIds", ids);
        },
        setOffenders({ commit, }, offenders){
            commit("updateOffenders", offenders);
        },
        setCallEmailId({ commit, }, id){
            commit("updateCallEmailId", id);
        },
        setLegalCaseId({ commit, }, id){
            commit("updateLegalCaseId", id);
        },
        setRegionId({ commit, }, id){
            commit("updateRegionId", id);
        },
        setDistrictId({ commit, }, id){
            commit("updateDistrictId", id);
        },
        setAllocatedGroupId({ commit, }, id){
            commit("updateAllocatedGroupId", id);
        },
        setInspectionId({ commit, }, id){
            commit("updateInspectionId", id);
        },
        setAssignedToId({ commit, }, assigned_to_id) {
            commit("updateAssignedToId", assigned_to_id);
        },
        setCanUserAction({ commit, }, can_user_action) {
            commit("updateCanUserAction", can_user_action);
        },
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
    },
};
