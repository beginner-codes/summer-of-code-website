async function apiRequest(method, endpoint, payload){
    let options = {
        headers: new Headers(
            {
                "Authorization": `Bearer ${sessionToken}`,
                'content-type': 'application/json'
            }
        ),
        method: method
    }
    if(method.toUpperCase() !== "GET" && method.toUpperCase() !== "HEAD")
        options.body = JSON.stringify(payload ?? {})

    const fetched = await fetch(
        endpoint,
        options
    )
    return await fetched.json()
}