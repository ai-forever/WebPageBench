import {
    createStore
} from 'vuex'

import {
    v4 as uuidv4
} from 'uuid';

import {
    DataService
} from "@/common/api.service";
import { isUnifiedBench, mergeDomainIntoConfig } from '@/common/benchTheme';

import {
    SET_USER_ID,
    SET_USER_NAME,
    SET_AUTHORIZATION,
    SET_TRACK_CONFIG,
    SET_KV_STORE,
    SET_EVENTS,
    PATCH_TRACK_CONFIG
} from "./mutations.type"

import {
    // GET_AUTHORIZATION,
    GET_TRACK_CONFIG,
    GET_KV_STORE,
    GET_EVENTS,
    SEND_EVENT
} from "./actions.type"

import {
    SettingsHelper
} from "@/common/settings.helper";

import { applyDefaultMockLoginFromTrackConfig, bindBenchTrackSession } from "@/utils/localCache.js";
import { rewriteMediaTree } from "@/common/cdnUrls";

const initialState = {
    userId: SettingsHelper.getUserId(),
    userName: "Sergei",
    submitInfo: {},
    submitsInfo: { "items": [] },
    authorized: false,
    currentTrackId: null,
    trackConfig: {},
    kvStore: {},
    events: []
}


export default createStore({
    state: {
        ...initialState
    },
    actions: {
        async [GET_TRACK_CONFIG](context, params) {
            console.log("params", params)
            const {
                data
            } = await DataService.getTrackConfig({
                "trackId": params.trackId,
            });
            context.commit(SET_TRACK_CONFIG, {
                data: data,
                trackId: params.trackId,
            });
            return data;
        },
        async [GET_KV_STORE](context, params) {
            const {
                data
            } = await DataService.getKvStore({
                "kvPath": params.kvPath,
            });
            context.commit(SET_KV_STORE, {
                data: data.kv_store
            });
            return data;
        },
        async [GET_EVENTS](context, params) {
            const {
                data
            } = await DataService.getEvents({
                "trackId": params.trackId,
            });
            context.commit(SET_EVENTS, {
                events: data.events
            });
            return data.events;
        },
        async [SEND_EVENT](context, params) {
            await DataService.sendEvent({
                "trackId": params.trackId,
                "eventName": params.eventName,
                "eventData": params.eventData,
            });
        }


        // async [GET_AUTHORIZATION](context, params) {
        //     await DataService.get_authorization().then(
        //         function (response) {
        //             console.log(response.data);
        //             context.commit(SET_AUTHORIZATION, response.data);
        //         },
        //         function (error) {
        //             let code = ErrorHelper.getErrorCode(error)
        //             if (code == '403') {
        //                 // alert('Not authorized.')
        //                 console.log(error);
        //             } else {
        //                 // alert(error)
        //                 console.log(error);
        //             }
        //             console.log(error);
        //         }
        //     );
        // },
    },
    mutations: {
        [SET_USER_ID](state, params) {
            state.userId = params.userId;
        },
        [SET_USER_NAME](state, params) {
            state.userId = params.userName;
        },
        [SET_AUTHORIZATION](state, params) {
            if (params.authorized) {
                state.authorized = true;
            }
        },
        [SET_TRACK_CONFIG](state, params) {
            console.log("SET_TRACK_CONFIG", params.data)
            const config_str = params.data["config"];
            let config = JSON.parse(config_str);
            const activeDomain = state.trackConfig?.test_data?.active_bench_domain;
            state.currentTrackId = params.trackId || null;
            try {
                bindBenchTrackSession(params.trackId, params.data && params.data.track_mtime);
            } catch (e) {
                // ignore
            }
            if (activeDomain && isUnifiedBench(config)) {
                config = mergeDomainIntoConfig(config, activeDomain);
            }
            state.trackConfig = config;
            try {
                applyDefaultMockLoginFromTrackConfig(config);
            } catch (e) {
                // ignore
            }
        },
        [PATCH_TRACK_CONFIG](state, config) {
            state.trackConfig = config;
            try {
                applyDefaultMockLoginFromTrackConfig(config);
            } catch (e) {
                // ignore
            }
        },
        [SET_KV_STORE](state, params) {
            state.kvStore = rewriteMediaTree(JSON.parse(params.data));
        },
        [SET_EVENTS](state, params) {
            state.events = params.events;
        },
    },
    getters: {
        userId(state) {
            return state.userId;
        },
        userName(state) {
            return state.userName;
        },
        authorized(state) {
            return state.authorized;
        },
        trackConfig(state) {
            return state.trackConfig;
        },
        currentTrackId(state) {
            return state.currentTrackId;
        },
        kvStore(state) {
            return state.kvStore;
        },
        events(state) {
            return state.events;
        }
    }
})

export const ErrorHelper = {
    getErrorCode(line) {
        if (line) {
            let match = String(line).match(/^.*\s([\d]+)$/i)
            if (match && match.length > 1) {
                return match[1]
            }
            return '402'
        }
        return '402'
    }
}