
const isFlush = (el) => (
    (el.scrollTop + el.clientHeight) >= el.scrollHeight // Was scrolled to bottom of screen
    ||
    (el.scrollTop == 0 && el.clientHeight >= el.scrollHeight) // No scrolling,
);

const autoScrollKey = Symbol("_v_autoscroll");

export const vAutoScroll = {
    mounted(el, binding, vnode) {
        // Define state object to track observers, etc.
        el[autoScrollKey] = {
            observer: null,
            scrollHandler: null,
            wasFlush: true,
        };
        const state = el[autoScrollKey];


        // Tracks when the window is scrolled to the bottom;
        const scrollHandler = () => {
            const flush = isFlush(el);
            state.wasFlush = flush;
        }
        el.addEventListener("scroll", scrollHandler)

        // Tracks when things may change on the page that would affect the scroll position
        const mutationHandler = (mutationList, observer) => {
            if (state.wasFlush && !isFlush(el)) {
                el.scrollTo({
                    left: 0,
                    top: el.scrollHeight,
                    behavior: "instant",
                });
            }
        }

        // Register Mutation observer to track all possible changes to this element and below.
        const mutationObserver = new MutationObserver(mutationHandler);
        mutationObserver.observe(el, {
            attributes: true, childList: true, subtree: true,
        });

        // Track observers/handlers in state so we can
        state.observer = mutationObserver;
        state.scrollHandler = scrollHandler;
    },

    unmounted(el: HTMLElement, binding, vnode) {
        // Cleanup
        const state = el[autoScrollKey];
        state.observer.disconnect();
        el.removeEventListener("scroll", state.scrollHandler);
        delete state.observer;
        delete el[autoScrollKey];
    },
}
