document.addEventListener('DOMContentLoaded', () => {
    // Create cursor element
    const cursor = document.createElement('div');
    cursor.classList.add('custom-cursor');
    document.body.appendChild(cursor);

    const cursorInner = document.createElement('div');
    cursorInner.classList.add('custom-cursor-inner');
    document.body.appendChild(cursorInner);

    // Track mouse movement
    document.addEventListener('mousemove', (e) => {
        cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
        cursorInner.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
    });

    // Hover effects
    const interactiveElements = document.querySelectorAll('a, button, input, select, .upload-area, .file-item');

    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.classList.add('hover');
            cursorInner.classList.add('hover');
        });

        el.addEventListener('mouseleave', () => {
            cursor.classList.remove('hover');
            cursorInner.classList.remove('hover');
        });
    });

    // Add click effect
    document.addEventListener('mousedown', () => {
        cursor.classList.add('click');
        cursorInner.classList.add('click');
    });

    document.addEventListener('mouseup', () => {
        cursor.classList.remove('click');
        cursorInner.classList.remove('click');
    });
});
