async function submitEmployee(event) {
    event.preventDefault();
    const form = document.getElementById('employeeForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch('/api/employees/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('token'),
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(JSON.stringify(errorData));
        }
        showToast('Employé ajouté avec succès!', 'success');
        window.location.href = '{% url "employee_list" %}';
    } catch (error) {
        showToast('Erreur lors de l\'ajout de l\'employé: ' + error.message, 'error');
    }
}