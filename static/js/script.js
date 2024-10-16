// Populating the day dropdown
const daySelect = document.getElementById('day');
for (let i = 1; i <= 31; i++) {
    const option = document.createElement('option');
    option.value = i;
    option.text = i;
    daySelect.appendChild(option);
}

// Populating the month dropdown
const monthSelect = document.getElementById('month');
const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
months.forEach((month, index) => {
    const option = document.createElement('option');
    option.value = index + 1;  // month index starts from 1 for January
    option.text = month;
    monthSelect.appendChild(option);
});

// Populating the year dropdown
const yearSelect = document.getElementById('year');
const currentYear = new Date().getFullYear();
for (let year = currentYear; year >= 1900; year--) {
    const option = document.createElement('option');
    option.value = year;
    option.text = year;
    yearSelect.appendChild(option);
}

// Existing code for form submission
document.getElementById('cfForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = {
        name: document.getElementById('name').value,
        surname: document.getElementById('surname').value,
        day: document.getElementById('day').value,
        month: document.getElementById('month').value,
        year: document.getElementById('year').value,
        sex: document.querySelector('input[name="sex"]:checked').value,
        placeOfBirth: document.getElementById('placeOfBirth').value
    };
    const response = await fetch('/generate_cf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    });
    const result = await response.json();
    document.getElementById('cfResult').innerText = `Codice Fiscale: ${result.codiceFiscale}`;
});