import streamlit as st
from datetime import datetime
import json

# Page configuration
st.set_page_config(page_title="To-Do List", page_icon="✅", layout="centered")

# Initialize session state for tasks
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# Load tasks from file (persistence)
def load_tasks():
    try:
        with open('tasks.json', 'r') as f:
            st.session_state.tasks = json.load(f)
    except FileNotFoundError:
        st.session_state.tasks = []

# Save tasks to file
def save_tasks():
    with open('tasks.json', 'w') as f:
        json.dump(st.session_state.tasks, f)

# Load tasks on startup
if len(st.session_state.tasks) == 0:
    load_tasks()

# App title with custom styling
st.markdown("""
    <style>
    .big-font {
        font-size:40px !important;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("✅ My To-Do List")
st.markdown("*Stay organized and productive!*")
st.markdown("---")

# Sidebar for additional features
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Priority levels
    show_priority = st.checkbox("Enable Priority Levels", value=False)
    
    # Due dates
    show_due_date = st.checkbox("Enable Due Dates", value=False)
    
    # Categories
    show_categories = st.checkbox("Enable Categories", value=False)
    
    st.markdown("---")
    st.header("📥 Import/Export")
    
    # Export tasks
    if st.button("Export Tasks", use_container_width=True):
        if st.session_state.tasks:
            json_str = json.dumps(st.session_state.tasks, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("No tasks to export!")
    
    # Clear all tasks
    st.markdown("---")
    if st.button("🗑️ Clear All Tasks", type="secondary", use_container_width=True):
        if st.session_state.tasks:
            st.session_state.tasks = []
            save_tasks()
            st.rerun()

# Input section with enhanced features
col1, col2 = st.columns([3, 1])

with col1:
    new_task = st.text_input("Add a new task", placeholder="Enter your task here...", label_visibility="collapsed")

# Optional fields based on settings
priority_level = None
due_date = None
category = None

if show_priority or show_due_date or show_categories:
    cols = st.columns(3)
    
    if show_priority:
        with cols[0]:
            priority_level = st.selectbox("Priority", ["Low", "Medium", "High"], key="priority_select")
    
    if show_due_date:
        with cols[1]:
            due_date = st.date_input("Due Date", key="due_date_select")
    
    if show_categories:
        with cols[2]:
            category = st.selectbox("Category", ["Personal", "Work", "Shopping", "Health", "Other"], key="category_select")

with col2:
    if st.button("Add Task", type="primary", use_container_width=True):
        if new_task.strip():
            task_item = {
                'task': new_task,
                'completed': False,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'priority': priority_level if show_priority else None,
                'due_date': due_date.strftime("%Y-%m-%d") if show_due_date and due_date else None,
                'category': category if show_categories else None
            }
            st.session_state.tasks.append(task_item)
            save_tasks()
            st.rerun()

st.markdown("---")

# Search functionality
search_query = st.text_input("🔍 Search tasks", placeholder="Search by task name...")

# Display tasks
if st.session_state.tasks:
    # Filter options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_option = st.radio(
            "Filter tasks:",
            ["All", "Active", "Completed"],
            horizontal=True
        )
    
    with col2:
        if show_priority:
            priority_filter = st.selectbox("Priority Filter", ["All", "Low", "Medium", "High"])
        else:
            priority_filter = "All"
    
    # Sort options
    sort_option = st.selectbox("Sort by:", ["Created Date", "Priority (High to Low)", "Due Date", "Alphabetical"])
    
    # Filter tasks based on selection
    filtered_tasks = st.session_state.tasks.copy()
    
    # Apply completion filter
    if filter_option == "Active":
        filtered_tasks = [t for t in filtered_tasks if not t['completed']]
    elif filter_option == "Completed":
        filtered_tasks = [t for t in filtered_tasks if t['completed']]
    
    # Apply priority filter
    if show_priority and priority_filter != "All":
        filtered_tasks = [t for t in filtered_tasks if t.get('priority') == priority_filter]
    
    # Apply search filter
    if search_query:
        filtered_tasks = [t for t in filtered_tasks if search_query.lower() in t['task'].lower()]
    
    # Apply sorting
    if sort_option == "Priority (High to Low)":
        priority_order = {"High": 0, "Medium": 1, "Low": 2, None: 3}
        filtered_tasks.sort(key=lambda x: priority_order.get(x.get('priority'), 3))
    elif sort_option == "Due Date":
        filtered_tasks.sort(key=lambda x: x.get('due_date') or '9999-12-31')
    elif sort_option == "Alphabetical":
        filtered_tasks.sort(key=lambda x: x['task'].lower())
    
    if filtered_tasks:
        for idx, task in enumerate(st.session_state.tasks):
            if task not in filtered_tasks:
                continue
            
            col1, col2, col3 = st.columns([0.5, 3, 0.5])
            
            with col1:
                # Checkbox for completion
                checked = st.checkbox("", value=task['completed'], key=f"check_{idx}", label_visibility="collapsed")
                if checked != task['completed']:
                    st.session_state.tasks[idx]['completed'] = checked
                    save_tasks()
                    st.rerun()
            
            with col2:
                # Priority indicator
                priority_emoji = ""
                if task.get('priority') == "High":
                    priority_emoji = "🔴"
                elif task.get('priority') == "Medium":
                    priority_emoji = "🟡"
                elif task.get('priority') == "Low":
                    priority_emoji = "🟢"
                
                # Display task with strikethrough if completed
                if task['completed']:
                    st.markdown(f"~~{priority_emoji} {task['task']}~~ ✓")
                else:
                    st.markdown(f"**{priority_emoji} {task['task']}**")
                
                # Display metadata
                metadata = f"Created: {task['created_at']}"
                if task.get('due_date'):
                    due = datetime.strptime(task['due_date'], "%Y-%m-%d")
                    if due.date() < datetime.now().date() and not task['completed']:
                        metadata += f" | 🔴 Due: {task['due_date']} (Overdue!)"
                    else:
                        metadata += f" | 📅 Due: {task['due_date']}"
                if task.get('category'):
                    metadata += f" | 🏷️ {task['category']}"
                
                st.caption(metadata)
            
            with col3:
                # Delete button
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.tasks.pop(idx)
                    save_tasks()
                    st.rerun()
            
            st.markdown("---")
        
        # Task statistics
        total = len(st.session_state.tasks)
        completed = sum(1 for t in st.session_state.tasks if t['completed'])
        active = total - completed
        
        if show_due_date:
            overdue = sum(1 for t in st.session_state.tasks 
                         if t.get('due_date') and not t['completed'] 
                         and datetime.strptime(t['due_date'], "%Y-%m-%d").date() < datetime.now().date())
        
        st.markdown("### 📊 Statistics")
        
        if show_due_date:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Tasks", total)
            col2.metric("Active", active)
            col3.metric("Completed", completed)
            col4.metric("Overdue", overdue, delta_color="inverse")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tasks", total)
            col2.metric("Active", active)
            col3.metric("Completed", completed)
        
        # Progress bar
        if total > 0:
            progress = completed / total
            st.progress(progress)
            st.caption(f"Progress: {completed}/{total} tasks completed ({progress*100:.1f}%)")
        
        # Clear completed button
        if completed > 0:
            if st.button("Clear Completed Tasks", type="secondary"):
                st.session_state.tasks = [t for t in st.session_state.tasks if not t['completed']]
                save_tasks()
                st.rerun()
    else:
        st.info(f"No {filter_option.lower()} tasks matching your criteria.")
else:
    st.info("No tasks yet. Add your first task above! 🎯")

# Footer
st.markdown("---")
st.caption("Made with ❤️ using Streamlit | Your productivity companion")