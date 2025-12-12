import streamlit as st
import json
import os
import hashlib
import math
import re
from datetime import datetime
from typing import Tuple, Optional, List, Dict, Any

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="Advanced Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

USERS_FILE = "users.json"
HISTORY_FILE = "histories.json"
MAX_HISTORY = 100
HISTORY_DISPLAY = 30

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
    }
    .calculator-display {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        font-size: 24px;
        font-family: 'Courier New', monospace;
        margin-bottom: 20px;
        min-height: 60px;
        word-wrap: break-word;
    }
    .history-item {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 8px;
        border-left: 3px solid #4CAF50;
    }
    .error-box {
        background-color: #ffebee;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA MODELS ====================
class User:
    def __init__(self, username: str, password_hash: str, created_at: str):
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "password": self.password_hash,
            "created_at": self.created_at
        }

class CalculationEntry:
    def __init__(self, expr: str, result: str, timestamp: str):
        self.expr = expr
        self.result = result
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "expr": self.expr,
            "result": self.result,
            "timestamp": self.timestamp
        }

# ==================== UTILITY FUNCTIONS ====================
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def load_json_file(path: str) -> Dict[str, Any]:
    """Load JSON file with error handling"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            st.error(f"Error loading {path}: {str(e)}")
            return {}
    return {}

def save_json_file(path: str, data: Dict[str, Any]) -> bool:
    """Save JSON file with error handling"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        st.error(f"Error saving {path}: {str(e)}")
        return False

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be at most 20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

# ==================== USER MANAGEMENT ====================
def create_user(username: str, password: str) -> Tuple[bool, str]:
    """Create a new user account"""
    username = username.strip()
    
    # Validate input
    valid, msg = validate_username(username)
    if not valid:
        return False, msg
    
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    
    users = load_json_file(USERS_FILE)
    
    if username in users:
        return False, "Username already exists"
    
    user = User(username, hash_password(password), datetime.utcnow().isoformat())
    users[username] = user.to_dict()
    
    if save_json_file(USERS_FILE, users):
        return True, "Account created successfully! You can now log in."
    return False, "Error creating account"

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user credentials"""
    username = username.strip()
    users = load_json_file(USERS_FILE)
    
    if username in users:
        stored_hash = users[username].get("password")
        return stored_hash == hash_password(password)
    return False

# ==================== HISTORY MANAGEMENT ====================
def load_history(username: str) -> List[Dict[str, str]]:
    """Load calculation history for a user"""
    histories = load_json_file(HISTORY_FILE)
    return histories.get(username, [])

def append_history(username: str, entry: CalculationEntry) -> bool:
    """Append calculation to user history"""
    histories = load_json_file(HISTORY_FILE)
    histories.setdefault(username, [])
    histories[username].insert(0, entry.to_dict())
    histories[username] = histories[username][:MAX_HISTORY]
    return save_json_file(HISTORY_FILE, histories)

def clear_history(username: str) -> bool:
    """Clear user's calculation history"""
    histories = load_json_file(HISTORY_FILE)
    if username in histories:
        histories.pop(username)
        return save_json_file(HISTORY_FILE, histories)
    return True

# ==================== CALCULATOR ENGINE ====================
def preprocess_expression(expr: str) -> str:
    """Preprocess expression for evaluation"""
    expr = expr.strip()
    # Replace percentage
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1/100)', expr)
    # Handle implicit multiplication: 2pi -> 2*pi, 3(4) -> 3*(4)
    expr = re.sub(r'(\d)([a-z])', r'\1*\2', expr)
    expr = re.sub(r'(\d)\(', r'\1*(', expr)
    expr = re.sub(r'\)(\d)', r')*\1', expr)
    expr = re.sub(r'\)\(', r')*(', expr)
    return expr

def safe_eval(expr: str) -> Tuple[Optional[float], Optional[str]]:
    """Safely evaluate mathematical expression"""
    try:
        # Build safe namespace
        safe_dict = {
            '__builtins__': None,
            'abs': abs,
            'round': round,
            'pow': pow,
            'min': min,
            'max': max,
        }
        
        # Add math module functions
        math_attrs = [attr for attr in dir(math) if not attr.startswith('_')]
        for attr in math_attrs:
            safe_dict[attr] = getattr(math, attr)
        
        # Preprocess expression
        processed = preprocess_expression(expr)
        
        # Evaluate
        result = eval(processed, safe_dict, {})
        
        # Format result
        if isinstance(result, (int, float)):
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return result, None
        else:
            return None, "Result is not a number"
            
    except ZeroDivisionError:
        return None, "Division by zero"
    except SyntaxError:
        return None, "Invalid syntax"
    except NameError as e:
        return None, f"Unknown function or variable: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

# ==================== SESSION STATE INITIALIZATION ====================
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'user': None,
        'expr': '',
        'last_result': None,
        'history': [],
        'memory': 0,
        'show_advanced': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ==================== CALLBACK FUNCTIONS ====================
def append_to_expr(value: str):
    """Append value to expression"""
    st.session_state.expr += value

def clear_expr():
    """Clear expression"""
    st.session_state.expr = ""
    st.session_state.last_result = None

def backspace():
    """Remove last character"""
    st.session_state.expr = st.session_state.expr[:-1]

def clear_memory():
    """Clear memory"""
    st.session_state.memory = 0

def add_memory():
    """Recall memory value"""
    if st.session_state.memory != 0:
        st.session_state.expr += str(st.session_state.memory)

def memory_add():
    """Add result to memory"""
    if st.session_state.last_result is not None:
        st.session_state.memory += st.session_state.last_result

def memory_subtract():
    """Subtract result from memory"""
    if st.session_state.last_result is not None:
        st.session_state.memory -= st.session_state.last_result

# ==================== SIDEBAR: AUTHENTICATION ====================
st.sidebar.title("👤 Account")

if not st.session_state.user:
    auth_mode = st.sidebar.radio("", ["Login", "Sign Up", "Guest Mode"], label_visibility="collapsed")
    
    if auth_mode in ["Login", "Sign Up"]:
        with st.sidebar.form(key='auth_form'):
            username = st.text_input("Username", max_chars=20)
            password = st.text_input("Password", type="password", max_chars=50)
            submit = st.form_submit_button("Submit")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                elif auth_mode == "Sign Up":
                    success, message = create_user(username, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:  # Login
                    if authenticate_user(username, password):
                        st.session_state.user = username.strip()
                        st.session_state.history = load_history(st.session_state.user)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
    
    else:  # Guest Mode
        if st.sidebar.button("Continue as Guest", use_container_width=True):
            guest_id = datetime.utcnow().strftime("guest_%Y%m%d_%H%M%S")
            st.session_state.user = guest_id
            st.session_state.history = []
            st.rerun()

else:
    st.sidebar.success(f"Logged in as: **{st.session_state.user}**")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        for key in ['user', 'expr', 'last_result', 'history', 'memory']:
            st.session_state[key] = None if key == 'user' else ([] if key == 'history' else (0 if key == 'memory' else ''))
        st.rerun()
    
    st.sidebar.divider()
    
    # Memory display
    st.sidebar.subheader("💾 Memory")
    st.sidebar.info(f"Stored: {st.session_state.memory}")
    
    mem_cols = st.sidebar.columns(3)
    mem_cols[0].button("M+", on_click=memory_add, use_container_width=True, key="sidebar_m_plus")
    mem_cols[1].button("M-", on_click=memory_subtract, use_container_width=True, key="sidebar_m_minus")
    mem_cols[2].button("MC", on_click=clear_memory, use_container_width=True, key="sidebar_mc")

# ==================== MAIN UI ====================
st.title("🧮 Advanced Calculator")
st.markdown("A feature-rich calculator with user accounts and calculation history")

if not st.session_state.user:
    st.info("👈 Please log in, sign up, or continue as guest from the sidebar to use the calculator.")
    
    # Feature showcase
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### ✨ Features")
        st.markdown("- Scientific functions\n- Calculation history\n- Memory storage\n- User accounts")
    with col2:
        st.markdown("### 🔢 Functions")
        st.markdown("- Basic: +, -, ×, ÷\n- Advanced: sin, cos, tan\n- Power: ^, sqrt\n- Constants: π, e")
    with col3:
        st.markdown("### 📝 Examples")
        st.markdown("- `sqrt(144)`\n- `sin(pi/2)`\n- `2^8`\n- `50% * 200`")
    
    st.stop()

# ==================== CALCULATOR INTERFACE ====================
calc_col, hist_col = st.columns([2, 1])

with calc_col:
    st.subheader("Calculator")
    
    # Display
    display_text = st.session_state.expr if st.session_state.expr else "0"
    st.markdown(f'<div class="calculator-display">{display_text}</div>', unsafe_allow_html=True)
    
    # Button grid - FIXED with unique keys and proper symbols
    button_layout = [
        ["MC", "MR", "C", "⌫"],
        ["7", "8", "9", "/", "sqrt"],
        ["4", "5", "6", "*", "^"],
        ["1", "2", "3", "-", "("],
        ["0", ".", "%", "+", ")"],
    ]
    
    for row_idx, row in enumerate(button_layout):
        cols = st.columns(len(row))
        for col_idx, (col, btn) in enumerate(zip(cols, row)):
            btn_key = f"btn_{row_idx}_{col_idx}_{btn}"
            
            if btn == "C":
                col.button(btn, on_click=clear_expr, use_container_width=True, key=btn_key)
            elif btn == "⌫":
                col.button(btn, on_click=backspace, use_container_width=True, key=btn_key)
            elif btn == "MC":
                col.button(btn, on_click=clear_memory, use_container_width=True, key=btn_key)
            elif btn == "MR":
                col.button(btn, on_click=add_memory, use_container_width=True, key=btn_key)
            elif btn == "÷":
                col.button(btn, on_click=append_to_expr, args=("/",), use_container_width=True, key=btn_key)
            elif btn == "×":
                col.button(btn, on_click=append_to_expr, args=("*",), use_container_width=True, key=btn_key)
            elif btn == "^":
                col.button(btn, on_click=append_to_expr, args=("**",), use_container_width=True, key=btn_key)
            else:
                col.button(btn, on_click=append_to_expr, args=(btn,), use_container_width=True, key=btn_key)
    
    # Advanced functions toggle
    if st.checkbox("Show Advanced Functions", value=st.session_state.show_advanced, key="adv_checkbox"):
        st.session_state.show_advanced = True
        adv_functions = [
            ["sin", "cos", "tan", "pi", "e"],
            ["asin", "acos", "atan", "log", "ln"],
            ["floor", "ceil", "abs", "factorial", "degrees"]
        ]
        
        for row_idx, row in enumerate(adv_functions):
            cols = st.columns(len(row))
            for col_idx, (col, func) in enumerate(zip(cols, row)):
                func_key = f"adv_btn_{row_idx}_{col_idx}_{func}"
                
                if func == "ln":
                    col.button(func, on_click=append_to_expr, args=("log(",), use_container_width=True, key=func_key)
                elif func == "factorial":
                    col.button(func, on_click=append_to_expr, args=("factorial(",), use_container_width=True, key=func_key)
                elif func in ["sin", "cos", "tan", "asin", "acos", "atan", "log", "sqrt", "floor", "ceil", "abs", "degrees"]:
                    col.button(func, on_click=append_to_expr, args=(f"{func}(",), use_container_width=True, key=func_key)
                else:
                    col.button(func, on_click=append_to_expr, args=(func,), use_container_width=True, key=func_key)
    else:
        st.session_state.show_advanced = False
    
    # Calculate button
    if st.button("🟰 Calculate", type="primary", use_container_width=True, key="calc_button"):
        if not st.session_state.expr.strip():
            st.warning("⚠️ Please enter an expression")
        else:
            result, error = safe_eval(st.session_state.expr)
            
            if error:
                st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
            else:
                st.session_state.last_result = result
                st.markdown(f'<div class="success-box">✅ Result: <strong>{result}</strong></div>', unsafe_allow_html=True)
                
                # Save to history
                entry = CalculationEntry(
                    st.session_state.expr,
                    str(result),
                    datetime.utcnow().isoformat()
                )
                append_history(st.session_state.user, entry)
                st.session_state.history = load_history(st.session_state.user)
                
                # Update expression with result
                st.session_state.expr = str(result)

# ==================== HISTORY PANEL ====================
with hist_col:
    st.subheader("📜 History")
    
    history = load_history(st.session_state.user)
    
    if history:
        st.caption(f"Showing {min(HISTORY_DISPLAY, len(history))} of {len(history)} calculations")
        
        for idx, item in enumerate(history[:HISTORY_DISPLAY]):
            timestamp = item.get("timestamp", "")[:19].replace("T", " ")
            with st.container():
                st.markdown(f"**{item['expr']}**")
                st.markdown(f"= `{item['result']}`")
                st.caption(f"🕒 {timestamp}")
                
                # Reuse button
                if st.button(f"↻ Reuse", key=f"reuse_{idx}"):
                    st.session_state.expr = item['expr']
                    st.rerun()
                
                st.divider()
        
        if st.button("🗑️ Clear History", use_container_width=True, key="clear_history_btn"):
            if clear_history(st.session_state.user):
                st.session_state.history = []
                st.rerun()
    else:
        st.info("No calculations yet. Start calculating to build your history!")

# ==================== FOOTER ====================
st.divider()
with st.expander("ℹ️ Help & Tips"):
    st.markdown("""
    ### Supported Operations
    - **Basic**: `+`, `-`, `*`, `/`
    - **Power**: `**` or `^` (e.g., `2**3` or `2^3`)
    - **Percentage**: `%` (e.g., `50% * 200`)
    - **Functions**: `sqrt`, `sin`, `cos`, `tan`, `log`, `ln`, `abs`, `floor`, `ceil`, etc.
    - **Constants**: `pi` (π), `e` (Euler's number)
    
    ### Examples
    - `5+3` → 8
    - `10-4` → 6
    - `sqrt(144)` → 12
    - `sin(pi/2)` → 1
    - `2^8` → 256
    - `50% * 200` → 100
    - `log(100)` → 2
    - `2pi` → 6.28... (implicit multiplication)
    
    ### Memory Functions
    - **M+**: Add current result to memory
    - **M-**: Subtract current result from memory
    - **MC**: Clear memory
    - **MR**: Recall memory value
    """)

st.caption("💡 Tip: Use parentheses for complex expressions like `(2+3)*(4+5)`")
st.caption("🚀 Run with: `streamlit run calculator.py`")