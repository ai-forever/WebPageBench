import router from "@/router";

import { SEND_EVENT } from "@/store/actions.type";

export const ActivityTracker = {
  data() {
    return {
      tracking: {
        isActive: false,
        startTime: null,
        currentView: null,
        steps: [],
      },
      throttledHandlers: {
        scrollHandler: null,
        mouseMoveHandler: null,
      },
    };
  },

  created() {
    console.log("Activity tracker created");
    this.startTracking();

    router.beforeEach((to, from, next) => {
      if (this.tracking.isActive) {
        console.log("Navigating to", to.name, to.path);

        setTimeout(() => {
          this.sendEvent({
            type: "state_changed",
            new_state: to.name,
            new_path: to.path,
            query: to.query,
            state_id: to.params.state_id,
          });
        }, 100);

        this.setCurrentView(to.name || to.path);
      }
      next();
    });
  },

  beforeUnmount() {
    this.stopTracking();
  },

  methods: {
    startTracking() {
      this.tracking.isActive = true;
      this.tracking.startTime = new Date();

      const currentRoute = router.currentRoute.value;
      this.setCurrentView(currentRoute.name || currentRoute.path);

      if (currentRoute && currentRoute.name) {
        setTimeout(() => {
          this.sendEvent({
            type: "state_changed",
            new_state: currentRoute.name,
            new_path: currentRoute.path,
            query: currentRoute.query,
            state_id: currentRoute.params && currentRoute.params.state_id,
          });
        }, 100);
      }

      this.setupEventListeners();
    },

    stopTracking() {
      this.tracking.isActive = false;
      this.removeEventListeners();
    },

    setCurrentView(viewName) {
      // Close prev step
      if (this.tracking.currentView) {
        const currentStep = this.getCurrentStep();
        if (currentStep) {
          currentStep.endTime = new Date().toISOString();
          currentStep.duration = new Date() - new Date(currentStep.startTime);
        }
        console.log("STEP", currentStep);
      }

      // Create new step
      this.tracking.currentView = viewName;
      this.tracking.steps.push({
        stepNumber: this.tracking.steps.length + 1,
        viewName: viewName,
        startTime: new Date().toISOString(),
        endTime: null,
        duration: 0,
        activities: [],
      });
    },

    getCurrentStep() {
      return this.tracking.steps[this.tracking.steps.length - 1];
    },

    setupEventListeners() {
      console.log("Setting up event listeners");

      // Bind all event handlers to preserve 'this' context
      this.boundTrackClick = this.trackClick.bind(this);
      this.boundTrackKeypress = this.trackKeypress.bind(this);
      // this.boundTrackInput = this.trackInput.bind(this);
      this.boundTrackVisibility = this.trackVisibility.bind(this);
      this.boundTrackMouseMove = this.trackMouseMove.bind(this);
      this.boundTrackScroll = this.trackScroll.bind(this);

      // Create throttled handlers with proper binding
      this.throttledHandlers.scrollHandler = this.throttle(
        this.boundTrackScroll,
        500
      );
      this.throttledHandlers.mouseMoveHandler = this.throttle(
        this.boundTrackMouseMove,
        1000
      );

      // Add listeners using the bound methods
      document.addEventListener("click", this.boundTrackClick);
      document.addEventListener("keydown", this.boundTrackKeypress);
      window.addEventListener("scroll", this.throttledHandlers.scrollHandler);
      // document.addEventListener("input", this.boundTrackInput);
      document.addEventListener("visibilitychange", this.boundTrackVisibility);
      // document.addEventListener("mousemove", this.throttledHandlers.mouseMoveHandler);
    },

    removeEventListeners() {
      console.log("Removing event listeners");

      document.removeEventListener("click", this.boundTrackClick);
      document.removeEventListener("keydown", this.boundTrackKeypress);
      window.removeEventListener(
        "scroll",
        this.throttledHandlers.scrollHandler
      );
      // document.removeEventListener("input", this.boundTrackInput);
      document.removeEventListener(
        "visibilitychange",
        this.boundTrackVisibility
      );
      document.removeEventListener(
        "mousemove",
        this.throttledHandlers.mouseMoveHandler
      );
    },

    logActivity(activity) {
      console.log("Logging activity", activity);

      const currentStep = this.getCurrentStep();
      if (currentStep) {
        currentStep.activities.push({
          ...activity,
          timestamp: new Date().toISOString(),
          timeInView: new Date() - new Date(currentStep.startTime),
          totalSessionTime: new Date() - this.tracking.startTime,
        });
      }

      this.sendEvent(activity);
    },

    sendEvent(event) {
      let fromLogEventView = this.$route.name === "event_log";
      if (fromLogEventView) return;

      let trackId = this.$route.params.track_id;
      
      console.log("Sending event", event, "trackId", trackId);
      // console.log("Parameters", this.$route.params);

      // event = {type: 'state_changed', new_state: 'bench_books_basket', new_path: '/ecommerce_basket_any_product/state_basket/bench_books_basket'}
      if (!trackId) {
        const fromPath = event && event.new_path ? String(event.new_path).split("/")[1] : "";
        trackId = fromPath;
        console.log("TrackId not found, using event.new_path", trackId);
        if (!trackId) return;
      }

      this.$store
        .dispatch(SEND_EVENT, {
          trackId: trackId,
          eventName: event.type,
          eventData: JSON.stringify(event),
        })
        .then(() => {
          // console.log('Data sent successfully');
        });
    },

    trackClick(event) {
      if (!this.tracking.isActive) return;

      const target = event.target;
      let safeClass = "";
      const rawClass = target && target.className;
      if (typeof rawClass === "string") {
        safeClass = rawClass;
      } else if (rawClass && typeof rawClass.baseVal === "string") {
        // SVG elements expose className as SVGAnimatedString
        safeClass = rawClass.baseVal;
      }

      let elementPath = "";
      try {
        elementPath = this.getElementPath(target);
      } catch (e) {
        elementPath = "";
      }

      this.logActivity({
        type: "click",
        element: target && target.tagName ? target.tagName.toLowerCase() : "",
        id: target.id,
        class: safeClass,
        path: elementPath,
        position: {
          x: event.clientX,
          y: event.clientY,
        },
      });
    },

    trackKeypress(event) {
      if (!this.tracking.isActive) {
        return;
      }

      this.logActivity({
        type: "keypress",
        key: event.key,
        element: event.target.tagName.toLowerCase(),
        isMetaKey: event.metaKey,
        isCtrlKey: event.ctrlKey,
      });
    },

    trackScroll() {
      if (!this.tracking.isActive) return;

      this.logActivity({
        type: "scroll",
        position: {
          scrollX: window.scrollX,
          scrollY: window.scrollY,
        },
        viewportHeight: window.innerHeight,
        documentHeight: document.documentElement.scrollHeight,
      });
    },

    trackInput(event) {
      if (!this.tracking.isActive) return;

      this.logActivity({
        type: "input",
        element: event.target.tagName.toLowerCase(),
        inputType: event.target.type,
        id: event.target.id,
        name: event.target.name,
      });
    },

    trackVisibility() {
      if (!this.tracking.isActive) return;

      this.logActivity({
        type: "visibility",
        state: document.visibilityState,
      });
    },

    trackMouseMove(event) {
      if (!this.tracking.isActive) return;

      this.logActivity({
        type: "mousemove",
        position: {
          x: event.clientX,
          y: event.clientY,
        },
      });
    },

    getElementPath(element) {
      const path = [];
      let current = element;
      while (current && current.nodeType === 1) {
        let selector = current.tagName ? current.tagName.toLowerCase() : "";
        if (current.id) {
          selector += `#${current.id}`;
        } else {
          let classString = "";
          const cn = current.className;
          if (typeof cn === "string") {
            classString = cn;
          } else if (cn && typeof cn.baseVal === "string") {
            // Handle SVGAnimatedString
            classString = cn.baseVal;
          }
          if (classString) {
            selector += `.${classString.trim().split(/\s+/).join(".")}`;
          }
        }
        path.unshift(selector);
        // Prefer parentElement; fallback to parentNode for SVG roots
        const next = current.parentElement || current.parentNode;
        if (!next || next === current || (next.nodeType && next.nodeType === 9)) {
          break;
        }
        current = next;
      }
      return path.join(" > ");
    },

    throttle(func, limit) {
      let inThrottle;
      return function (...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => (inThrottle = false), limit);
        }
      };
    },

    getTrackingSummary() {
      return {
        totalDuration: new Date() - this.tracking.startTime,
        startTime: this.tracking.startTime,
        steps: this.tracking.steps.map((step) => ({
          ...step,
          activityCount: step.activities.length,
          activityTypes: this.summarizeActivities(step.activities),
        })),
      };
    },

    summarizeActivities(activities) {
      return activities.reduce((summary, activity) => {
        summary[activity.type] = (summary[activity.type] || 0) + 1;
        return summary;
      }, {});
    },

    exportTracking() {
      const summary = this.getTrackingSummary();
      const dataStr = JSON.stringify(summary, null, 2);
      const dataBlob = new Blob([dataStr], { type: "application/json" });
      const url = window.URL.createObjectURL(dataBlob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `user-journey-${new Date().toISOString()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  },
};

export default ActivityTracker;
