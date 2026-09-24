import {
    v4 as uuidv4
} from 'uuid';

export const SettingsHelper = {
    getUserId() {
        this.initUserId();
        return localStorage.userId;
    },
    initUserId() {
        if (!localStorage.userId) {
            localStorage.userId = uuidv4();
        }
    },
    getUserToken() {
        if (!localStorage.userToken) {
            return "token is not set";
        }
        return localStorage.userToken;
    },
    setUserToken(token) {
        localStorage.userToken = token;
    },
}

const defaultClientSettings = {}