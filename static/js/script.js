/* ================================================================
   ROOT FINDER — Frontend Logic
   Communicates with Flask backend for equation solving
   ================================================================ */

(function () {
    'use strict';

    // ---- DOM References ----
    const equationInput   = document.getElementById('equation-input');
    const previewExpr     = document.getElementById('preview-expr');
    const previewStatus   = document.getElementById('preview-status');
    const btnBisection    = document.getElementById('btn-bisection');
    const btnNewton       = document.getElementById('btn-newton');
    const bisectionInputs = document.getElementById('bisection-inputs');
    const newtonInputs    = document.getElementById('newton-inputs');
    const rangeTitle      = document.getElementById('range-title');
    const toggleAdvBtn    = document.getElementById('toggle-advanced-btn');
    const advancedOpts    = document.getElementById('advanced-options');
    const computeBtn      = document.getElementById('compute-btn');
    const errorBanner     = document.getElementById('error-banner');
    const errorText       = document.getElementById('error-text');
    const resultsSection  = document.getElementById('results-section');
    const resultsMeta     = document.getElementById('results-meta');
    const tableHead       = document.getElementById('table-head');
    const tableBody       = document.getElementById('table-body');
    const answerValue     = document.getElementById('answer-value');
    const answerDetail    = document.getElementById('answer-detail');

    let selectedMethod = 'bisection';
    let validateTimer  = null;

    // ---- Method Selection ----
    function selectMethod(method) {
        selectedMethod = method;
        btnBisection.classList.toggle('active', method === 'bisection');
        btnNewton.classList.toggle('active', method === 'newton');

        if (method === 'bisection') {
            bisectionInputs.classList.remove('hidden');
            newtonInputs.classList.add('hidden');
            rangeTitle.textContent = 'Set Interval Range';
        } else {
            bisectionInputs.classList.add('hidden');
            newtonInputs.classList.remove('hidden');
            rangeTitle.textContent = 'Set Initial Guess';
        }
    }

    btnBisection.addEventListener('click', () => selectMethod('bisection'));
    btnNewton.addEventListener('click', () => selectMethod('newton'));

    // ---- Advanced Options Toggle ----
    toggleAdvBtn.addEventListener('click', () => {
        const isOpen = !advancedOpts.classList.contains('hidden');
        advancedOpts.classList.toggle('hidden', isOpen);
        toggleAdvBtn.classList.toggle('open', !isOpen);
    });

    // ---- Live Equation Preview ----
    equationInput.addEventListener('input', () => {
        clearTimeout(validateTimer);
        const val = equationInput.value.trim();
        if (!val) {
            previewExpr.textContent = '—';
            previewStatus.textContent = '';
            previewStatus.className = 'preview-status';
            return;
        }
        validateTimer = setTimeout(() => validateEquation(val), 350);
    });

    async function validateEquation(eq) {
        try {
            const res = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ equation: eq }),
            });
            const data = await res.json();
            if (data.valid) {
                previewExpr.textContent = `f(x) = ${data.pretty}`;
                previewStatus.textContent = '✓ valid';
                previewStatus.className = 'preview-status valid';
            } else {
                previewExpr.textContent = eq;
                previewStatus.textContent = '✗ invalid';
                previewStatus.className = 'preview-status invalid';
            }
        } catch {
            previewStatus.textContent = '';
        }
    }

    // ---- Compute ----
    computeBtn.addEventListener('click', () => compute());

    // Also allow pressing Enter in any input to compute
    document.querySelectorAll('input').forEach((inp) => {
        inp.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') compute();
        });
    });

    async function compute() {
        hideError();
        resultsSection.classList.add('hidden');

        const equation = equationInput.value.trim();
        if (!equation) {
            showError('Please enter an equation first.');
            return;
        }

        const tol     = parseFloat(document.getElementById('tolerance').value) || 0.0001;
        const maxIter = parseInt(document.getElementById('max-iter').value, 10) || 50;

        const payload = {
            equation,
            method: selectedMethod,
            tolerance: tol,
            maxIter,
        };

        if (selectedMethod === 'bisection') {
            const aVal = document.getElementById('range-a').value.trim();
            const bVal = document.getElementById('range-b').value.trim();
            if (aVal !== '') payload.a = parseFloat(aVal);
            if (bVal !== '') payload.b = parseFloat(bVal);
        } else {
            const x0Val = document.getElementById('initial-guess').value.trim();
            if (x0Val !== '') payload.x0 = parseFloat(x0Val);
        }

        // Show loading
        computeBtn.classList.add('loading');
        computeBtn.disabled = true;

        try {
            const res = await fetch('/api/solve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();

            if (!data.success) {
                showError(data.error || 'Something went wrong.');
                return;
            }

            // Fill auto-detected values back in the UI inputs
            if (data.auto_detected) {
                if (data.method === 'bisection') {
                    document.getElementById('range-a').value = data.a;
                    document.getElementById('range-b').value = data.b;
                } else if (data.method === 'newton') {
                    document.getElementById('initial-guess').value = data.x0;
                }
            }

            renderResults(data);
        } catch (err) {
            showError('Network error — is the server running?');
        } finally {
            computeBtn.classList.remove('loading');
            computeBtn.disabled = false;
        }
    }

    // ---- Render Results ----
    function renderResults(data) {
        // Meta tags
        const methodLabel = data.method === 'bisection' ? 'Bisection' : 'Newton-Raphson';
        let metaHTML = `
            <span class="meta-tag"><span class="tag-label">Method</span> ${methodLabel}</span>
            <span class="meta-tag"><span class="tag-label">f(x)</span> ${escapeHTML(data.equation)}</span>
        `;
        if (data.method === 'bisection') {
            metaHTML += `<span class="meta-tag"><span class="tag-label">Interval [a, b]</span> [${formatNum(data.a, 6)}, ${formatNum(data.b, 6)}]</span>`;
        } else {
            metaHTML += `<span class="meta-tag"><span class="tag-label">Initial Guess (x₀)</span> ${formatNum(data.x0, 6)}</span>`;
        }
        if (data.derivative) {
            metaHTML += `<span class="meta-tag"><span class="tag-label">f'(x)</span> ${escapeHTML(data.derivative)}</span>`;
        }
        if (data.auto_detected) {
            metaHTML += `<span class="meta-tag" style="background: rgba(139, 92, 246, 0.15); border-color: rgba(139, 92, 246, 0.4);"><span class="tag-label" style="color: var(--text-accent); font-weight:600;">✨ Auto-detected</span></span>`;
        }
        metaHTML += `<span class="meta-tag"><span class="tag-label">Iterations</span> ${data.table.length}</span>`;
        resultsMeta.innerHTML = metaHTML;

        // Table head
        let headHTML = '<tr>';
        data.headers.forEach((h) => {
            headHTML += `<th>${escapeHTML(h)}</th>`;
        });
        headHTML += '</tr>';
        tableHead.innerHTML = headHTML;

        // Table body
        let bodyHTML = '';
        data.table.forEach((row, idx) => {
            const isLast = idx === data.table.length - 1;
            bodyHTML += `<tr class="${isLast && data.converged ? 'highlight-row' : ''}">`;
            data.columns.forEach((col) => {
                let val = row[col];
                if (typeof val === 'number') {
                    val = formatNum(val);
                } else if (val === null || val === undefined) {
                    val = '—';
                }
                bodyHTML += `<td>${val}</td>`;
            });
            bodyHTML += '</tr>';
        });
        tableBody.innerHTML = bodyHTML;

        // Answer
        if (data.root !== null && data.root !== undefined) {
            answerValue.textContent = `x ≈ ${formatNum(data.root, 10)}`;
        } else {
            answerValue.textContent = '—';
        }

        const statusClass = data.converged ? 'converged' : 'not-converged';
        answerDetail.innerHTML = `<span class="${statusClass}">${escapeHTML(data.message)}</span>`;

        // Show results
        resultsSection.classList.remove('hidden');

        // Scroll into view
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ---- Helpers ----
    function showError(msg) {
        errorText.textContent = msg;
        errorBanner.classList.remove('hidden');
        errorBanner.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideError() {
        errorBanner.classList.add('hidden');
    }

    function escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatNum(n, digits) {
        if (digits === undefined) digits = 8;
        if (Number.isInteger(n)) return String(n);
        // Use toPrecision for cleaner display
        const s = n.toPrecision(digits);
        // Remove trailing zeros after decimal point for readability
        return parseFloat(s).toString();
    }
})();
