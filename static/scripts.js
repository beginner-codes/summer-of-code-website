async function apiRequest(method, endpoint, payload){
    const fetched = await fetch(
        endpoint,
        {
            headers: new Headers(
                {
                    "Authorization": `Bearer ${sessionToken}`, 
                    'content-type': 'application/json'
                }
            ),
            method: method,
            body: JSON.stringify(payload ?? {})
        }
    )
    return await fetched.json()
}