// leads.js

// Get agent ID and auth token on load
const currentAgentId = document.getElementById('agentId').value;
//const currentAgentId = "{{ USERDATA.id }}";
let currentLeadId = null;

document.addEventListener('DOMContentLoaded', async function() {
    // Wait for auth token to be available (from base template)
    if (!window.authToken) {
        await new Promise(resolve => {
            const checkToken = setInterval(() => {
                if (window.authToken) {
                    clearInterval(checkToken);
                    resolve();
                }
            }, 100);
        });
    }

    // Initial leads load
    await loadLeads();
    
    // Initialize modal handlers
    initializeModalHandlers();
});

let leadsData = []; // Store all leads data
// Main function to load leads data
async function loadLeads() {
    try {
        const response = await fetch(`/api/leads/by-agent/${currentAgentId}/`, {
            headers: {
                'Authorization': `Token ${window.authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch leads');
        }

        const leads = await response.json();
        leadsData = leads; // Store the leads data
        populateLeadsTable(leads);
    } catch (error) {
        console.error('Error loading leads:', error);
        showErrorToast('Failed to load leads data');
    }
}

// Populate leads table with data
function populateLeadsTable(leads) {
    const tableBody = document.getElementById('leadsTableBody');
    
    if (!leads.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No leads found</td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = leads.map(lead => `
        <tr>
            <td>
                <div class="d-flex flex-column">
                    <strong>${lead.property.property_type} - ${formatAddress(lead.property.address)}</strong>
                    <small class="text-muted">
                        ${lead.property.total_bedrooms} Beds • ${lead.property.total_bathrooms} Baths
                    </small>
                </div>
            </td>
            <td>
                <div class="d-flex flex-column">
                    <span>${lead.property.owner_name || 'N/A'}</span>
                    <small class="text-muted">${lead.property.owner_contact || 'No contact'}</small>
                </div>
            </td>
            <td>
                <span class="badge bg-${getStatusColor(lead.status)}">
                    ${lead.status}
                </span>
            </td>
            <td>
                ${lead.property.commission ? `R${formatMoney(lead.property.commission)}` : 'Not set'}
            </td>
            <td>
                <div class="d-flex flex-column">
                    <span>${formatDate(lead.created_at)}</span>
                    <small class="text-muted">
                        ${getTimeAgo(lead.created_at)}
                    </small>
                </div>
            </td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="showPropertyDetails('${lead.id}')">
                        Details
                    </button>
                    <button class="btn btn-sm btn-outline-success" 
                            onclick="showProgressModal('${lead.id}')">
                        Update Progress
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Property Details Modal Functions
function showPropertyDetails(leadId) {
    const lead = leadsData.find(l => l.id === leadId);
    if (!lead) {
        showErrorToast('Failed to find lead details');
        return;
    }

    populateDetailsModal(lead);
    const modal = new bootstrap.Modal(document.getElementById('propertyDetailsModal'));
    modal.show();
}

// Update populateDetailsModal to handle the nested response structure
function populateDetailsModal(lead) {
    // Populate property images carousel
    const carouselInner = document.getElementById('modalPropertyImages');
    if (lead.property.property_images && lead.property.property_images.length > 0) {
        carouselInner.innerHTML = lead.property.property_images.map((img, index) => `
            <div class="carousel-item ${index === 0 ? 'active' : ''}">
                <img src="${img.image}" class="d-block w-100" alt="Property Image ${index + 1}">
            </div>
        `).join('');
    } else {
        carouselInner.innerHTML = `
            <div class="carousel-item active">
                <div class="no-image-placeholder d-flex align-items-center justify-content-center bg-light" style="height: 300px;">
                    <span class="text-muted">No images available</span>
                </div>
            </div>
        `;
    }

    // Populate all modal fields
    document.getElementById('modalPropertyType').textContent = lead.property.property_type || 'N/A';
    document.getElementById('modalPropertyStatus').textContent = lead.status;
    document.getElementById('modalPropertyStatus').className = `badge bg-${getStatusColor(lead.status)}`;
    document.getElementById('modalAddress').textContent = lead.property.address || 'No address provided';
    document.getElementById('modalBedrooms').textContent = lead.property.total_bedrooms || 0;
    document.getElementById('modalBathrooms').textContent = lead.property.total_bathrooms || 0;
    
    document.getElementById('modalOwnerName').textContent = lead.property.owner_name || 'N/A';
    document.getElementById('modalOwnerContact').textContent = lead.property.owner_contact || 'N/A';
    document.getElementById('modalPrice').textContent = lead.property.price ? `R${formatMoney(lead.property.price)}` : 'Not set';
    document.getElementById('modalCommission').textContent = lead.property.commission ? `R${formatMoney(lead.property.commission)}` : 'Not set';
    
    document.getElementById('modalLeadSource').textContent = lead.property.lead_source || 'N/A';
    document.getElementById('modalReferenceName').textContent = lead.property.reference_name || 'N/A';
    document.getElementById('modalReferenceDetails').textContent = lead.property.reference_details || 'No details provided';
    
    document.getElementById('modalSpotterNotes').textContent = lead.property.spotter_notes || 'No spotter notes';
    document.getElementById('modalAgentNotes').textContent = lead.property.agent_notes || 'No agent notes';
    
    document.getElementById('modalCreatedAt').textContent = formatDate(lead.created_at);
    document.getElementById('modalUpdatedAt').textContent = formatDate(lead.property.updated_at);
}

// Progress Modal Functions
function initializeModalHandlers() {
    const saveProgressBtn = document.getElementById('saveProgress');
    const commissionInput = document.getElementById('commissionAmount');
    const statusSelect = document.getElementById('propertyStatus');

    // Save Progress Button Handler
    saveProgressBtn.addEventListener('click', async () => {
        const commission = commissionInput.value;
        const status = statusSelect.value;
        const propertyListingLink = document.getElementById('propertyListingLink').value;
        console.log("Property Listing Link:", propertyListingLink);

        // Validation
        if (!status) {
            showErrorToast('Please select a status');
            return;
        }

        if (!commission && status !== 'Owner Not Found') {
            showErrorToast('Commission amount is required for this status');
            return;
        }

        try {
            // Update commission if provided
            if (commission) {
                const commissionResponse = await fetch(`/api/leads/${currentLeadId}/set-commission/`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Token ${window.authToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ commission: commission })
                });

                if (!commissionResponse.ok) {
                    throw new Error('Failed to update commission');
                }
            }

            // Update status
            const statusResponse = await fetch(`/api/leads/${currentLeadId}/update-status/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Token ${window.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: status, propertyListingLink: propertyListingLink })
            });
            if (!statusResponse.ok) {
                throw new Error('Failed to update status');
            }

            showSuccessToast('Progress updated successfully!');

            // Close modal and refresh
            const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
            progressModal.hide();
            await loadLeads();

        } catch (error) {
            console.error('Error updating progress:', error);
            showErrorToast('Failed to update progress');
        }
    });

    // Status Selection Handler
    statusSelect.addEventListener('change', () => {
        const helpText = document.getElementById('statusHelpText');
        const commission = commissionInput.value;
        const selectedStatus = statusSelect.value;

        if (selectedStatus === 'Owner Not Found' && commission) {
            helpText.textContent = 'Warning: Cannot set status to Owner Not Found when commission is specified';
            statusSelect.value = '';
        } else if (!commission && selectedStatus !== 'Owner Not Found') {
            helpText.textContent = 'Please specify commission amount first';
        } else {
            helpText.textContent = '';
        }
    });
}

async function showProgressModal(leadId) {
    currentLeadId = leadId;
    
    // Find the current lead data from our stored leads
    const lead = leadsData.find(l => l.id === leadId);
    if (!lead) {
        showErrorToast('Failed to find lead details');
        return;
    }

    // Get the form elements
    const commissionInput = document.getElementById('commissionAmount');
    const statusSelect = document.getElementById('propertyStatus');
    const helpText = document.getElementById('statusHelpText');
    
    // Pre-populate and handle commission field
    if (lead.property.commission) {
        commissionInput.value = lead.property.commission;
        commissionInput.disabled = true; // Disable the input if commission exists
        helpText.textContent = 'Commission amount has already been set';
    } else {
        commissionInput.value = '';
        commissionInput.disabled = false;
        helpText.textContent = '';
    }

    // Set current status
    statusSelect.value = lead.status;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('progressModal'));
    modal.show();
}

// Utility Functions
function formatAddress(address) {
    if (!address) return 'No address';
    return address.length > 30 ? address.substring(0, 30) + '...' : address;
}

function formatMoney(amount) {
    return new Intl.NumberFormat('en-ZA').format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-ZA', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 30) return `${diffDays} days ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
}

function getStatusColor(status) {
    const colors = {
        'New Submission': 'primary',
        'Unsuccessful': 'danger',
        'Pending Mandate': 'warning',
        'Already Listed': 'info',
        'Listed': 'success',
        'Sold': 'success',
        'Commission Paid': 'success',
        'Owner Not Found': 'secondary',
        'Other Sole Mandate': 'info'
    };
    return colors[status] || 'secondary';
}

function showSuccessToast(message) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'success',
        title: message,
        showConfirmButton: false,
        timer: 3000
    });
}

function showErrorToast(message) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'error',
        title: message,
        showConfirmButton: false,
        timer: 3000
    });
}