document.addEventListener('DOMContentLoaded', () => {
    // 1. Interactive Bit-Field Highlighting
    const bitBoxes = document.querySelectorAll('.bit-box');
    const operandRows = document.querySelectorAll('.operand-row');

    const tooltip = document.getElementById('bit-tooltip');

    function highlight(name, active) {
        let descText = "";

        // 1. Highlight Bit Boxes
        bitBoxes.forEach(box => {
            if (box.dataset.op === name) {
                if(active) box.classList.add('highlight');
                else box.classList.remove('highlight');
            }
        });

        // 2. Highlight Operand Rows & Grab Description
        operandRows.forEach(row => {
            if (row.dataset.op === name) {
                if(active) {
                    row.classList.add('highlight');
                    // Grab the description from the second span in the row
                    const descSpan = row.querySelectorAll('span')[1]; 
                    if (descSpan) descText = descSpan.innerText;
                } else {
                    row.classList.remove('highlight');
                }
            }
        });

        // 3. Update Tooltip
        if (tooltip) {
            if (active) {
                // If we found a description in operands, use it. 
                // Otherwise, check if it looks like a fixed binary value (0/1) or Hex
                if (descText) {
                    tooltip.innerText = `${name}: ${descText}`;
                    tooltip.style.opacity = '1';
                } else if (/^[01]+$/.test(name)) {
                    tooltip.innerText = "Fixed Opcode Bits";
                    tooltip.style.opacity = '1';
                } else {
                    // Fallback for things like 'opcode' or 'func3' that aren't operands
                    tooltip.innerText = name; 
                    tooltip.style.opacity = '1';
                }
            } else {
                tooltip.style.opacity = '0';
            }
        }
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

    // --- New: Copy to Clipboard Logic ---
    document.querySelectorAll('.code-block').forEach(block => {
        // 1. Create the button
        const button = document.createElement('button');
        button.className = 'copy-btn';
        button.innerHTML = '📋';
        button.ariaLabel = 'Copy code';
        
        // 2. Add click handler
        button.addEventListener('click', () => {
            navigator.clipboard.writeText(block.innerText.trim());
            
            // Visual feedback
            const originalText = button.innerHTML;
            button.innerHTML = '✅';
            setTimeout(() => button.innerHTML = originalText, 2000);
        });

        // 3. Append to the block
        block.style.position = 'relative';
        block.appendChild(button);
    });
});
