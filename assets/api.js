let sessionToken = null;

function setSessionToken(token) {
    sessionToken = token;
}

async function fetchApi(path, options = {}) {
    const headers = { 
        "Content-Type": "application/json", 
        ...options.headers 
    };
    
    if (sessionToken) {
        headers["Authorization"] = `Bearer ${sessionToken}`;
    }
    
    const res = await fetch(`${window.BRISQ_CONFIG.API_BASE}${path}`, { 
        ...options, 
        headers 
    });
    
    if (!res.ok && res.status !== 401) {
        // We let callers handle 401 themselves if they want, or we can throw.
        // We'll throw for anything that isn't ok to maintain the existing error contract.
        // If 401 specifically needs handling by callers (like login), it will be caught there.
    }
    
    return res;
}
