// leads.js

// Get agent ID and auth token on load
const currentAgentId = document.getElementById('agentId').value;
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
                    <strong>${lead.property_type} - ${formatAddress(lead.address)}</strong>
                    <small class="text-muted">
                        ${lead.total_bedrooms} Beds • ${lead.total_bathrooms} Baths
                    </small>
                </div>
            </td>
            <td>
                <div class="d-flex flex-column">
                    <span>${lead.owner_name || 'N/A'}</span>
                    <small class="text-muted">${lead.owner_contact || 'No contact'}</small>
                </div>
            </td>
            <td>
                <span class="badge bg-${getStatusColor(lead.status)}">
                    ${lead.status}
                </span>
            </td>
            <td>
                ${lead.commission ? `R${formatMoney(lead.commission)}` : 'Not set'}
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
async function showPropertyDetails(leadId) {
    currentLeadId = leadId;
    try {
        const response = await fetch(`/api/leads/by-agent/${leadId}/`, {
            headers: {
                'Authorization': `Token ${window.authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch lead details');
        }

        const lead = await response.json();
        populateDetailsModal(lead);
        const modal = new bootstrap.Modal(document.getElementById('propertyDetailsModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading lead details:', error);
        showErrorToast('Failed to load property details');
    }
}

function populateDetailsModal(lead) {
    // Populate property images carousel
    const carouselInner = document.getElementById('modalPropertyImages');
    if (lead.image_urls && lead.image_urls.length > 0) {
        carouselInner.innerHTML = lead.image_urls.map((url, index) => `
            <div class="carousel-item ${index === 0 ? 'active' : ''}">
                <img src="${url}" class="d-block w-100" alt="Property Image ${index + 1}">
            </div>
        `).join('');
    } else {
        carouselInner.innerHTML = `
            <div class="carousel-item active">
                <div class="no-image-placeholder">No images available</div>
            </div>
        `;
    }

    // Populate all modal fields
    document.getElementById('modalPropertyType').textContent = lead.property_type;
    document.getElementById('modalPropertyStatus').textContent = lead.status;
    document.getElementById('modalPropertyStatus').className = `badge bg-${getStatusColor(lead.status)}`;
    document.getElementById('modalAddress').textContent = lead.address || 'No address provided';
    document.getElementById('modalBedrooms').textContent = lead.total_bedrooms;
    document.getElementById('modalBathrooms').textContent = lead.total_bathrooms;
    
    document.getElementById('modalOwnerName').textContent = lead.owner_name || 'N/A';
    document.getElementById('modalOwnerContact').textContent = lead.owner_contact || 'N/A';
    document.getElementById('modalPrice').textContent = lead.price ? `R${formatMoney(lead.price)}` : 'Not set';
    document.getElementById('modalCommission').textContent = lead.commission ? `R${formatMoney(lead.commission)}` : 'Not set';
    
    document.getElementById('modalLeadSource').textContent = lead.lead_source || 'N/A';
    document.getElementById('modalReferenceName').textContent = lead.reference_name || 'N/A';
    document.getElementById('modalReferenceDetails').textContent = lead.reference_details || 'No details provided';
    
    document.getElementById('modalSpotterNotes').textContent = lead.spotter_notes || 'No spotter notes';
    document.getElementById('modalAgentNotes').textContent = lead.agent_notes || 'No agent notes';
    
    document.getElementById('modalCreatedAt').textContent = formatDate(lead.created_at);
    document.getElementById('modalUpdatedAt').textContent = formatDate(lead.updated_at);
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
                body: JSON.stringify({ status: status })
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

function showProgressModal(leadId) {
    currentLeadId = leadId;
    
    // Reset form
    document.getElementById('commissionAmount').value = '';
    document.getElementById('propertyStatus').value = '';
    document.getElementById('statusHelpText').textContent = '';
    
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