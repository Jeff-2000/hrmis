async function login(username, password) {
    const response = await fetch('/api/v1/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    if (data.access_token) {
        localStorage.setItem('token', data.access_token);
        window.location.href = '/employees/';
    } else {
        alert('Login failed: ' + (data.error || 'Unknown error'));
    }
}