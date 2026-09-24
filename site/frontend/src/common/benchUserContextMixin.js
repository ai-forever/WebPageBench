import { mapGetters } from 'vuex';
import {
  getBenchLoginData,
  getBenchPersonalInfo,
  getBenchSessionUser,
  getGroceryUserContext,
  getRailPassengers,
  getRailPrimaryPassenger,
  getShopUserContext,
} from '@/common/benchPersonalInfo.js';

/** Shared computed helpers for bench pages that need unified personal data. */
export const benchUserContextMixin = {
  computed: {
    ...mapGetters(['trackConfig']),
    personalInfo() {
      return getBenchPersonalInfo(this.trackConfig);
    },
    benchLoginData() {
      return getBenchLoginData(this.trackConfig);
    },
    benchSessionUser() {
      return getBenchSessionUser(this.trackConfig);
    },
    shopUser() {
      return getShopUserContext(this.trackConfig);
    },
    groceryUser() {
      return getGroceryUserContext(this.trackConfig);
    },
    railPassengers() {
      return getRailPassengers(this.trackConfig);
    },
    railPrimaryPassenger() {
      return getRailPrimaryPassenger(this.trackConfig);
    },
  },
};
