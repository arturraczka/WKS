function showMessages() {
    const messages = document.querySelectorAll('.alert');
    messages.forEach((message) => {
        message.style.opacity = 1;
        message.style.visibility = 'visible';

        setTimeout(() => {
            message.style.opacity = 0;
            message.style.visibility = 'hidden';

            // Remove the message from the DOM after fading out
            setTimeout(() => {
                message.remove();
            }, 10); // Adjust the duration for fading out (0.5s in this example)
        }, 18000); // Hide the message after 18 seconds (18000 milliseconds)
    });
}

// Call the showMessages function when the page loads
document.addEventListener('DOMContentLoaded', showMessages);
