from flask import Flask, render_template, request, jsonify
import sympy as sp
import math

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

def parse_equation(equation_str):
    """Parse a user-provided equation string into a SymPy expression."""
    x = sp.Symbol('x')
    # Allow common math notations
    equation_str = equation_str.replace('^', '**')
    
    transformations = standard_transformations + (implicit_multiplication_application,)
    expr = parse_expr(
        equation_str,
        transformations=transformations,
        local_dict={'x': x, 'e': sp.E, 'pi': sp.pi}
    )
    return expr, x


def safe_eval(f, val):
    """Evaluate a lambdified function, returning None on math errors."""
    try:
        result = f(val)
        if result is None or math.isnan(result) or math.isinf(result):
            return None
        return result
    except Exception:
        return None


def find_bisection_interval(f_lambda):
    """Scan values of x outward to find an interval [a, b] where f(a)*f(b) < 0."""
    points = [0.0]
    steps = [0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0]
    for step in steps:
        points.append(step)
        points.append(-step)
    
    points = sorted(list(set(points)))
    
    evals = []
    for p in points:
        val = safe_eval(f_lambda, p)
        if val is not None and not math.isnan(val) and not math.isinf(val):
            if abs(val) < 1e-12:
                # Exact or extremely close to root, return a range around it
                # Check 1.0 step
                val_left = safe_eval(f_lambda, p - 1.0)
                val_right = safe_eval(f_lambda, p + 1.0)
                if val_left is not None and val_right is not None and val_left * val_right < 0:
                    return p - 1.0, p + 1.0
                # Check 0.1 step
                val_left = safe_eval(f_lambda, p - 0.1)
                val_right = safe_eval(f_lambda, p + 0.1)
                if val_left is not None and val_right is not None and val_left * val_right < 0:
                    return p - 0.1, p + 0.1
                # Fallback range
                return p - 1.0, p + 1.0
            evals.append((p, val))
            
    # Search for any adjacent points with opposite signs
    for i in range(len(evals) - 1):
        x1, y1 = evals[i]
        x2, y2 = evals[i+1]
        if y1 * y2 < 0:
            return x1, x2
            
    return None, None


def find_initial_guess(f_lambda):
    """Automatically find an initial guess x0 for Newton-Raphson method."""
    a, b = find_bisection_interval(f_lambda)
    if a is not None and b is not None:
        return (a + b) / 2.0
    
    # Otherwise, check a range of points and find the one that minimizes |f(x)|
    test_points = [0.0, 1.0, -1.0, 2.0, -2.0, 0.5, -0.5, 5.0, -5.0, 10.0, -10.0]
    best_x = 0.0
    best_val = float('inf')
    for x in test_points:
        val = safe_eval(f_lambda, x)
        if val is not None:
            abs_val = abs(val)
            if abs_val < best_val:
                best_val = abs_val
                best_x = x
    return best_x

# ---------------------------------------------------------------------------
# Bisection Method
# ---------------------------------------------------------------------------

def bisection(f_lambda, a, b, tol, max_iter):
    """
    Bisection root-finding method.
    Returns (table_rows, root, converged, message).
    """
    fa = safe_eval(f_lambda, a)
    fb = safe_eval(f_lambda, b)

    if fa is None or fb is None:
        return [], None, False, "Cannot evaluate the function at one or both endpoints."

    if fa * fb > 0:
        return [], None, False, (
            f"Invalid range: f({a}) = {fa:.6g} and f({b}) = {fb:.6g} have the same sign. "
            "The Bisection method requires f(a) and f(b) to have opposite signs."
        )

    rows = []
    for i in range(1, max_iter + 1):
        c = (a + b) / 2.0
        fc = safe_eval(f_lambda, c)
        if fc is None:
            return rows, None, False, f"Cannot evaluate f({c})."

        fa_val = safe_eval(f_lambda, a)
        fb_val = safe_eval(f_lambda, b)

        error = abs(b - a) / 2.0

        rows.append({
            'iter': i,
            'a': round(a, 10),
            'b': round(b, 10),
            'c': round(c, 10),
            'fa': round(fa_val, 10) if fa_val is not None else None,
            'fb': round(fb_val, 10) if fb_val is not None else None,
            'fc': round(fc, 10),
            'error': round(error, 10),
        })

        if abs(fc) < 1e-15 or error < tol:
            return rows, c, True, f"Converged after {i} iterations."

        if fa_val * fc < 0:
            b = c
        else:
            a = c

    return rows, (a + b) / 2.0, False, f"Did not converge within {max_iter} iterations. Best approximation returned."

# ---------------------------------------------------------------------------
# Newton-Raphson Method
# ---------------------------------------------------------------------------

def newton_raphson(f_lambda, fp_lambda, x0, tol, max_iter):
    """
    Newton-Raphson root-finding method.
    Returns (table_rows, root, converged, message).
    """
    rows = []
    xn = x0

    for i in range(1, max_iter + 1):
        fxn = safe_eval(f_lambda, xn)
        fpxn = safe_eval(fp_lambda, xn)

        if fxn is None:
            return rows, None, False, f"Cannot evaluate f({xn})."
        if fpxn is None or abs(fpxn) < 1e-15:
            return rows, None, False, (
                f"Derivative is zero (or undefined) at x = {xn:.6g}. "
                "Newton-Raphson cannot continue. Try a different initial guess."
            )

        xn1 = xn - fxn / fpxn
        error = abs(xn1 - xn)

        rows.append({
            'iter': i,
            'xn': round(xn, 10),
            'fxn': round(fxn, 10),
            'fpxn': round(fpxn, 10),
            'xn1': round(xn1, 10),
            'error': round(error, 10),
        })

        if abs(fxn) < 1e-15 or error < tol:
            return rows, xn1, True, f"Converged after {i} iterations."

        xn = xn1

    return rows, xn, False, f"Did not converge within {max_iter} iterations. Best approximation returned."

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/validate', methods=['POST'])
def validate_equation():
    """Validate that an equation string can be parsed."""
    data = request.get_json()
    eq_str = data.get('equation', '').strip()
    if not eq_str:
        return jsonify({'valid': False, 'error': 'Equation is empty.'})
    try:
        expr, x = parse_equation(eq_str)
        # Try to evaluate at a test point to ensure it works
        f = sp.lambdify(x, expr, modules=['math'])
        f(1.0)
        pretty = str(expr)
        return jsonify({'valid': True, 'pretty': pretty})
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)})


@app.route('/api/solve', methods=['POST'])
def solve():
    """Run the selected root-finding algorithm and return the iteration table."""
    data = request.get_json()
    eq_str = data.get('equation', '').strip()
    method = data.get('method', 'bisection')
    tol = float(data.get('tolerance', 0.0001))
    max_iter = int(data.get('maxIter', 50))

    # Parse equation
    try:
        expr, x = parse_equation(eq_str)
        f = sp.lambdify(x, expr, modules=['math'])
    except Exception as e:
        return jsonify({'success': False, 'error': f'Invalid equation: {e}'}), 400

    if method == 'bisection':
        a_val = data.get('a')
        b_val = data.get('b')
        
        if a_val is None or a_val == "" or b_val is None or b_val == "":
            a, b = find_bisection_interval(f)
            if a is None or b is None:
                return jsonify({'success': False, 'error': 'Could not automatically find an interval where the function changes sign. Please specify a range manually.'}), 400
            auto_detected = True
        else:
            try:
                a, b = float(a_val), float(b_val)
                auto_detected = False
            except ValueError:
                return jsonify({'success': False, 'error': 'Lower and upper bounds must be numeric.'}), 400
            
            if a >= b:
                return jsonify({'success': False, 'error': 'Lower bound (a) must be less than upper bound (b).'}), 400

        rows, root, converged, message = bisection(f, a, b, tol, max_iter)
        columns = ['iter', 'a', 'b', 'c', 'fa', 'fb', 'fc', 'error']
        headers = ['n', 'a', 'b', 'c = (a+b)/2', 'f(a)', 'f(b)', 'f(c)', '|Error|']

    elif method == 'newton':
        x0_val = data.get('x0')
        if x0_val is None or x0_val == "":
            x0 = find_initial_guess(f)
            auto_detected = True
        else:
            try:
                x0 = float(x0_val)
                auto_detected = False
            except ValueError:
                return jsonify({'success': False, 'error': 'Initial guess must be numeric.'}), 400

        # Compute symbolic derivative
        try:
            expr_prime = sp.diff(expr, x)
            fp = sp.lambdify(x, expr_prime, modules=['math'])
            derivative_str = str(expr_prime)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Could not compute derivative: {e}'}), 400

        rows, root, converged, message = newton_raphson(f, fp, x0, tol, max_iter)
        columns = ['iter', 'xn', 'fxn', 'fpxn', 'xn1', 'error']
        headers = ['n', 'xₙ', 'f(xₙ)', "f'(xₙ)", 'xₙ₊₁', '|Error|']
    else:
        return jsonify({'success': False, 'error': 'Unknown method.'}), 400

    result = {
        'success': True,
        'converged': converged,
        'message': message,
        'root': root,
        'table': rows,
        'columns': columns,
        'headers': headers,
        'method': method,
        'equation': str(expr),
        'auto_detected': auto_detected
    }

    if method == 'bisection':
        result['a'] = a
        result['b'] = b
    elif method == 'newton':
        result['x0'] = x0
        result['derivative'] = derivative_str

    return jsonify(result)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
