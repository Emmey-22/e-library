// Admin Dashboard JavaScript

// Debugging version - add this at the top of admin.js
console.log("Admin JS loaded");

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded");
    initAdminDashboard();
});

function initAdminDashboard() {
    console.log("Initializing admin dashboard");
    
    // Debug sidebar links
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    console.log(`Found ${sidebarLinks.length} sidebar links`);
    
    setupDarkMode();
    setupSidebarNavigation();
    loadDefaultSection();
}

function setupSidebarNavigation() {
    console.log("Setting up sidebar navigation");
    
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    sidebarLinks.forEach(link => {
        console.log(`Setting up click handler for: ${link.textContent.trim()}`);
        
        link.addEventListener('click', function(e) {
            console.log(`Link clicked: ${this.textContent.trim()}`);
            
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const sectionId = this.getAttribute('data-section');
                console.log(`Showing section: ${sectionId}`);
                showSection(sectionId);
                setActiveLink(this);
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard
    initAdminDashboard();
});

function initAdminDashboard() {
    // Set up dark mode toggle
    setupDarkMode();
    
    // Set up sidebar navigation
    setupSidebarNavigation();
    
    // Load the default section
    loadDefaultSection();
}

// Dark Mode Functionality
function setupDarkMode() {
    const toggle = document.getElementById('darkModeToggle');
    if (!toggle) return;

    // Set initial state from localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
        toggle.checked = true;
    }
    
    // Toggle dark/light mode
    toggle.addEventListener('change', function() {
        const theme = this.checked ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
    });
}

// Sidebar Navigation
function setupSidebarNavigation() {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const sectionId = this.getAttribute('data-section');
                showSection(sectionId);
                setActiveLink(this);
            }
        });
    });
}

// Load Default Section
function loadDefaultSection() {
    const firstSection = document.querySelector('.sidebar-link[data-section]');
    if (firstSection) {
        showSection(firstSection.getAttribute('data-section'));
        setActiveLink(firstSection);
    }
}

// Show Section Content
async function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    const activeSection = document.getElementById(sectionId);
    if (!activeSection) return;
    
    activeSection.style.display = 'block';
    
    // Load content if empty
    if (activeSection.innerHTML.trim() === '') {
        await loadSectionContent(sectionId);
    }
}

// Set Active Link Style
function setActiveLink(activeLink) {
    // Remove active class from all links
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to clicked link
    activeLink.classList.add('active');
}

// Load Section Content Dynamically
async function loadSectionContent(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    
    section.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;

    try {
        let response;
        let htmlContent;
        
        switch(sectionId) {
            case 'manage-lecturers':
                response = await fetchWithErrorHandling('/admin/api/lecturers');
                htmlContent = generateLecturersTable(response);
                break;
                
            case 'manage-courses':
                response = await fetchWithErrorHandling('/admin/api/courses');
                htmlContent = generateCoursesTable(response);
                break;
                
            case 'assign-courses':
                response = await fetchWithErrorHandling('/admin/api/assignments');
                htmlContent = generateAssignmentsTable(response);
                break;
                
            case 'manage-materials':
                response = await fetchWithErrorHandling('/admin/api/materials');
                htmlContent = generateMaterialsTable(response);
                break;
                
            default:
                htmlContent = `<div class="alert alert-info">Section content will be loaded here</div>`;
        }
        
        section.innerHTML = htmlContent;
        initializeSectionInteractions(sectionId);
    } catch (error) {
        console.error('Error loading section:', error);
        section.innerHTML = `
            <div class="alert alert-danger">
                Failed to load content. Please try again.
                <br><small>${error.message}</small>
            </div>
        `;
    }
}

// Generate Lecturers Table HTML
function generateLecturersTable(lecturers) {
    return `
        <div class="card shadow rounded-4 p-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4>Lecturer Management</h4>
                <button class="btn btn-sm btn-primary" onclick="showSection('add-lecturer')">
                    <i class="bi bi-plus-lg"></i> Add Lecturer
                </button>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Assigned Courses</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${lecturers.map(lecturer => `
                            <tr>
                                <td>${lecturer.username}</td>
                                <td>${lecturer.email}</td>
                                <td>
                                    ${lecturer.assigned_courses && lecturer.assigned_courses.length > 0 ? 
                                        lecturer.assigned_courses.map(c => c.course_code).join(', ') : 
                                        'None'}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="editLecturer(${lecturer.id})">
                                            <i class="bi bi-pencil"></i> Edit
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="deleteLecturer(${lecturer.id})">
                                            <i class="bi bi-trash"></i> Delete
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// Generate Courses Table HTML
function generateCoursesTable(courses) {
    return `
        <div class="card shadow rounded-4 p-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4>Course Management</h4>
                <button class="btn btn-sm btn-primary" onclick="showSection('add-course')">
                    <i class="bi bi-plus-lg"></i> Add Course
                </button>
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Course Code</th>
                            <th>Title</th>
                            <th>Level</th>
                            <th>Assigned Lecturer</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${courses.map(course => `
                            <tr>
                                <td>${course.course_code}</td>
                                <td>${course.course_title}</td>
                                <td>${course.level}</td>
                                <td>
                                    ${course.lecturer || 'Not assigned'}
                                </td>
                                <td>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary" onclick="editCourse(${course.id})">
                                            <i class="bi bi-pencil"></i> Edit
                                        </button>
                                        <button class="btn btn-outline-danger" onclick="deleteCourse(${course.id})">
                                            <i class="bi bi-trash"></i> Delete
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// Initialize Section Interactions
function initializeSectionInteractions(sectionId) {
    // Initialize any interactive elements specific to each section
    switch(sectionId) {
        case 'manage-lecturers':
            // Initialize any lecturer-specific interactions
            break;
        case 'manage-courses':
            // Initialize any course-specific interactions
            break;
        // Add other cases as needed
    }
}

// Fetch with Error Handling
async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Edit Lecturer
async function editLecturer(lecturerId) {
    try {
        const lecturer = await fetchWithErrorHandling(`/admin/api/lecturers/${lecturerId}`);
        
        document.getElementById('editLecturerId').value = lecturer.id;
        document.getElementById('editLecturerUsername').value = lecturer.username;
        document.getElementById('editLecturerEmail').value = lecturer.email;
        
        const modal = new bootstrap.Modal(document.getElementById('editLecturerModal'));
        modal.show();
    } catch (error) {
        showToast(`Failed to load lecturer: ${error.message}`, 'error');
    }
}

// Save Lecturer Changes
async function saveLecturerChanges() {
    const formData = new FormData();
    formData.append('id', document.getElementById('editLecturerId').value);
    formData.append('username', document.getElementById('editLecturerUsername').value);
    formData.append('email', document.getElementById('editLecturerEmail').value);
    
    const password = document.getElementById('editLecturerPassword').value;
    if (password) {
        formData.append('password', password);
    }
    
    try {
        const data = await fetchWithErrorHandling('/admin/api/lecturers/update', {
            method: 'POST',
            body: formData
        });
        
        if (data.success) {
            showToast('Lecturer updated successfully', 'success');
            loadSectionContent('manage-lecturers');
            bootstrap.Modal.getInstance(document.getElementById('editLecturerModal')).hide();
        } else {
            showToast(data.error || 'Failed to update lecturer', 'error');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Delete Lecturer
async function deleteLecturer(lecturerId) {
    if (!confirm('Are you sure you want to delete this lecturer?')) return;
    
    try {
        const data = await fetchWithErrorHandling(`/admin/api/lecturers/${lecturerId}`, {
            method: 'DELETE'
        });
        
        if (data.success) {
            showToast('Lecturer deleted successfully', 'success');
            loadSectionContent('manage-lecturers');
        } else {
            showToast(data.error || 'Failed to delete lecturer', 'error');
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0 mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    
    // Remove toast after it hides
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}