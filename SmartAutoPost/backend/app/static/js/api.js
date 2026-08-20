const API = '/api/v1';


const token = () => 
    localStorage.getItem('access_token');



/* =========================================================
   ERROR HANDLER
   ========================================================= */


function normaliseError(data, status) {


    if (!data) 
        return `Request failed (${status})`;


    if (typeof data === 'string') 
        return data;



    if (typeof data.detail === 'string') 
        return data.detail;



    if (Array.isArray(data.detail)) {


        return data.detail.map(item => {


            const field = 
            Array.isArray(item.loc)
            ? item.loc[item.loc.length - 1]
            : 'field';


            return `${field}: ${item.msg || 'Invalid value'}`;


        }).join(', ');


    }



    if (typeof data.message === 'string') 
        return data.message;



    try {

        return JSON.stringify(data);

    } 
    
    catch {

        return `Request failed (${status})`;

    }

}




/* =========================================================
   API REQUEST
   ========================================================= */


async function api(path, options = {}) {


    const headers = {
        ...(options.headers || {})
    };



    if (!(options.body instanceof FormData)) {


        headers['Content-Type'] =
        'application/json';


    }



    if (token()) {


        headers.Authorization =
        `Bearer ${token()}`;


    }



    const response = await fetch(
        API + path,
        {
            ...options,
            headers
        }
    );



    const text = 
    await response.text();



    let data = null;



    try {


        data = text 
        ? JSON.parse(text)
        : null;


    } 
    
    catch {


        data = text;


    }




    if (response.status === 401) {


        localStorage.removeItem(
            'access_token'
        );


        localStorage.removeItem(
            'refresh_token'
        );


        if(location.pathname !== '/login') {


            location.href = '/login';


        }



        throw new Error(
            'Session expired. Please sign in again.'
        );


    }





    if (!response.ok) {


        throw new Error(
            normaliseError(
                data,
                response.status
            )
        );


    }



    return data;


}





/* =========================================================
   SOCIAL LOGIN TOKEN SAVE
   ========================================================= */


function saveAuthTokens(data) {


    if(data.access_token) {


        localStorage.setItem(
            "access_token",
            data.access_token
        );


    }



    if(data.refresh_token) {


        localStorage.setItem(
            "refresh_token",
            data.refresh_token
        );


    }



    if(data.user) {


        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );


    }


}




/* =========================================================
   ORGANIZATION
   ========================================================= */


function orgId() {


    return Number(
        localStorage.getItem(
            'organization_id'
        ) || 0
    );


}





/* =========================================================
   TOAST
   ========================================================= */


function showToast(
    message,
    error = false
) {


    const toast =
    document.getElementById(
        'toast'
    );



    if(!toast) 
        return;



    toast.textContent =
    typeof message === 'string'
    ? message
    : normaliseError(
        message,
        0
    );



    toast.style.background =
    error
    ? '#b42335'
    : '#1e293b';



    toast.classList.add(
        'show'
    );



    clearTimeout(
        window.__toastTimer
    );



    window.__toastTimer =
    setTimeout(
        () => {


            toast.classList.remove(
                'show'
            );


        },
        3500
    );


}





/* =========================================================
   MODAL
   ========================================================= */


function openModal(id) {


    document
    .getElementById(id)
    ?.classList.add('open');


}





function closeModal(id) {


    document
    .getElementById(id)
    ?.classList.remove('open');


}





/* =========================================================
   LOGOUT
   ========================================================= */


function logout() {


    localStorage.clear();


    location.href =
    '/login';


}





/* =========================================================
   FORMATTERS
   ========================================================= */


function fmtDate(value) {


    return value
    ? new Date(value)
        .toLocaleString('en-IN')
    : '—';


}




function esc(value = '') {


    return String(value)
    .replace(
        /[&<>"']/g,
        c => ({

            '&':'&amp;',
            '<':'&lt;',
            '>':'&gt;',
            '"':'&quot;',
            "'":'&#039;'

        }[c])

    );


}