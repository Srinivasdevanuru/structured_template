import streamlit as st
import streamlit_authenticator as stauth
import bcrypt
from typing import Dict, List, Optional
from database import get_db
from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="viewer")  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    session_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

# Database setup for auth
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_auth_tables():
    """Create authentication tables"""
    if DATABASE_URL:
        Base.metadata.create_all(bind=engine)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(username: str, email: str, full_name: str, password: str, role: str = "viewer") -> bool:
    """Create a new user"""
    if not DATABASE_URL:
        return False
        
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            return False
        
        # Create new user
        hashed_pw = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_pw,
            role=role
        )
        
        db.add(new_user)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def authenticate_user(username_or_email: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user info"""
    if not DATABASE_URL:
        return None
        
    db = SessionLocal()
    try:
        # Check if login is with username or email
        user = db.query(User).filter(
            ((User.username == username_or_email) | (User.email == username_or_email)),
            User.is_active == True
        ).first()
        
        if user and verify_password(password, user.hashed_password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            return {
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'last_login': user.last_login
            }
        return None
        
    except Exception as e:
        return None
    finally:
        db.close()

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user information by username"""
    if not DATABASE_URL:
        return None
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
        return None
    except Exception as e:
        return None
    finally:
        db.close()

def get_all_users() -> List[Dict]:
    """Get all users (admin only)"""
    if not DATABASE_URL:
        return []
        
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return [{
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at,
            'last_login': user.last_login
        } for user in users]
    except Exception as e:
        return []
    finally:
        db.close()

def update_user_role(username: str, new_role: str) -> bool:
    """Update user role (admin only)"""
    if not DATABASE_URL:
        return False
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.role = new_role
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def deactivate_user(username: str) -> bool:
    """Deactivate user (admin only)"""
    if not DATABASE_URL:
        return False
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            user.is_active = False
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def create_default_admin():
    """Create default admin user if none exists"""
    if not DATABASE_URL:
        return False
        
    db = SessionLocal()
    try:
        # Check if any admin exists
        admin_exists = db.query(User).filter(User.role == "admin").first()
        
        if not admin_exists:
            # Create default admin
            create_user(
                username="admin",
                email="admin@medibox.com",
                full_name="System Administrator",
                password="admin123",  # Should be changed on first login
                role="admin"
            )
            return True
        return False
    except Exception as e:
        return False
    finally:
        db.close()

def check_permission(required_role: str) -> bool:
    """Check if current user has required permission"""
    if 'user_info' not in st.session_state:
        return False
    
    user_role = st.session_state.user_info.get('role', 'viewer')
    
    # Role hierarchy: admin > analyst > viewer
    role_hierarchy = {'admin': 3, 'analyst': 2, 'viewer': 1}
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def login_form():
    """Display login form"""
    st.title("🔐 Medibox Detection System - Login")
    
    with st.form("login_form"):
        st.subheader("Sign In")
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
        with col2:
            register_button = st.form_submit_button("Register", use_container_width=True)
        
        if login_button:
            if username and password:
                user_info = authenticate_user(username, password)
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.success(f"Welcome back, {user_info['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")
        
        if register_button:
            st.session_state.show_register = True
            st.rerun()

def register_form():
    """Display registration form"""
    st.title("📝 User Registration")
    
    with st.form("register_form"):
        st.subheader("Create Account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        full_name = st.text_input("Full Name")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            register_button = st.form_submit_button("Register", type="primary", use_container_width=True)
        with col2:
            back_button = st.form_submit_button("Back to Login", use_container_width=True)
        
        if register_button:
            if not all([username, email, full_name, password, confirm_password]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                if create_user(username, email, full_name, password, "viewer"):
                    st.success("Account created successfully! Please login.")
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Username or email already exists")
        
        if back_button:
            st.session_state.show_register = False
            st.rerun()

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user_info = None
    if 'show_register' in st.session_state:
        del st.session_state.show_register
    st.rerun()

def user_management_tab():
    """User management interface (admin only)"""
    if not check_permission("admin"):
        st.error("Access denied. Admin privileges required.")
        return
    
    st.header("👥 User Management")
    
    # Get all users
    users = get_all_users()
    
    if users:
        st.subheader("All Users")
        
        for user in users:
            with st.expander(f"{user['full_name']} ({user['username']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Role:** {user['role']}")
                    st.write(f"**Status:** {'Active' if user['is_active'] else 'Inactive'}")
                
                with col2:
                    st.write(f"**Created:** {user['created_at'].strftime('%Y-%m-%d')}")
                    if user['last_login']:
                        st.write(f"**Last Login:** {user['last_login'].strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.write("**Last Login:** Never")
                
                with col3:
                    # Role update
                    new_role = st.selectbox(
                        "Change Role:",
                        ["viewer", "analyst", "admin"],
                        index=["viewer", "analyst", "admin"].index(user['role']),
                        key=f"role_{user['username']}"
                    )
                    
                    if st.button(f"Update Role", key=f"update_{user['username']}"):
                        if update_user_role(user['username'], new_role):
                            st.success("Role updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update role")
                    
                    if user['is_active'] and st.button(f"Deactivate", key=f"deactivate_{user['username']}"):
                        if deactivate_user(user['username']):
                            st.success("User deactivated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to deactivate user")
    else:
        st.info("No users found")

def auth_sidebar():
    """Authentication sidebar"""
    with st.sidebar:
        if st.session_state.get('authenticated', False):
            user_info = st.session_state.get('user_info', {})
            
            st.markdown("---")
            st.subheader("👤 User Info")
            st.write(f"**Name:** {user_info.get('full_name', 'Unknown')}")
            st.write(f"**Role:** {user_info.get('role', 'viewer').title()}")
            
            if st.button("🚪 Logout", use_container_width=True):
                logout()