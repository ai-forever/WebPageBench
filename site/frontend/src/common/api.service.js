import axios from "axios";

import {
    API_URL
} from "@/common/config";
import {
    SettingsHelper
} from "@/common/settings.helper";


const ApiService = {
    init() {
        console.log("API_URL", API_URL)
        axios.defaults.baseURL = API_URL;
    },
    query(resource, params) {
        return axios.get(resource, params).catch(error => {
            throw new Error(`ApiService ${error}`);
        });
    },
    get(resource, slug = "") {
        return axios.get(`${resource}/${slug}`).catch(error => {
            throw new Error(`ApiService ${error}`);
        });
    },
    download(resource, slug = "") {
        return axios.get(`${resource}/${slug}`, {
            responseType: 'blob'
        }).catch(error => {
            throw new Error(`ApiService ${error}`);
        });
    },
    post(resource, slug, params, isBinary) {
        let config = {}
        if (isBinary) {
            config = {
                responseType: 'blob'
            }
        }
        return axios.post(
            `${resource}/${slug}`,
            params,
            config
        ).catch(error => {
            throw new Error(`ApiService ${error}`);
        });
    },
    update(resource, slug, params) {
        return axios.put(`${resource}/${slug}`, params);
    },
    put(resource, params) {
        return axios.put(`${resource}`, params);
    },
    delete(resource) {
        return axios.delete(resource).catch(error => {
            throw new Error(`ApiService ${error}`);
        });
    }
};

export default ApiService;

export const DataService = {
    getTrackConfig(params) {
        let form = new FormData();
        // form.append("token", SettingsHelper.getUserToken());
        form.append("track_id", params.trackId);
        return ApiService.post("track", `get`, form);
    },
    getKvStore(params) {
        let form = new FormData();
        // form.append("token", SettingsHelper.getUserToken());
        form.append("kv_path", params.kvPath);
        return ApiService.post("kv", `get`, form);
    },
    sendEvent(params) {
        let form = new FormData();
        // form.append("token", SettingsHelper.getUserToken());
        form.append("track_id", params.trackId);
        form.append("event_name", params.eventName);
        form.append("event_data", params.eventData);
        return ApiService.post("event", `add`, form);
    },
    getEvents(params) {
        let form = new FormData();
        // form.append("token", SettingsHelper.getUserToken());
        form.append("track_id", params.trackId);
        return ApiService.post("event", `get`, form);
    },
    getGroceryCategory(params) {
        let form = new FormData();
        // form.append("token", SettingsHelper.getUserToken());
        form.append("category_id", params.categoryId);
        return ApiService.post("grocery", `category`, form);
    }
    // get_authorization(params) {
    //     let form = new FormData();
    //     form.append("token", SettingsHelper.getUserToken());
    //     return ApiService.post("user", `authorized`, form);
    // }
};