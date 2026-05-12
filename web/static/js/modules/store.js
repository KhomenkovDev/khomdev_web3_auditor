const state = {
    sessionId: null,
    findings: [],
    status: 'idle', 
};

const listeners = [];

export function getState() {
    return state;
}

export function setState(updates) {
    Object.assign(state, updates);
    listeners.forEach(fn => fn(state));
}

export function onStateChange(fn) {
    listeners.push(fn);
    return () => {
        const idx = listeners.indexOf(fn);
        if (idx !== -1) listeners.splice(idx, 1);
    };
}
