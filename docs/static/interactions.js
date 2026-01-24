document.addEventListener('DOMContentLoaded', () => {
    // 1. Interactive Bit-Field Highlighting
    const bitBoxes = document.querySelectorAll('.bit-box');
    const operandRows = document.querySelectorAll('.operand-row');

    function highlight(name, active) {
        // Find bit boxes with this name
        bitBoxes.forEach(box => {
            if (box.dataset.op === name) {
                if(active) box.classList.add('highlight');
                else box.classList.remove('highlight');
            }
        });

        // Find operand rows with this name
        operandRows.forEach(row => {
            if (row.dataset.op === name) {
                if(active) row.classList.add('highlight');
                else row.classList.remove('highlight');
            }
        });
    }

    // Attach events to Bit Boxes
    bitBoxes.forEach(box => {
        if(box.dataset.op) { // Only if it has a name
            box.addEventListener('mouseenter', () => highlight(box.dataset.op, true));
            box.addEventListener('mouseleave', () => highlight(box.dataset.op, false));
        }
    });

    // Attach events to Operand Rows
    operandRows.forEach(row => {
        if(row.dataset.op) {
            row.addEventListener('mouseenter', () => highlight(row.dataset.op, true));
            row.addEventListener('mouseleave', () => highlight(row.dataset.op, false));
        }
    });
});
