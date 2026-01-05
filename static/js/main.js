// Main JavaScript for Second game app

document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to anchor links
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add hover effects to vote options
    const voteOptions = document.querySelectorAll('.vote-option');
    voteOptions.forEach(option => {
        option.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(12px)';
        });
        
        option.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(8px)';
        });
    });

    // Add form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'var(--error)';
                    isValid = false;
                } else {
                    field.style.borderColor = 'var(--border-subtle)';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showFlashMessage('Please fill in all required fields.', 'error');
            }
        });
    });

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Add loading states to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        if (button.type === 'submit') {
            button.addEventListener('click', function() {
                const form = this.closest('form');
                if (form && form.checkValidity()) {
                    this.style.opacity = '0.7';
                    this.style.pointerEvents = 'none';
                    this.textContent = 'Loading...';
                }
            });
        }
    });

    // Add character counters to text inputs with maxlength
    const textInputs = document.querySelectorAll('input[type="text"][maxlength], textarea[maxlength]');
    textInputs.forEach(input => {
        const maxLength = input.getAttribute('maxlength');
        if (maxLength) {
            const counter = document.createElement('div');
            counter.className = 'char-counter';
            counter.style.cssText = `
                font-family: var(--font-mono);
                font-size: 0.8rem;
                color: var(--text-muted);
                text-align: right;
                margin-top: 0.25rem;
            `;
            
            const updateCounter = () => {
                const remaining = maxLength - input.value.length;
                counter.textContent = `${remaining} characters remaining`;
                if (remaining < 10) {
                    counter.style.color = 'var(--warning)';
                } else {
                    counter.style.color = 'var(--text-muted)';
                }
            };
            
            updateCounter();
            input.addEventListener('input', updateCounter);
            input.parentNode.appendChild(counter);
        }
    });
});

// Utility function to show flash messages dynamically
function showFlashMessage(message, type = 'info') {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
    
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        <span class="flash-icon">${type === 'success' ? '✓' : '⚠'}</span>
        ${message}
    `;
    
    flashContainer.appendChild(flash);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            flash.remove();
        }, 300);
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(container, mainContent.firstChild);
    return container;
}

// Add some visual flair with particle effects on wins
function celebrateWin() {
    const winnerCard = document.querySelector('.winner-card');
    if (winnerCard) {
        createConfetti();
    }
}

function createConfetti() {
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.style.cssText = `
            position: fixed;
            width: 10px;
            height: 10px;
            background: var(--accent-gold);
            z-index: 1000;
            pointer-events: none;
            border-radius: 50%;
            left: ${Math.random() * 100}vw;
            top: -10px;
            animation: fall ${Math.random() * 3 + 2}s linear forwards;
        `;
        document.body.appendChild(confetti);
        
        setTimeout(() => {
            confetti.remove();
        }, 5000);
    }
}

// Add the falling animation for confetti
const style = document.createElement('style');
style.textContent = `
    @keyframes fall {
        to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
    
    .char-counter {
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--text-muted);
        text-align: right;
        margin-top: 0.25rem;
    }
`;
document.head.appendChild(style);

// Initialize confetti on results page if there's a winner
if (document.querySelector('.winner-card')) {
    setTimeout(celebrateWin, 1000);
}