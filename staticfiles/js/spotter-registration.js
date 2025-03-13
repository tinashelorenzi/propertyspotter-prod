//spotter-registration.js
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const form = document.getElementById('registrationForm');
    const steps = document.querySelectorAll('.form-step');
    const stepIndicators = document.querySelectorAll('.step');
    const nextButtons = document.querySelectorAll('.next-step');
    const prevButtons = document.querySelectorAll('.prev-step');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
    
    let currentStep = 0;

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Handle "Next" button clicks
    nextButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (validateStep(currentStep)) {
                currentStep++;
                updateSteps();
            }
        });
    });

    // Handle "Previous" button clicks
    prevButtons.forEach(button => {
        button.addEventListener('click', () => {
            currentStep--;
            updateSteps();
        });
    });

    // Validate each step
    function validateStep(step) {
        const currentStepElement = steps[step];
        const requiredFields = currentStepElement.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            field.classList.remove('is-invalid');
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
            }
        });

        // Step-specific validation
        if (step === 0) {
            // Email validation
            const emailInput = document.getElementById('email');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailInput.value)) {
                isValid = false;
                emailInput.classList.add('is-invalid');
            }

            // Password validation
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            
            if (password.length < 8) {
                isValid = false;
                document.getElementById('password').classList.add('is-invalid');
            }

            if (password !== confirmPassword) {
                isValid = false;
                document.getElementById('confirm_password').classList.add('is-invalid');
            }
        }

        // Step 2: Phone number validation
        if (step === 1) {
            const phoneInput = document.getElementById('phone');
            const phoneRegex = /^\+?[\d\s-]{10,}$/;
            if (!phoneRegex.test(phoneInput.value)) {
                isValid = false;
                phoneInput.classList.add('is-invalid');
            }
        }

        return isValid;
    }

    // Update steps visibility and indicators
    function updateSteps() {
        steps.forEach((step, index) => {
            step.classList.remove('active');
            stepIndicators[index].classList.remove('active', 'completed');
            
            if (index === currentStep) {
                step.classList.add('active');
                stepIndicators[index].classList.add('active');
            } else if (index < currentStep) {
                stepIndicators[index].classList.add('completed');
            }
        });
    }

    // Handle profile image preview
    const profileImageInput = document.getElementById('profile_image');
    const photoPreview = document.getElementById('photoPreview');

    profileImageInput?.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                alert('File size must be less than 5MB');
                this.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                photoPreview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateStep(currentStep)) {
            return;
        }

        // Show loading modal
        loadingModal.show();

        // Prepare form data
        const formData = new FormData(form);
        formData.append('role', 'Spotter'); // Set default role
        formData.append('is_active', 'true');
        formData.append('profile_complete', 'false');

        try {
            const response = await fetch('/api/users/register/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            });

            loadingModal.hide();

            if (response.ok) {
                successModal.show();
                
                // Optional: Redirect after successful registration
                successModal._element.addEventListener('hidden.bs.modal', () => {
                    window.location.href = '/login';
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Registration failed');
            }
        } catch (error) {
            loadingModal.hide();
            
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3';
            errorDiv.innerHTML = `
                <i class="fas fa-exclamation-circle me-2"></i>
                ${error.message || 'An error occurred during registration'}
            `;
            form.insertBefore(errorDiv, form.firstChild);

            // Remove error message after 5 seconds
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
    });

    // Add input event listeners for real-time validation
    const requiredInputs = form.querySelectorAll('[required]');
    requiredInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('is-invalid');
            }
        });
    });

    // Password strength indicator
    const passwordInput = document.getElementById('password');
    const strengthIndicator = document.createElement('div');
    strengthIndicator.className = 'password-strength mt-2';
    passwordInput.parentElement.appendChild(strengthIndicator);

    passwordInput.addEventListener('input', function() {
        const strength = checkPasswordStrength(this.value);
        updatePasswordStrengthIndicator(strength);
    });

    function checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        return strength;
    }

    function updatePasswordStrengthIndicator(strength) {
        const levels = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'];
        const colors = ['#dc3545', '#ffc107', '#fd7e14', '#20c997', '#198754'];
        
        strengthIndicator.innerHTML = `
            <div class="progress" style="height: 5px;">
                <div class="progress-bar" role="progressbar" 
                     style="width: ${(strength / 5) * 100}%; background-color: ${colors[strength - 1]}" 
                     aria-valuenow="${(strength / 5) * 100}" aria-valuemin="0" aria-valuemax="100">
                </div>
            </div>
            <small class="text-muted mt-1" style="color: ${colors[strength - 1]} !important">
                ${strength > 0 ? levels[strength - 1] : 'No Password'}
            </small>
        `;
    }
});