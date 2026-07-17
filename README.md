# Root Finder — Numerical Methods Calculator

A beautiful, high-performance dark-themed web application to compute the roots of equations using numerical analysis methods. Built with a Flask backend and a modern glassmorphic frontend.

## ✨ Features

- **Implicit Multiplication Parsing**: Allows inputs like `5x`, `sin(x)-5x+2`, or `(x+1)(x-2)` without needing explicit `*` operators, powered by SymPy's parsing transformations.
- **Bisection Method**:
  - Auto-scans and resolves correct sign-changing intervals `[a, b]` if left blank.
  - Returns step-by-step intermediate iterations (`n`, `a`, `b`, `c`, `f(a)`, `f(b)`, `f(c)`, `Error`).
- **Newton-Raphson Method**:
  - Automatically calculates symbolic derivatives $f'(x)$ at runtime.
  - Automatically estimates suitable initial guesses $x_0$ if left blank.
  - Returns detailed tangent-line convergence iterations (`n`, `x_n`, `f(x_n)`, `f'(x_n)`, `x_n+1`, `Error`).
- **Rich User Interface**:
  - Fully responsive premium dark layout with subtle animated background glows.
  - Interactive validation status badges for real-time mathematical expression syntax checking.
  - Auto-populates resolved values back into form fields.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SymPy
- **Frontend**: HTML5, Vanilla CSS3 (Custom variables, glassmorphism), JavaScript (Fetch API, DOM manipulation)

## 🚀 Installation & Running Locally

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/SaifHassanEmon/RootFInder.git
   cd RootFInder
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Server**:
   ```bash
   python app.py
   ```

4. Open `http://127.0.0.1:5000` in your web browser.
