export function _logActivity(vm, activity) {
  try {
    const trackerHost = vm && (vm.$root || vm);
    if (trackerHost && typeof trackerHost.logActivity === 'function') {
      trackerHost.logActivity(activity);
    }
  } catch (e) {
    console.log('Error sending activity', e);
  }
}

export default { _logActivity };


