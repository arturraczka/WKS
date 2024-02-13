window.addEventListener('scroll', () => {
    const stickyElement = document.querySelector('.sticky-element');
    const content = document.querySelector('.content');
    const container = document.querySelector('.container');

    const containerRect = container.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();

    const isSticky = containerRect.top <= 0 && contentRect.bottom >= window.innerHeight;

    if (isSticky) {
        stickyElement.style.width = `${containerRect.width}px`;
        stickyElement.style.left = `${containerRect.left}px`;
    } else {
        stickyElement.style.width = 'auto';
        stickyElement.style.left = 'auto';
    }
});