


async function handleLogin() {
    const username = document.getElementById('username');
    const password = document.getElementById('password');

    username.classList.remove('error-placeholder');
    password.classList.remove('error-placeholder');

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: username.value, password: password.value }),
    });

    const result = await response.json();

    if (result.success) {
        window.location.href = '/';
    } else {
        if (result.error === 'username') {
            username.value = '';
            username.placeholder = "Username yang Anda masukkan tidak terdaftar";
            username.classList.add('error-placeholder');
        } else if (result.error === 'password') {
            password.value = '';
            password.placeholder = "Password tidak sesuai";
            password.classList.add('error-placeholder');
        }
    }
}


const loginPopup = document.getElementById('login-popup');
const triggerPopup = document.querySelector('.trigger-popup');
const inputFields = document.querySelectorAll('#login-popup input');
let timeoutId;
let isInputFocused = false;

triggerPopup.addEventListener('mouseenter', () => {
    clearTimeout(timeoutId);
    loginPopup.classList.add('show');
});

triggerPopup.addEventListener('mouseleave', (e) => {
    if (!isInputFocused && !loginPopup.contains(e.relatedTarget)) {
        timeoutId = setTimeout(() => {
            loginPopup.classList.remove('show');
        }, 300);
    }
});

loginPopup.addEventListener('mouseenter', () => {
    clearTimeout(timeoutId);
});

loginPopup.addEventListener('mouseleave', (e) => {
    if (!isInputFocused && !triggerPopup.contains(e.relatedTarget)) {
        timeoutId = setTimeout(() => {
            loginPopup.classList.remove('show');
        }, 300);
    }
});

inputFields.forEach(input => {
    input.addEventListener('focus', () => {
        isInputFocused = true;
        clearTimeout(timeoutId);
    });

    input.addEventListener('blur', () => {
        const isAnyInputFocused = Array.from(inputFields).some(input => input === document.activeElement);
        isInputFocused = isAnyInputFocused;

        if (!isInputFocused) {
            timeoutId = setTimeout(() => {
                if (!loginPopup.contains(document.activeElement) && !triggerPopup.contains(document.activeElement)) {
                    loginPopup.classList.remove('show');
                }
            }, 300);
        }
    });
});





function autoResize(textarea) {
    textarea.style.height = 'fit-content';
    textarea.style.height = (textarea.scrollHeight) + 'px';
  }

  function addExample() {
    const container = document.getElementById('example-container');

    const areaDiv = document.createElement('div');


    const textarea = document.createElement('textarea');
    textarea.name = 'examples[]';
    textarea.placeholder = `Example ${container.childElementCount + 1}`;
    
    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.textContent = 'Remove Example';
    removeButton.onclick = () => areaDiv.remove();


    areaDiv.appendChild(textarea);
    areaDiv.appendChild(removeButton);
    container.appendChild(areaDiv);
}








async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const conflictId = document.getElementById('conflict_id').value;
    
    // Convert FormData to JSON
    const payload = {
        name: formData.get('name'),
        saran: formData.get('saran'),
        examples: formData.getAll('examples[]'),
        solutions: formData.getAll('solutions[]'),
        relations: {
            cause: formData.getAll('cause[]'),
            depends_on: formData.getAll('depends_on[]'),
            resolve: formData.getAll('resolve[]')
        }
    };

    try {
        const url = conflictId ? `/update_conflict/${conflictId}` : '/add_conflict';
        const method = conflictId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.message);
        
        alert('Data saved successfully!');
        window.location.href = `/edit_conflict/${result.conflict_id}`;
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    }
}

// Fungsi tambahkan input
function addDependsOn() {
    const container = document.getElementById('depends-on-container');
    const areaDiv = document.createElement('div');
    areaDiv.classList.add('kolom-konflik-in');
    const newInput = document.createElement('textarea');
    newInput.name = 'depends_on[]';
    newInput.placeholder = `Depends On ${container.children.length + 1}`;
    newInput.required = true;

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.textContent = 'remove';
    removeButton.onclick = () => {
        areaDiv.classList.remove('kolom-konflik-in');
        areaDiv.classList.add('kolom-konflik-out');
        setTimeout(() => areaDiv.remove(),300);
    }

    areaDiv.appendChild(newInput);
    areaDiv.appendChild(removeButton);
    container.appendChild(areaDiv);
}
function addExample() {
    const container = document.getElementById('example-container');
    const newInput = document.createElement('textarea');
    newInput.name = 'examples[]';
    newInput.placeholder = `exampel n ${container.children.length + 1}`;
    newInput.required = true;
    container.appendChild(newInput);
}
function addSolution() {
    const container = document.getElementById('solution-container');
    const newInput = document.createElement('textarea');
    newInput.name = 'solutions[]';
    newInput.placeholder = `exampel n ${container.children.length + 1}`;
    newInput.required = true;
    container.appendChild(newInput);
}
function addCause() {
    const container = document.getElementById('cause-container');
    const newInput = document.createElement('textarea');
    newInput.name = 'cause[]';
    newInput.placeholder = `exampel n ${container.children.length + 1}`;
    newInput.required = true;
    container.appendChild(newInput);
}
function addResolve() {
    const container = document.getElementById('resolve-container');
    const newInput = document.createElement('textarea');
    newInput.name = 'resolve[]';
    newInput.placeholder = `exampel n ${container.children.length + 1}`;
    newInput.required = true;
    container.appendChild(newInput);
}

// Fungsi serupa untuk addExample, addSolution, addCause, addResolve




function addRelationInput(relationType, conflictId) {
    const container = document.getElementById(`${relationType}-container-${conflictId}`);
    if (!container) {
        console.error(`Container untuk ${relationType} dengan konflik ID ${conflictId} tidak ditemukan!`);
        return;
    }

    const li = document.createElement('li');

    const textarea = document.createElement('textarea');
    textarea.name = `${relationType}-${conflictId}[]`;
    textarea.placeholder = `Tambah ${relationType.charAt(0).toUpperCase() + relationType.slice(1)}`;
    textarea.required = true;

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.textContent = 'Remove';
    removeButton.onclick = () => li.remove();

    li.appendChild(textarea);
    li.appendChild(removeButton);
    container.appendChild(li);
}


// Contoh menggunakan Fetch API dengan JSON
async function submitRelations(conflictId) {
    const payload = {
        cause: [],
        depends_on: [],
        resolve: []
    };

    // Kumpulkan data dari semua input
    document.querySelectorAll('.relation-input').forEach(input => {
        const type = input.name.replace('[]', '');
        if (payload[type] && input.value.trim()) {
            payload[type].push(input.value.trim());
        }
    });

    try {
        const response = await fetch(`/submit_relations/${conflictId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Failed to save relations');
        }
        
        alert(result.message);
        // Optional: reload halaman atau update UI
        window.location.reload();
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
    }
}



async function submitSaran(conflictId) {
    const formData = new FormData();
    const saranInput = document.querySelector(`#saran-input-${conflictId}`);
    formData.append('saran', saranInput.value);

    try {
        const response = await fetch(`/saran/${conflictId}`, {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            alert('Saran updated successfully!');
        } else {
            const errorData = await response.json();
            alert(`Gagal submit saran: ${errorData.message}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Terjadi kesalahan saat mengirim data.');
    }
}



let currentExample = {
    modelTypy: null,
    conflictId: null,
    itemId: null,
    currentContent: ""
};

function openExampleModal(modelTypy,itemId, conflictId) {
    if (!conflictId) {
        console.error('Conflict ID tidak valid');
        return;
    }

    currentExample = {
        modelTypy: modelTypy,
        conflictId: conflictId,
        itemId: null,
        currentContent: ""
    };

    const modalId = `${modelTypy}-modal-${conflictId}-${itemId}`;
    const modal = document.getElementById(modalId);
    
    if (!modal) {
        console.error(`Modal dengan ID ${modalId} tidak ditemukan`);
        return;
    }

    const textarea = modal.querySelector('textarea');
    textarea.value = modelTypy === 'new' 
        ? "" 
        : document.getElementById(`${modelTypy}-content-${conflictId}-${itemId}`)?.innerText || "";

    currentExample.originalContent = textarea.value;

    const handleInput = (e) => {
        currentExample.currentContent = e.target.value;
    };
    
    textarea.removeEventListener('input', handleInput);
    textarea.addEventListener('input', handleInput);

    modal.style.display = 'block';
}
async function handleExampleSubmit(modelTypy,conflictId, itemId) {
    const modal = document.getElementById(`${modelTypy}-modal-${conflictId}-${itemId}`);
    const textarea = modal.querySelector('textarea');
    const content = textarea.value.trim();  

    if (!content) {
        alert('Konten tidak boleh kosong!');
        textarea.focus();
        return;
    }

    try {
        const isNew = itemId === 'new';
        let url;
        
        if(isNew) {
            url = `/${modelTypy}/create/${conflictId}`;
        } else {
            const baseUrl = getBaseUrlByModel(modelTypy);
            url = `/${baseUrl}/update/${itemId}`;
        }

        const response = await fetch(url, {
            method: isNew ? 'POST' : 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            if (isNew) {
                location.reload();
            } else {
                const contentElement = document.getElementById(`${modelTypy}-content-${conflictId}-${itemId}`);
                contentElement.textContent = content;
                forceCloseExampleModal(modelTypy,conflictId, itemId);
                alert('Perubahan berhasil disimpan!');
            }
        } else {
            const error = await response.json();
            alert(`Gagal menyimpan: ${error.message}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Terjadi kesalahan sistem');
    }
}


function handleCloseExampleModal(modelTypy,conflictId, itemId) {
    const modal = document.getElementById(`${modelTypy}-modal-${conflictId}-${itemId}`);
    const textarea = modal.querySelector('textarea');
    
    if (textarea.value.trim() !== currentExample.originalContent) {
        showConfirmationDialog({
            message: "Ada perubahan yang belum disimpan! Yakin ingin menutup?",
            onConfirm: () => {
                textarea.value = currentExample.originalContent;
                forceCloseExampleModal(modelTypy,conflictId, itemId);
            },
            onCancel: () => {
                textarea.focus();
            }
        });
    } else {
        forceCloseExampleModal(modelTypy,conflictId, itemId);
    }
}
// beloooooooom
function forceCloseExampleModal(modelTypy,conflictId, itemId) {
    const modalId = `${modelTypy}-modal-${conflictId}-${itemId}`;
    const modal = document.getElementById(modalId);
    
    if (modal) {
        modal.style.display = 'none';
        resetExampleState();
    }
}



function resetExampleState() {
    currentExample = {
        modelTypy: null,
        conflictId: null,
        itemId: null,
        currentContent: ""
    };
}


function confirmDeleteExample(modelTypy,itemId, conflictId) {
    showConfirmationDialog({
        message: `Yakin ingin menghapus ${modelTypy} ini?`,
        onConfirm: async () => {
            try {
                const baseUrl = getBaseUrlByModel(modelTypy);
                const url = `/${baseUrl}/delete/${itemId}`;

                await fetch(url, {method: 'DELETE'});
                const element = document.getElementById(`${modelTypy}-${conflictId}-${itemId}`);
                element.remove();
            } catch(error) {
                alert(`Gagal menghapus: ${error.message}`);
            }
        }
    });
}


// Helper function baru
function getBaseUrlByModel(modelTypy) {
    switch(modelTypy) {
        case 'example':
            return 'example';
        case 'solusi':
            return 'solusi';
        default: // Untuk relation dan turunannya
            return 'relation';
    }
}

function showConfirmationDialog({ message, onConfirm, onCancel }) {
    const confirmModal = document.getElementById('global-confirm-modal');
    const confirmMessage = document.getElementById('confirm-message');
    
    confirmMessage.textContent = message;
    confirmModal.style.display = 'block';

    const handler = (e) => {
        if(e.target.id === 'confirm-yes') {
            onConfirm();
            confirmModal.style.display = 'none';
            document.removeEventListener('click', handler);
        }
        if(e.target.id === 'confirm-no') {
            if(onCancel) onCancel();
            confirmModal.style.display = 'none';
            document.removeEventListener('click', handler);
        }
    };

    document.addEventListener('click', handler);
}

function handleEditExample(conflictId, modelTypy) {
    const contentElement = document.getElementById(`example-content-${conflictId}-${modelTypy}`);
    const modal = document.getElementById(`example-modal-${conflictId}-${modelTypy}`);
    const textarea = modal.querySelector('textarea');
    
    currentExample = {
        conflictId: conflictId,
        modelTypy: modelTypy,
        originalContent: contentElement.innerText,
        currentContent: contentElement.innerText
    };

    textarea.value = currentExample.originalContent;
    modal.style.display = 'block';
}








// nama saran

let originalContent = "";

function openEditModal(type, id) {
    const modal = document.getElementById(`modal-${type}-${id}`);
    const inputField = document.getElementById(`input-${type}-${id}`);
    const displayElement = document.querySelector(`#conflict-${type}-display-${id}`);
    
    originalContent = displayElement.innerText.trim();
    inputField.value = originalContent;
    
    inputField.addEventListener('input', function() {
        isContentChanged = (this.value.trim() !== originalContent);
    });

    if (modal) {
        modal.style.display = "block";
    }
}
function closeEditModal(type, id) {
    const modal = document.getElementById(`modal-${type}-${id}`);
    if (modal) {
        modal.style.display = "none";
    }
    isContentChanged = false;
}

function handleCancel(type, id) {
    const inputField = document.getElementById(`input-${type}-${id}`);
    const currentContent = inputField.value.trim();
    
    if (currentContent !== originalContent) {
        const confirmModal = document.getElementById("modal-confirm-cancel");
        confirmModal.dataset.type = type;
        confirmModal.dataset.id = id;
        confirmModal.style.display = "block";
    } else {
        closeEditModal(type, id);
    }
}

function closeConfirmCancelModal() {
    const confirmModal = document.getElementById("modal-confirm-cancel");
    if (confirmModal) {
        confirmModal.style.display = "none";
    }
}

function confirmCancel() {
    const confirmModal = document.getElementById("modal-confirm-cancel");
    const type = confirmModal.dataset.type;
    const id = confirmModal.dataset.id;
    
    const inputField = document.getElementById(`input-${type}-${id}`);
    inputField.value = originalContent;
    
    closeEditModal(type, id);
    closeConfirmCancelModal();
}

async function updateContent(type, id) {
    const inputField = document.getElementById(`input-${type}-${id}`);
    const newContent = inputField.value.trim();

    const payload = {
        [type]: newContent
    };

    try {
        const response = await fetch(`/update/${type}/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            document.getElementById(`conflict-${type}-display-${id}`).innerText = newContent;
            closeEditModal(type, id);
        } else {
            alert(`Gagal mengubah ${type}: ${result.message}`);
        }
    } catch (error) {
        alert(`Terjadi kesalahan: ${error.message}`);
    }
}


const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
document.querySelector('.animation-wrapper').appendChild(canvas);

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const squares = [];
const numSquares = 30;






// Function to create random colors
function getRandomColor() {
    const colors = ['#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9', '#92A8D1', '#955251', '#B565A7'];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Shape object
class Shape {
    constructor(x, y, size, speedX, speedY, color, type) {
        this.x = x;
        this.y = y;
        this.size = size;
        this.speedX = speedX;
        this.speedY = speedY;
        this.color = color;
        this.type = type; // Type of shape: 'square', 'circle', or 'triangle'
    }
    draw() {
        ctx.fillStyle = this.color;

        switch (this.type) {
            case 'square':
                ctx.fillRect(this.x, this.y, this.size, this.size);
                break;
            case 'circle':
                ctx.beginPath();
                ctx.arc(this.x + this.size / 2, this.y + this.size / 2, this.size / 2, 0, Math.PI * 2);
                ctx.fill();
                break;
            case 'triangle':
                ctx.beginPath();
                ctx.moveTo(this.x, this.y + this.size);
                ctx.lineTo(this.x + this.size / 2, this.y);
                ctx.lineTo(this.x + this.size, this.y + this.size);
                ctx.closePath();
                ctx.fill();
                break;
        }
    }
    update() {
        // Move randomly
        this.x += this.speedX;
        this.y += this.speedY;

        // Bounce if it hits the edges
        if (this.x < 0 || this.x + this.size > canvas.width) this.speedX *= -1;
        if (this.y < 0 || this.y + this.size > canvas.height) this.speedY *= -1;
    }
}

// Initialize shapes
const shapes = [];
for (let i = 0; i < 50; i++) {
    const size = Math.random() * 20 + 10; // Random size
    const x = Math.random() * canvas.width; // Random X position
    const y = Math.random() * canvas.height; // Random Y position
    const speedX = (Math.random() - 0.5) * 4; // Random speed X
    const speedY = (Math.random() - 0.5) * 4; // Random speed Y
    const color = getRandomColor();
    const types = ['square', 'circle', 'triangle'];
    const type = types[Math.floor(Math.random() * types.length)]; // Random shape
    shapes.push(new Shape(x, y, size, speedX, speedY, color, type));
}

// Animate the shapes
function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update and draw shapes
    for (let shape of shapes) {
        shape.update(); // Update position
        shape.draw();   // Draw shape
    }

    requestAnimationFrame(animate);
}

animate();

// Adjust canvas size on window resize
window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});




function toggleList(button, listId) {
    const list = document.getElementById(listId);
    const isExpanded = list.classList.contains('expanded');
    
    if(isExpanded) {
        list.classList.remove('expanded');
        button.querySelector('span').textContent = '▼ Tampilkan';
    } else {
        list.classList.add('expanded');
        button.querySelector('span').textContent = '▲ Sembunyikan';
    }
}



function toggleDetails(id) {
    const details = document.getElementById(id);
    details.style.display = details.style.display === 'none' ? 'block' : 'none';
}