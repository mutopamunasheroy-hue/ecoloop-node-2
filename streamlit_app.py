
import streamlit as st
import pandas as pd
import qrcode
import io
import uuid

from datetime import date, datetime
from supabase import create_client


# =====================================================
# ECOLOOP NODE — APP CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="EcoLoop Node",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# BRAND IDENTITY
# =====================================================

APP_NAME = "EcoLoop Node"

APP_TAGLINE = (
    "Turning everyday environmental action "
    "into measurable community impact."
)

NGIH_NAME = "Next Gen Impact Hub"

NGIH_MISSION = (
    "To create a generation of youth who lead and "
    "influence across governance, economy, environment, "
    "and technology."
)

APP_VERSION = "2.0"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_supabase_client():

    if "_supabase_client" not in st.session_state:

        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]

        st.session_state["_supabase_client"] = create_client(
            supabase_url,
            supabase_key
        )

    return st.session_state["_supabase_client"]


try:
    supabase = get_supabase_client()
    supabase_error = None

except Exception as error:
    supabase = None
    supabase_error = type(error).__name__


# =====================================================
# INITIAL SESSION STATE
# =====================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "user": None,
    "profile": None,
    "access_token": None,
    "refresh_token": None,
    "current_page": "Home",
}

for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:
        st.session_state[key] = value

# =====================================================
# AUTHENTICATION AND SESSION MANAGEMENT
# =====================================================

def load_user_profile():

    if not supabase:
        return None

    user_id = st.session_state.get("user_id")

    if not user_id:
        return None

    try:
        response = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )

        profile = response.data

        st.session_state["profile"] = profile

        return profile

    except Exception:
        return None


def set_user_session(auth_response):

    session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)

    if not user:
        return False

    if not session:
        st.session_state["user_id"] = str(user.id)
        st.session_state["user"] = user
        st.session_state["logged_in"] = True

        load_user_profile()
        return True

    st.session_state["user_id"] = str(user.id)
    st.session_state["user"] = user
    st.session_state["access_token"] = session.access_token
    st.session_state["refresh_token"] = session.refresh_token
    st.session_state["logged_in"] = True

    load_user_profile()

    return True


def restore_auth_session():

    if not supabase:
        return False

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token or not refresh_token:
        return False

    try:
        response = supabase.auth.set_session(
            access_token,
            refresh_token
        )

        user = getattr(response, "user", None)

        if not user:
            return False

        st.session_state["user"] = user
        st.session_state["user_id"] = str(user.id)
        st.session_state["logged_in"] = True

        load_user_profile()

        return True

    except Exception:
        clear_user_session()
        return False


def clear_user_session():

    if supabase:
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

    st.session_state["logged_in"] = False
    st.session_state["user"] = None
    st.session_state["profile"] = None
    st.session_state["user_id"] = None
    st.session_state["access_token"] = None
    st.session_state["refresh_token"] = None
    st.session_state["current_page"] = "Home"


def is_logged_in():

    return (
        st.session_state.get("logged_in", False)
        and st.session_state.get("user_id") is not None
    )


def is_admin():

    profile = st.session_state.get("profile")

    if not profile:
        return False

    return profile.get("role") == "admin"


def require_login():

    if not is_logged_in():
        st.warning("Please log in to access this page.")
        return False

    return True


# =====================================================
# RESTORE AN EXISTING LOGIN
# =====================================================

if (
    supabase
    and not st.session_state.get("logged_in", False)
    and st.session_state.get("access_token")
    and st.session_state.get("refresh_token")
):

    restore_auth_session()

   
# =====================================================
# ECOLOOP NODE — VISUAL DESIGN SYSTEM
# =====================================================

import os

# -----------------------------------------------------
# NGIH BRAND COLOURS
# -----------------------------------------------------

NGIH_FOREST = "#176B45"
NGIH_LIME = "#A8D94F"
NGIH_TEAL = "#168C83"
NGIH_AMBER = "#E9A23B"
NGIH_PURPLE = "#7654A6"

LOGO_FILE = "IMG-20261028-WA0000.jpg"

# -----------------------------------------------------
# GLOBAL VISUAL STYLING
# -----------------------------------------------------

st.markdown("""
<style>

@import url(
    'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap'
);

:root {
    --eco-green: #176B45;
    --eco-lime: #A8D94F;
    --eco-teal: #168C83;
    --eco-amber: #E9A23B;
    --eco-purple: #7654A6;
}

/* GLOBAL TYPOGRAPHY */

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* MAIN BACKGROUND */

.stApp {
    background-color: var(--background-color);
}

/* HEADINGS */

h1, h2, h3 {
    font-weight: 800 !important;
    letter-spacing: -0.5px;
}

h1 {
    color: var(--eco-green) !important;
}

h2, h3 {
    color: var(--text-color) !important;
}

/* BODY TEXT */

p, label, .stMarkdown, .stCaption {
    line-height: 1.6;
}

/* BUTTONS */

.stButton > button {
    border-radius: 12px;
    min-height: 46px;
    font-weight: 700;
    border: 1px solid var(--eco-green);
    transition: 0.2s ease;
}

.stButton > button[kind="primary"] {
    background-color: var(--eco-green);
    color: white;
    border: 1px solid var(--eco-green);
}

.stButton > button:hover {
    border-color: var(--eco-lime);
    color: var(--eco-green);
}

/* INPUT FIELDS */

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"],
.stTextArea textarea {
    border-radius: 10px;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    min-width: 260px;
}

section[data-testid="stSidebar"] button {
    width: 100%;
    min-height: 44px;
    border-radius: 10px;
    font-weight: 600;
    text-align: left;
}

/* SIDEBAR MENU CONTROL */

button[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"] {
    min-width: 48px !important;
    min-height: 48px !important;
    width: 48px !important;
    height: 48px !important;
    border-radius: 10px !important;
    border: 2px solid #A8D94F !important;
    background-color: #176B45 !important;
    color: white !important;
    opacity: 1 !important;
    visibility: visible !important;
}

button[data-testid="stSidebarCollapsedControl"] svg,
button[data-testid="stSidebarCollapseButton"] svg {
    width: 25px !important;
    height: 25px !important;
    color: white !important;
    stroke: white !important;
}

/* ECOLOOP CARDS */

.eco-card {
    padding: 20px;
    border-radius: 16px;
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-left: 5px solid var(--eco-lime);
    background: var(--secondary-background-color);
    margin-bottom: 16px;
}

.eco-card-title {
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 8px;
}

.eco-card-description {
    font-size: 14px;
    line-height: 1.7;
}

/* METRIC CARDS */

[data-testid="stMetric"] {
    background: var(--secondary-background-color);
    padding: 16px;
    border-radius: 14px;
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-top: 3px solid var(--eco-green);
}

/* ALERTS */

div[data-testid="stAlert"] {
    border-radius: 12px;
}

/* TABLES */

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* LINKS */

a {
    color: var(--eco-teal);
}

/* MOBILE LAYOUT */

@media (max-width: 768px) {

    section[data-testid="stSidebar"] {
        min-width: 0;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    h1 {
        font-size: 1.8rem !important;
    }

    h2 {
        font-size: 1.4rem !important;
    }

    .eco-card {
        padding: 15px;
    }

    .stButton > button {
        min-height: 48px;
    }
}

</style>
""", unsafe_allow_html=True)



# =====================================================
# REUSABLE PAGE DESIGN COMPONENTS
# =====================================================

def section_heading(title, subtitle=None):

    st.markdown(f"## {title}")

    if subtitle:
        st.caption(subtitle)


def eco_card(title, description, icon="♻️"):

    st.markdown(
        f"""
        <div class="eco-card">
            <div class="eco-card-title">
                {icon} {title}
            </div>
            <div class="eco-card-description">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_empty_state(message):

    st.info(message)


def get_table_count(table_name):

    if not supabase:
        return 0

    try:
        response = (
            supabase
            .table(table_name)
            .select("id", count="exact")
            .limit(0)
            .execute()
        )

        return response.count or 0

    except Exception:
        return 0


# =====================================================
# ECOLOOP NODE — MOBILE BRAND HEADER
# =====================================================

import os
import base64

LOGO_FILE = "IMG-20261028-WA0000.jpg"


def show_app_header():

    if os.path.exists(LOGO_FILE):

        with open(LOGO_FILE, "rb") as logo_file:
            logo_data = base64.b64encode(
                logo_file.read()
            ).decode("utf-8")

        logo_html = (
            f'<img src="data:image/jpeg;base64,{logo_data}" '
            'width="125" '
            'style="height:auto; max-height:none; '
            'object-fit:contain; display:block;">'
        )

    else:
        logo_html = "NGIH"

    header_html = f"""
    <table width="100%" cellpadding="8" cellspacing="0"
           style="border-collapse:collapse;">
        <tr>
            <td width="35%" valign="middle">
                {logo_html}
            </td>
            <td width="65%" valign="middle">
                <h2 style="margin:0; font-size:25px;">
                    {APP_NAME}
                </h2>
                <p style="margin:6px 0;">
                    <strong>Powered by {NGIH_NAME} (NGIH)</strong>
                </p>
                <p style="margin:4px 0; font-size:12px;">
                    {APP_TAGLINE}
                </p>
            </td>
        </tr>
    </table>
    """

    st.markdown(
        header_html,
        unsafe_allow_html=True
    )

    st.divider()

# =====================================================
# ECOLOOP NODE — NAVIGATION STRUCTURE
# =====================================================

NAVIGATION = {
    "Home": [
        "Home"
    ],

    "EcoLoop": [
        "EcoLoop Nodes",
        "Record Waste",
        "Collection Management",
        "Environmental Impact"
    ],

    "Community": [
        "Community Groups",
        "Challenges",
        "Action Gallery",
        "Leaderboard",
        "Notifications Centre"
    ],

    "Learn & Grow": [
        "Explore & Learn",
        "Eco Quiz"
    ],

    "Account": [
        "My Profile",
        "About NGIH"
    ]
}


ADMIN_PAGES = [
    "Verify Contributions",
    "Admin Studio",
    "System Diagnostics"
]


# =====================================================
# PAGE SELECTION
# =====================================================

def navigate_to(page):

    st.session_state["current_page"] = page

    for category, pages in NAVIGATION.items():

        if page in pages:
            st.session_state["main_category"] = category
            break


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

def render_navigation():

    with st.sidebar:

        st.markdown(
            f"""
            <div style="padding: 10px 4px 18px 4px;">
                <h2 style="margin-bottom:0;">
                    ♻️ EcoLoop Node
                </h2>
                <p style="font-size:12px; opacity:0.75;">
                    Powered by NGIH
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        selected_category = st.session_state.get(
            "main_category",
            "Home"
        )

        if selected_category not in NAVIGATION:
            selected_category = "Home"

        for category, pages in NAVIGATION.items():

            with st.expander(
                category,
                expanded=(selected_category == category)
            ):

                for page in pages:

                    is_current = (
                        st.session_state.get("current_page")
                        == page
                    )

                    if st.button(
                        f"{'● ' if is_current else ''}{page}",
                        key=f"nav_{page}",
                        use_container_width=True
                    ):
                        navigate_to(page)
                        st.rerun()

        # Administrator navigation

        if is_admin():

            with st.expander(
                "Administration",
                expanded=(
                    st.session_state.get("current_page")
                    in ADMIN_PAGES
                )
            ):

                for page in ADMIN_PAGES:

                    is_current = (
                        st.session_state.get("current_page")
                        == page
                    )

                    if st.button(
                        f"{'● ' if is_current else ''}{page}",
                        key=f"admin_nav_{page}",
                        use_container_width=True
                    ):
                        navigate_to(page)
                        st.rerun()

        st.divider()

        # Account status

        if is_logged_in():

            profile = st.session_state.get("profile") or {}

            display_name = profile.get(
                "full_name",
                "EcoLoop Member"
            )

            st.caption(f"Signed in as {display_name}")

            if st.button(
                "Log Out",
                key="sidebar_logout",
                use_container_width=True
            ):
                clear_user_session()
                st.rerun()

        else:

            st.caption("You are browsing as a guest.")

            if st.button(
                "Log In",
                key="sidebar_login",
                use_container_width=True
            ):
                navigate_to("Login")
                st.rerun()

# =====================================================
# PAGE 1 — HOME DASHBOARD
# =====================================================

def home_page():

    # -----------------------------------------------
    # WELCOME HEADER
    # -----------------------------------------------

    st.title("♻️ Welcome to EcoLoop Node")

    st.write(APP_TAGLINE)

    st.divider()

    # -----------------------------------------------
    # DATABASE STATUS
    # -----------------------------------------------

    if not supabase:

        st.warning(
            "The database connection is currently unavailable. "
            "Some dashboard information may not load."
        )

    # -----------------------------------------------
    # GUEST DASHBOARD
    # -----------------------------------------------

    if not is_logged_in():

        st.subheader("Small actions. Measurable impact.")

        eco_card(
            "Record your environmental action",
            "Contribute recyclable waste and help build "
            "a cleaner, more sustainable community.",
            "♻️"
        )

        eco_card(
            "Connect with your community",
            "Join environmental groups, take part in "
            "challenges and learn from other members.",
            "🌍"
        )

        eco_card(
            "Track environmental progress",
            "Follow verified contributions and discover "
            "how community action creates measurable impact.",
            "📊"
        )

        st.subheader("Get started")

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Create an Account",
                use_container_width=True
            ):
                navigate_to("Register")
                st.rerun()

        with col2:

            if st.button(
                "Log In",
                use_container_width=True
            ):
                navigate_to("Login")
                st.rerun()

        st.divider()

        st.subheader("About EcoLoop Node")

        st.write(
            "EcoLoop Node is a community-focused environmental "
            "technology platform developed under Next Gen "
            "Impact Hub (NGIH). It encourages responsible waste "
            "management, environmental learning and community "
            "participation."
        )

        return

    # -----------------------------------------------
    # MEMBER DASHBOARD
    # -----------------------------------------------

    profile = st.session_state.get("profile") or {}

    display_name = profile.get(
        "full_name",
        "EcoLoop Member"
    )

    st.subheader(f"Welcome back, {display_name}!")

    st.caption(
        "Here is an overview of your EcoLoop activity."
    )

    user_id = st.session_state.get("user_id")

    contributions = []
    verified_weight = 0.0
    total_points = 0

    # -----------------------------------------------
    # LOAD MEMBER CONTRIBUTIONS
    # -----------------------------------------------

    if supabase and user_id:

        try:

            response = (
                supabase
                .table("waste_contributions")
                .select(
                    "id, material_type, weight, "
                    "verification_status, submitted_at, points"
                )
                .eq("user_id", user_id)
                .order("submitted_at", desc=True)
                .execute()
            )

            contributions = response.data or []

            verified = [
                item for item in contributions
                if item.get("verification_status") == "verified"
            ]

            verified_weight = sum(
                float(item.get("weight") or 0)
                for item in verified
            )

            total_points = sum(
                int(item.get("points") or 0)
                for item in verified
            )

        except Exception:

            st.warning(
                "Your contribution summary could not be loaded."
            )

    # -----------------------------------------------
    # DASHBOARD METRICS
    # -----------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Submissions",
            len(contributions)
        )

    with col2:
        st.metric(
            "Verified Waste",
            f"{verified_weight:.2f} kg"
        )

    with col3:
        st.metric(
            "Points Earned",
            total_points
        )

    with col4:

        pending_count = sum(
            1 for item in contributions
            if item.get("verification_status") == "pending"
        )

        st.metric(
            "Pending Verification",
            pending_count
        )

    st.divider()

    # -----------------------------------------------
    # RECENT CONTRIBUTIONS
    # -----------------------------------------------

    st.subheader("Your Recent Contributions")

    if contributions:

        recent_rows = []

        for item in contributions[:5]:

            recent_rows.append({
                "Material": item.get("material_type", "Unknown"),
                "Weight (kg)": item.get("weight", 0),
                "Status": item.get(
                    "verification_status",
                    "Unknown"
                ).capitalize(),
                "Date": item.get("submitted_at", "")
            })

        st.dataframe(
            pd.DataFrame(recent_rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        show_empty_state(
            "You have not recorded any waste contributions yet. "
            "Your first contribution can start your EcoLoop journey."
        )

    # -----------------------------------------------
    # QUICK ACTIONS
    # -----------------------------------------------

    st.divider()

    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button(
            "♻️ Record Waste",
            use_container_width=True
        ):
            navigate_to("Record Waste")
            st.rerun()

    with col2:

        if st.button(
            "📊 View Impact",
            use_container_width=True
        ):
            navigate_to("Environmental Impact")
            st.rerun()

    with col3:

        if st.button(
            "🏆 Leaderboard",
            use_container_width=True
        ):
            navigate_to("Leaderboard")
            st.rerun()

    # -----------------------------------------------
    # COMMUNITY MESSAGE
    # -----------------------------------------------

    st.divider()

    eco_card(
        "Every contribution counts",
        "Your verified environmental actions contribute "
        "to a wider community effort towards responsible "
        "waste management and environmental protection.",
        "🌱"
    )


# =====================================================
# PAGE 2 — LOGIN
# =====================================================

def login_form():

    st.title("Welcome Back")
    st.write("Log in to continue your EcoLoop journey.")

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    st.divider()

    st.subheader("Member Login")

    with st.form("ecoloop_login_form"):

        email = st.text_input(
            "Email Address",
            placeholder="Enter your registered email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        submitted = st.form_submit_button(
            "Log In",
            use_container_width=True
        )

        if submitted:

            if not email.strip() or not password:
                st.warning("Please enter your email and password.")

            else:
                try:

                    response = supabase.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                    })

                    if set_user_session(response):

                        st.success("Welcome back to EcoLoop Node!")

                        st.session_state["current_page"] = "Home"
                        st.session_state["main_category"] = "Home"

                        st.rerun()

                    else:
                        st.error(
                            "Your login was not completed. "
                            "Please try again."
                        )

                except Exception as error:
                    st.error("We could not complete your login.")
                    st.caption(f"Authentication details: {str(error)}")

    st.divider()

    # FORGOT PASSWORD

    with st.expander("Forgot your password?"):

        st.write(
            "Enter your registered email address. "
            "We'll request a password-reset email."
        )

        reset_email = st.text_input(
            "Registered Email",
            key="password_reset_email",
            placeholder="Enter your email address"
        )

        if st.button(
            "Send Password Reset Link",
            use_container_width=True
        ):

            if not reset_email.strip():
                st.warning("Please enter your registered email.")

            else:
                try:

                    supabase.auth.reset_password_for_email(
                        reset_email.strip()
                    )

                    st.success(
                        "If the account exists, a password-reset "
                        "email will be sent. Check your inbox."
                    )

                except Exception as error:
                    st.error("We could not request the password reset.")
                    st.caption(f"Details: {str(error)}")

    st.divider()

    st.write("New to EcoLoop Node?")

    if st.button(
        "Create an Account",
        use_container_width=True
    ):
        navigate_to("Register")
        st.rerun()



# =====================================================
# PAGE 3 — REGISTRATION
# =====================================================

def registration_form():

    st.title("Join EcoLoop Node")

    st.write(
        "Create an account and become part of a community "
        "working towards a cleaner environment."
    )

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    with st.form("ecoloop_registration_form"):

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Enter your password again"
        )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

        if submitted:

            if not full_name.strip() or not email.strip():
                st.warning("Please complete your name and email.")

            elif len(password) < 8:
                st.warning(
                    "Your password must contain at least 8 characters."
                )

            elif password != confirm_password:
                st.warning("Your passwords do not match.")

            else:

                try:

                    response = supabase.auth.sign_up({
                        "email": email.strip(),
                        "password": password,
                        "options": {
                            "data": {
                                "full_name": full_name.strip()
                            }
                        }
                    })

                    user = getattr(response, "user", None)
                    session = getattr(response, "session", None)

                    if user and session:

                        set_user_session(response)

                        st.success(
                            "Your account has been created successfully!"
                        )

                        st.session_state["current_page"] = "Home"
                        st.session_state["main_category"] = "Home"
                        st.rerun()

                    elif user:

                        st.success(
                            "Registration received. Please check your "
                            "email to confirm your account before logging in."
                        )

                    else:

                        st.error(
                            "Registration could not be completed. "
                            "Please try again."
                        )

                except Exception:
                    st.error(
                        "Registration failed. The email may already "
                        "be registered, or the details may be invalid."
                    )

    st.divider()

    st.write("Already have an account?")

    if st.button("Go to Login", use_container_width=True):
        navigate_to("Login")
        st.rerun()


# =====================================================
# PAGE 4 — MY PROFILE
# =====================================================

def account_page():

    st.title("My Profile")

    if not require_login():
        return

    profile = st.session_state.get("profile") or {}

    user = st.session_state.get("user")

    email = getattr(user, "email", "Not available")

    st.subheader(
        profile.get("full_name", "EcoLoop Member")
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Account Role",
            profile.get("role", "user").capitalize()
        )

    with col2:
        st.metric(
            "Account Status",
            "Active"
        )

    st.divider()

    st.subheader("Account Information")

    st.write("**Full Name:**", profile.get("full_name", "Not available"))
    st.write("**Email:**", email)
    st.write("**User ID:**", st.session_state.get("user_id", "Not available"))

    created_at = profile.get("created_at")

    if created_at:
        st.write("**Member Since:**", str(created_at)[:10])

    st.divider()

    st.caption(
        "Your account information is managed through "
        "EcoLoop Node and its secure authentication system."
    )

    if st.button(
        "Log Out",
        use_container_width=True
    ):
        clear_user_session()
        st.rerun()

# =====================================================
# PAGE 5 — ECOLOOP NODES AND QR STATIONS
# =====================================================

# Your currently deployed EcoLoop Node application
APP_URL = (
    "https://ecoloop-node-2-g2jtmgyszhvgynvmnzuo7d.streamlit.app"
)


def generate_station_qr(station_code):

    station_url = (
        f"{APP_URL}/?station={station_code}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(station_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="#176B45",
        back_color="white"
    )

    image_buffer = io.BytesIO()
    qr_image.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    return image_buffer


def load_collection_stations():

    if not supabase:
        return []

    try:

        response = (
            supabase
            .table("collection_stations")
            .select("*")
            .order("station_code")
            .execute()
        )

        return response.data or []

    except Exception:

        st.error("Could not load collection stations.")
        return []


def ecoloop_nodes_page():

    st.title("♻️ EcoLoop Nodes")

    st.write(
        "Explore registered EcoLoop collection stations "
        "and use their QR codes to identify where you "
        "are recording a contribution."
    )

    if not supabase:
        st.warning("The database connection is unavailable.")
        return

    # -----------------------------------------------
    # READ STATION CODE FROM QR LINK
    # -----------------------------------------------

    try:

        station_from_url = st.query_params.get("station")

        if isinstance(station_from_url, str):

            st.session_state["selected_station"] = (
                station_from_url.strip()
            )

    except Exception:
        pass

    # -----------------------------------------------
    # LOAD REGISTERED STATIONS
    # -----------------------------------------------

    stations = load_collection_stations()

    if not stations:

        show_empty_state(
            "No collection stations are currently available."
        )
        return

    st.metric(
        "Registered Collection Stations",
        len(stations)
    )

    st.divider()

    # -----------------------------------------------
    # SELECT A STATION
    # -----------------------------------------------

    station_options = {
        (
            f"{station.get('station_code', 'Unknown')} — "
            f"{station.get('station_name', 'Unnamed Station')}"
        ): station.get("station_code")
        for station in stations
    }

    available_codes = list(station_options.values())

    selected_code = st.session_state.get("selected_station")

    if selected_code not in available_codes:
        selected_code = available_codes[0]

    selected_label = next(
        (
            label
            for label, code in station_options.items()
            if code == selected_code
        ),
        list(station_options.keys())[0]
    )

    selected_label = st.selectbox(
        "Choose a collection station",
        options=list(station_options.keys()),
        index=list(station_options.keys()).index(selected_label)
    )

    selected_code = station_options[selected_label]

    st.session_state["selected_station"] = selected_code

    # -----------------------------------------------
    # DISPLAY SELECTED STATION
    # -----------------------------------------------

    selected_station = next(
        (
            station for station in stations
            if station.get("station_code") == selected_code
        ),
        None
    )

    if selected_station:

        st.subheader(
            selected_station.get(
                "station_name",
                "Collection Station"
            )
        )

        st.write(
            f"**Station Code:** {selected_code}"
        )

        st.caption(
            "Use this station's QR code when recording "
            "a waste contribution."
        )

        # -------------------------------------------
        # GENERATE QR CODE
        # -------------------------------------------

        qr_buffer = generate_station_qr(selected_code)

        col1, col2 = st.columns([1, 2])

        with col1:

            st.image(
                qr_buffer,
                caption=f"QR Code — {selected_code}",
                use_container_width=True
            )

            qr_buffer.seek(0)

            st.download_button(
                label="Download Station QR",
                data=qr_buffer,
                file_name=f"{selected_code}_QR.png",
                mime="image/png",
                use_container_width=True
            )

        with col2:

            eco_card(
                "Station identification",
                "This QR code opens EcoLoop Node with the "
                "station code included. Members can then "
                "select that station when submitting a "
                "contribution.",
                "📍"
            )

            eco_card(
                "Contribution verification",
                "Scanning a QR code identifies a station. "
                "It does not independently prove that waste "
                "was physically deposited. Contributions "
                "remain subject to the verification process.",
                "🔐"
            )

    st.divider()

    # -----------------------------------------------
    # ALL REGISTERED STATIONS
    # -----------------------------------------------

    st.subheader("All Registered Stations")

    station_rows = []

    for station in stations:

        station_rows.append({
            "Station Code": station.get("station_code"),
            "Station Name": station.get("station_name")
        })

    st.dataframe(
        pd.DataFrame(station_rows),
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# PAGE 6 — RECORD WASTE CONTRIBUTIONS
# =====================================================

def record_waste_page():

    st.title("♻️ Record Waste")

    st.write(
        "Record your recyclable waste contribution "
        "and help us measure environmental impact."
    )

    # -----------------------------------------------
    # LOGIN REQUIREMENT
    # -----------------------------------------------

    if not require_login():
        return

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    # -----------------------------------------------
    # LOAD COLLECTION STATIONS
    # -----------------------------------------------

    stations = load_collection_stations()

    if not stations:

        st.warning(
            "There are currently no registered collection stations."
        )
        return

    station_options = {
        (
            f"{station.get('station_code')} — "
            f"{station.get('station_name')}"
        ): station.get("station_code")
        for station in stations
    }

    station_labels = list(station_options.keys())

    # -----------------------------------------------
    # MATERIAL CATEGORIES
    # -----------------------------------------------

    MATERIAL_TYPES = [
        "Plastic",
        "Paper",
        "Metal",
        "Glass",
        "Organic",
        "Electronic"
    ]

    st.subheader("Contribution Details")

    st.caption(
        "Please provide accurate information about "
        "the waste you are contributing."
    )

    # -----------------------------------------------
    # CONTRIBUTION FORM
    # -----------------------------------------------

    with st.form("record_waste_form"):

        default_station = st.session_state.get(
            "selected_station"
        )

        default_index = 0

        if default_station in station_options.values():

            default_index = list(
                station_options.values()
            ).index(default_station)

        selected_station_label = st.selectbox(
            "Collection Station",
            options=station_labels,
            index=default_index
        )

        material_type = st.selectbox(
            "Material Type",
            options=MATERIAL_TYPES
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=0.01,
            max_value=10000.0,
            value=1.0,
            step=0.1,
            format="%.2f"
        )

        submitted = st.form_submit_button(
            "Submit Contribution",
            use_container_width=True
        )

        if submitted:

            selected_station_code = station_options[
                selected_station_label
            ]

            if weight <= 0:

                st.warning(
                    "Please enter a valid contribution weight."
                )

            else:

                try:

                    user_id = st.session_state.get("user_id")

                    contribution_data = {
                        "user_id": user_id,
                        "station_code": selected_station_code,
                        "material_type": material_type,
                        "weight": float(weight)
                    }

                    response = (
                        supabase
                        .table("waste_contributions")
                        .insert(contribution_data)
                        .execute()
                    )

                    if response.data:

                        st.success(
                            "Your waste contribution has been submitted!"
                        )

                        st.info(
                            "Status: Pending verification. "
                            "Your contribution will count towards "
                            "verified impact after approval."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "The contribution could not be confirmed. "
                            "Please try again."
                        )

                except Exception:

                    st.error(
                        "We could not submit your contribution. "
                        "Please check your connection and try again."
                    )

    # -----------------------------------------------
    # VERIFICATION EXPLANATION
    # -----------------------------------------------

    st.divider()

    st.subheader("What happens after submission?")

    eco_card(
        "1. Contribution submitted",
        "Your material type, weight and selected station "
        "are recorded in EcoLoop Node.",
        "📝"
    )

    eco_card(
        "2. Verification",
        "A coordinator reviews the contribution before "
        "it is accepted as verified.",
        "🔍"
    )

    eco_card(
        "3. Environmental impact",
        "Approved contributions can contribute to your "
        "verified waste totals and the community leaderboard.",
        "🌍"
    )

    st.caption(
        "Submitting a contribution does not automatically "
        "award points or mark it as verified."
    )

# =====================================================
# PAGE 7 — ENVIRONMENTAL IMPACT
# =====================================================

def environmental_impact_page():

    st.title("🌍 Environmental Impact")

    st.write(
        "Explore the measurable environmental "
        "contributions recorded through EcoLoop Node."
    )

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    # -----------------------------------------------
    # LOAD VERIFIED CONTRIBUTIONS
    # -----------------------------------------------

    try:

        response = (
            supabase
            .table("waste_contributions")
            .select(
                "material_type, weight, points, submitted_at"
            )
            .eq("verification_status", "verified")
            .execute()
        )

        contributions = response.data or []

    except Exception:

        st.error(
            "Environmental impact information could not be loaded."
        )
        return

    if not contributions:

        st.info(
            "No verified contributions have been recorded yet. "
            "The environmental dashboard will grow as contributions "
            "are verified."
        )
        return

    # -----------------------------------------------
    # CALCULATE TOTAL IMPACT
    # -----------------------------------------------

    total_weight = sum(
        float(item.get("weight") or 0)
        for item in contributions
    )

    total_contributions = len(contributions)

    total_points = sum(
        int(item.get("points") or 0)
        for item in contributions
    )

    unique_materials = len(set(
        item.get("material_type")
        for item in contributions
        if item.get("material_type")
    ))

    # -----------------------------------------------
    # MAIN IMPACT METRICS
    # -----------------------------------------------

    st.subheader("Community Impact Overview")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Verified Waste",
            f"{total_weight:,.2f} kg"
        )

    with col2:

        st.metric(
            "Verified Contributions",
            total_contributions
        )

    col3, col4 = st.columns(2)

    with col3:

        st.metric(
            "Material Categories",
            unique_materials
        )

    with col4:

        st.metric(
            "Points Awarded",
            total_points
        )

    st.divider()

    # -----------------------------------------------
    # MATERIAL BREAKDOWN
    # -----------------------------------------------

    st.subheader("Waste by Material Type")

    material_totals = {}

    for item in contributions:

        material = item.get(
            "material_type",
            "Other"
        )

        weight = float(item.get("weight") or 0)

        material_totals[material] = (
            material_totals.get(material, 0) + weight
        )

    material_df = pd.DataFrame(
        [
            {
                "Material": material,
                "Weight (kg)": weight
            }
            for material, weight in material_totals.items()
        ]
    )

    material_df = material_df.sort_values(
        "Weight (kg)",
        ascending=False
    )

    st.bar_chart(
        material_df.set_index("Material")
    )

    st.dataframe(
        material_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # -----------------------------------------------
    # CONTRIBUTION HISTORY
    # -----------------------------------------------

    st.subheader("Verified Contribution Records")

    history_rows = []

    for item in contributions:

        history_rows.append({
            "Material": item.get("material_type", "Unknown"),
            "Weight (kg)": float(item.get("weight") or 0),
            "Date": item.get("submitted_at", "")
        })

    history_df = pd.DataFrame(history_rows)

    if "Date" in history_df.columns:

        history_df = history_df.sort_values(
            "Date",
            ascending=False
        )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # -----------------------------------------------
    # ENVIRONMENTAL MESSAGE
    # -----------------------------------------------

    eco_card(
        "Measuring collective action",
        "Every verified contribution adds to the community's "
        "record of responsible waste management. These figures "
        "represent recorded waste weights, not estimates of "
        "carbon emissions or pollution prevented.",
        "🌱"
    )

# =====================================================
# PAGE 8 — COMMUNITY LEADERBOARD
# =====================================================

def leaderboard_page():

    st.title("🏆 Community Leaderboard")

    st.write(
        "Recognising individuals and communities "
        "contributing towards a cleaner environment."
    )

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    # -----------------------------------------------
    # LOAD VERIFIED CONTRIBUTIONS
    # -----------------------------------------------

    try:

        response = (
            supabase
            .table("waste_contributions")
            .select("user_id, weight, points")
            .eq("verification_status", "verified")
            .execute()
        )

        contributions = response.data or []

    except Exception:

        st.error("Leaderboard information could not be loaded.")
        return

    if not contributions:

        show_empty_state(
            "The leaderboard will appear once members have "
            "verified waste contributions."
        )
        return

    # -----------------------------------------------
    # CALCULATE INDIVIDUAL SCORES
    # -----------------------------------------------

    individual_scores = {}

    for item in contributions:

        user_id = item.get("user_id")

        if not user_id:
            continue

        if user_id not in individual_scores:

            individual_scores[user_id] = {
                "weight": 0.0,
                "points": 0
            }

        individual_scores[user_id]["weight"] += float(
            item.get("weight") or 0
        )

        individual_scores[user_id]["points"] += int(
            item.get("points") or 0
        )

    # -----------------------------------------------
    # LOAD MEMBER PROFILES
    # -----------------------------------------------

    profiles = {}

    try:

        profile_response = (
            supabase
            .table("profiles")
            .select("id, full_name")
            .execute()
        )

        for profile in profile_response.data or []:

            profiles[profile["id"]] = profile.get(
                "full_name",
                "EcoLoop Member"
            )

    except Exception:

        st.warning(
            "Member names could not be loaded. "
            "User IDs will be displayed instead."
        )

    # -----------------------------------------------
    # BUILD INDIVIDUAL LEADERBOARD
    # -----------------------------------------------

    ranking_rows = []

    for user_id, score in individual_scores.items():

        ranking_rows.append({
            "Member": profiles.get(
                user_id,
                "EcoLoop Member"
            ),
            "Verified Waste (kg)": round(
                score["weight"], 2
            ),
            "Points": score["points"]
        })

    ranking_rows.sort(
        key=lambda row: (
            row["Points"],
            row["Verified Waste (kg)"]
        ),
        reverse=True
    )

    st.subheader("🌟 Individual Rankings")

    if ranking_rows:

        for position, member in enumerate(
            ranking_rows[:3],
            start=1
        ):

            medal = {
                1: "🥇",
                2: "🥈",
                3: "🥉"
            }.get(position, "🏅")

            st.markdown(
                f"""
                <div class="eco-card">
                    <div class="eco-card-title">
                        {medal} {position}. {member['Member']}
                    </div>
                    <div class="eco-card-description">
                        {member['Verified Waste (kg)']:.2f} kg
                        verified · {member['Points']} points
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.dataframe(
            pd.DataFrame(ranking_rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        show_empty_state(
            "No individual rankings are available yet."
        )

    st.divider()

    # -----------------------------------------------
    # TEAM LEADERBOARD
    # -----------------------------------------------

    st.subheader("🤝 Community Team Rankings")

    st.caption(
        "Team rankings are based on verified contributions "
        "from members with approved group memberships."
    )

    try:

        membership_response = (
            supabase
            .table("group_memberships")
            .select("*")
            .eq("status", "approved")
            .execute()
        )

        memberships = membership_response.data or []

        group_response = (
            supabase
            .table("community_groups")
            .select("*")
            .execute()
        )

        groups = group_response.data or []

        group_names = {}

        for group in groups:

            group_id = group.get("id")

            group_name = (
                group.get("group_name")
                or group.get("name")
                or group.get("title")
                or "Community Group"
            )

            if group_id:
                group_names[group_id] = group_name

        user_groups = {}

        for membership in memberships:

            user_id = membership.get("user_id")
            group_id = membership.get("group_id")

            if user_id and group_id:
                user_groups.setdefault(
                    user_id, set()
                ).add(group_id)

        team_scores = {}

        for user_id, score in individual_scores.items():

            for group_id in user_groups.get(user_id, set()):

                if group_id not in team_scores:

                    team_scores[group_id] = {
                        "weight": 0.0,
                        "points": 0
                    }

                team_scores[group_id]["weight"] += score["weight"]
                team_scores[group_id]["points"] += score["points"]

        team_rows = []

        for group_id, score in team_scores.items():

            team_rows.append({
                "Community Group": group_names.get(
                    group_id,
                    "Community Group"
                ),
                "Verified Waste (kg)": round(
                    score["weight"], 2
                ),
                "Points": score["points"]
            })

        team_rows.sort(
            key=lambda row: (
                row["Points"],
                row["Verified Waste (kg)"]
            ),
            reverse=True
        )

        if team_rows:

            st.dataframe(
                pd.DataFrame(team_rows),
                use_container_width=True,
                hide_index=True
            )

        else:

            show_empty_state(
                "Team rankings will appear when groups have "
                "approved members with verified contributions."
            )

    except Exception:

        st.info(
            "Team rankings are not available yet. "
            "The existing group membership structure needs "
            "to be checked before this section can be connected."
        )

    st.divider()

    eco_card(
        "Recognition through participation",
        "EcoLoop rankings recognise recorded, verified "
        "environmental contributions. Rankings are updated "
        "as new contributions are approved.",
        "🌍"
    )

# =====================================================
# PAGE 9 — EXPLORE & LEARN
# =====================================================

def explore_learn_page():

    st.title("📚 Explore & Learn")

    st.write(
        "Discover environmental knowledge, "
        "sustainable practices and practical ways "
        "to protect our communities."
    )

    # -----------------------------------------------
    # LEARNING TOPICS
    # -----------------------------------------------

    LEARNING_TOPICS = [

        {
            "title": "Understanding Waste Management",
            "icon": "♻️",
            "description": (
                "Learn what waste management means, why it matters "
                "and how communities can manage waste responsibly."
            ),
            "content": """
            Waste management refers to the collection,
            transportation, sorting, treatment and disposal
            of waste.

            **Key ideas:**

            - Reduce unnecessary waste.
            - Reuse materials whenever possible.
            - Recycle suitable materials.
            - Dispose of waste responsibly.

            **Community example:**

            Households can separate plastic bottles, paper
            and metal rather than mixing everything together.
            """
        },

        {
            "title": "The Circular Economy",
            "icon": "🔄",
            "description": (
                "Understand how materials can remain useful "
                "instead of becoming waste."
            ),
            "content": """
            A circular economy aims to reduce waste by keeping
            products and materials in use for longer.

            **Key ideas:**

            - Design products to last.
            - Repair instead of immediately replacing.
            - Reuse and recycle materials.
            - Reduce unnecessary consumption.

            **Community example:**

            A school can collect used paper for recycling
            rather than throwing it away.
            """
        },

        {
            "title": "Plastic Pollution",
            "icon": "🌊",
            "description": (
                "Explore the effects of plastic pollution "
                "on land, water and communities."
            ),
            "content": """
            Plastic pollution occurs when plastic materials
            accumulate in the environment.

            **Key ideas:**

            - Plastic can persist in the environment.
            - Poor disposal can block drainage systems.
            - Plastic can harm wildlife.
            - Responsible collection and recycling help
              reduce plastic waste.
            """
        },

        {
            "title": "Climate Action",
            "icon": "🌍",
            "description": (
                "Learn about climate change and actions "
                "that support environmental sustainability."
            ),
            "content": """
            Climate action includes efforts to address
            climate change and reduce its impacts.

            **Key ideas:**

            - Protect natural ecosystems.
            - Use resources responsibly.
            - Support sustainable transport.
            - Improve waste management.
            - Participate in environmental education.

            **Community example:**

            Communities can organise local clean-up
            activities and tree-protection initiatives.
            """
        },

        {
            "title": "Electronic Waste",
            "icon": "🔌",
            "description": (
                "Understand electronic waste and why "
                "responsible handling is important."
            ),
            "content": """
            Electronic waste, also called e-waste, includes
            discarded electrical and electronic equipment.

            Examples include:

            - Old mobile phones.
            - Computers and keyboards.
            - Broken electronic equipment.
            - Discarded cables and chargers.

            **Important:**

            Some electronic waste contains hazardous
            materials. Use appropriate collection and
            recycling services instead of dismantling
            or burning electronic equipment.
            """
        },

        {
            "title": "Community Environmental Action",
            "icon": "🤝",
            "description": (
                "Discover how individuals and organisations "
                "can work together to protect the environment."
            ),
            "content": """
            Environmental protection becomes stronger
            when communities participate.

            **Possible activities:**

            - Community clean-up campaigns.
            - Waste separation programmes.
            - Environmental awareness sessions.
            - School recycling initiatives.
            - Protection of local green spaces.

            **Remember:**

            Sustainable change requires participation,
            cooperation and consistent action.
            """
        }
    ]

    # -----------------------------------------------
    # DISPLAY LEARNING TOPICS
    # -----------------------------------------------

    st.subheader("Learning Library")

    st.caption(
        "Select a topic to explore its learning notes."
    )

    for index, topic in enumerate(LEARNING_TOPICS):

        with st.expander(
            f"{topic['icon']} {topic['title']}"
        ):

            st.write(topic["description"])

            st.divider()

            st.markdown(topic["content"])

    st.divider()

    # -----------------------------------------------
    # LEARNING MESSAGE
    # -----------------------------------------------

    eco_card(
        "Knowledge creates action",
        "Environmental protection begins with understanding "
        "the challenges around us and learning how to respond "
        "through responsible community action.",
        "🌱"
    )

    st.caption(
        "EcoLoop Node — Learn. Participate. Make an impact."
    )

# =====================================================
# PAGE 10 — ECO QUIZ
# =====================================================

def get_quiz_options(question):

    raw_options = question.get("options")

    # Options stored as a dictionary
    if isinstance(raw_options, dict):

        return {
            str(key): str(value)
            for key, value in raw_options.items()
            if value is not None
        }

    # Options stored as a list
    if isinstance(raw_options, list):

        result = {}

        for index, option in enumerate(raw_options):

            default_key = chr(65 + index)

            if isinstance(option, dict):

                key = (
                    option.get("value")
                    or option.get("key")
                    or option.get("label")
                    or default_key
                )

                value = (
                    option.get("text")
                    or option.get("option_text")
                    or option.get("answer")
                    or option.get("label")
                    or str(option)
                )

                result[str(key)] = str(value)

            else:

                result[default_key] = str(option)

        return result

    # Options stored in separate database columns
    result = {}

    for letter, number in zip(
        ["A", "B", "C", "D"],
        ["1", "2", "3", "4"]
    ):

        value = (
            question.get(f"option_{letter.lower()}")
            or question.get(f"option{number}")
            or question.get(f"choice_{letter.lower()}")
        )

        if value is not None:
            result[letter] = str(value)

    return result


def get_quiz_result_data(response):

    data = getattr(response, "data", None)

    if isinstance(data, list) and data:
        return data[0]

    if isinstance(data, dict):
        return data

    return {}


def reset_quiz_session():

    st.session_state["quiz_attempt_id"] = None
    st.session_state["active_quiz_id"] = None
    st.session_state["active_quiz_title"] = None
    st.session_state["active_quiz_questions"] = []
    st.session_state["quiz_question_index"] = 0
    st.session_state["quiz_last_result"] = None
    st.session_state["quiz_completed"] = False
    st.session_state["quiz_final_score"] = None


def eco_quiz_page():

    st.title("🧠 Eco Quiz")

    st.write(
        "Test your environmental knowledge, "
        "learn new facts and earn points through "
        "approved quiz participation."
    )

    # -----------------------------------------------
    # LOGIN REQUIREMENT
    # -----------------------------------------------

    if not require_login():
        return

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    # -----------------------------------------------
    # INITIALISE QUIZ SESSION VARIABLES
    # -----------------------------------------------

    quiz_defaults = {
        "quiz_attempt_id": None,
        "active_quiz_id": None,
        "active_quiz_title": None,
        "active_quiz_questions": [],
        "quiz_question_index": 0,
        "quiz_last_result": None,
        "quiz_completed": False,
        "quiz_final_score": None
    }

    for key, value in quiz_defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

    # -----------------------------------------------
    # LOAD AVAILABLE QUIZZES
    # -----------------------------------------------

    try:

        quiz_response = (
            supabase
            .table("quizzes")
            .select("*")
            .execute()
        )

        all_quizzes = quiz_response.data or []

    except Exception:

        st.error("Available quizzes could not be loaded.")
        return

    active_quizzes = [
        quiz for quiz in all_quizzes
        if quiz.get(
            "is_active",
            quiz.get("active", True)
        )
    ]

    if not active_quizzes and not st.session_state["quiz_attempt_id"]:

        show_empty_state(
            "There are no active quizzes available at the moment."
        )
        return

    # -----------------------------------------------
    # QUIZ SELECTION
    # -----------------------------------------------

    if not st.session_state["quiz_attempt_id"]:

        st.subheader("Available Quizzes")

        quiz_options = {}

        for quiz in active_quizzes:

            quiz_id = quiz.get("id")

            if not quiz_id:
                continue

            title = (
                quiz.get("title")
                or quiz.get("quiz_title")
                or quiz.get("name")
                or "Environmental Quiz"
            )

            quiz_options[title] = quiz

        if not quiz_options:

            show_empty_state(
                "No usable quizzes were found."
            )
            return

        selected_title = st.selectbox(
            "Choose a quiz",
            options=list(quiz_options.keys())
        )

        selected_quiz = quiz_options[selected_title]

        description = (
            selected_quiz.get("description")
            or selected_quiz.get("quiz_description")
            or "Test your environmental knowledge."
        )

        st.write(description)

        if st.button(
            "Start Quiz",
            use_container_width=True
        ):

            try:

                quiz_id = selected_quiz.get("id")

                question_response = (
                    supabase
                    .table("quiz_questions")
                    .select("*")
                    .eq("quiz_id", quiz_id)
                    .execute()
                )

                questions = question_response.data or []

                if not questions:

                    st.warning(
                        "This quiz does not have any questions yet."
                    )
                    return

                # Create an attempt.
                # The existing database trigger validates it.

                attempt_response = (
                    supabase
                    .table("quiz_attempts")
                    .insert({
                        "user_id": st.session_state["user_id"],
                        "quiz_id": quiz_id
                    })
                    .execute()
                )

                attempt_data = attempt_response.data or []

                if not attempt_data:

                    st.error(
                        "The quiz attempt could not be started."
                    )
                    return

                attempt_id = attempt_data[0].get("id")

                if not attempt_id:

                    st.error(
                        "The database did not return an attempt ID."
                    )
                    return

                st.session_state["quiz_attempt_id"] = attempt_id
                st.session_state["active_quiz_id"] = quiz_id
                st.session_state["active_quiz_title"] = selected_title
                st.session_state["active_quiz_questions"] = questions
                st.session_state["quiz_question_index"] = 0
                st.session_state["quiz_last_result"] = None
                st.session_state["quiz_completed"] = False
                st.session_state["quiz_final_score"] = None

                st.rerun()

            except Exception:

                st.error(
                    "The quiz could not be started. "
                    "Please try again."
                )

        return

    # -----------------------------------------------
    # ACTIVE QUIZ
    # -----------------------------------------------

    st.subheader(
        st.session_state["active_quiz_title"]
    )

    questions = st.session_state["active_quiz_questions"]

    current_index = st.session_state["quiz_question_index"]

    # -----------------------------------------------
    # COMPLETED QUIZ
    # -----------------------------------------------

    if st.session_state["quiz_completed"]:

        st.success("Quiz completed!")

        final_score = st.session_state.get(
            "quiz_final_score"
        )

        if final_score is not None:

            st.metric(
                "Your Final Score",
                final_score
            )

        st.write(
            "Your completed attempt has been processed "
            "by the EcoLoop Node database."
        )

        if st.button(
            "Return to Quiz Library",
            use_container_width=True
        ):

            reset_quiz_session()
            st.rerun()

        return

    # -----------------------------------------------
    # CHECK QUESTION POSITION
    # -----------------------------------------------

    if current_index >= len(questions):

        st.error(
            "The quiz has reached an unexpected state."
        )
        return

    question = questions[current_index]

    question_text = (
        question.get("question_text")
        or question.get("question")
        or question.get("text")
        or "Question text unavailable."
    )

    options = get_quiz_options(question)

    if not options:

        st.error(
            "The answer options for this question "
            "could not be loaded."
        )
        return

    # -----------------------------------------------
    # PROGRESS
    # -----------------------------------------------

    total_questions = len(questions)

    progress = (
        (current_index + 1) / total_questions
    )

    st.progress(progress)

    st.caption(
        f"Question {current_index + 1} of {total_questions}"
    )

    st.markdown(f"### {question_text}")

    # -----------------------------------------------
    # DISPLAY PREVIOUS ANSWER FEEDBACK
    # -----------------------------------------------

    previous_result = st.session_state.get(
        "quiz_last_result"
    )

    if previous_result:

        if previous_result.get("is_correct") is True:
            st.success("Your answer was correct.")

        elif previous_result.get("is_correct") is False:
            st.error("Your answer was not correct.")

        explanation = previous_result.get("explanation")

        if explanation:
            st.info(explanation)

        if current_index < total_questions:

            if st.button(
                "Next Question",
                use_container_width=True
            ):

                st.session_state["quiz_question_index"] += 1
                st.session_state["quiz_last_result"] = None
                st.rerun()

        return

    # -----------------------------------------------
    # ANSWER SUBMISSION
    # -----------------------------------------------

    with st.form(
        f"quiz_question_form_{current_index}"
    ):

        selected_key = st.radio(
            "Choose your answer",
            options=list(options.keys()),
            format_func=lambda key: (
                f"{key}. {options[key]}"
            )
        )

        submitted = st.form_submit_button(
            "Submit Answer",
            use_container_width=True
        )

        if submitted:

            try:

                answer_response = supabase.rpc(
                    "submit_quiz_answer",
                    {
                        "p_attempt_id": (
                            st.session_state["quiz_attempt_id"]
                        ),
                        "p_question_id": question["id"],
                        "p_selected_option": selected_key
                    }
                ).execute()

                result = get_quiz_result_data(
                    answer_response
                )

                if not result:

                    st.error(
                        "The database did not return "
                        "an answer result."
                    )
                    return

                is_correct = result.get(
                    "is_correct",
                    result.get("correct")
                )

                st.session_state["quiz_last_result"] = {
                    "is_correct": is_correct,
                    "explanation": result.get("explanation"),
                }

                # Finish the attempt after the final answer.

                if current_index == total_questions - 1:

                    finish_response = supabase.rpc(
                        "finish_quiz_attempt",
                        {
                            "p_attempt_id": (
                                st.session_state["quiz_attempt_id"]
                            )
                        }
                    ).execute()

                    finish_data = get_quiz_result_data(
                        finish_response
                    )

                    final_score = finish_data.get("score")

                    if final_score is None:

                        try:

                            attempt_result = (
                                supabase
                                .table("quiz_attempts")
                                .select("score")
                                .eq(
                                    "id",
                                    st.session_state["quiz_attempt_id"]
                                )
                                .maybe_single()
                                .execute()
                            )

                            if attempt_result.data:
                                final_score = attempt_result.data.get(
                                    "score"
                                )

                        except Exception:
                            pass

                    st.session_state["quiz_final_score"] = final_score
                    st.session_state["quiz_completed"] = True

                st.rerun()

            except Exception:

                st.error(
                    "Your answer could not be submitted. "
                    "Please try again."
                )

    st.caption(
        "Your answers are checked securely by the EcoLoop "
        "Node database."
    )

# =====================================================
# PAGE 11 — COMMUNITY GROUPS
# =====================================================

def community_groups_page():

    st.title("🤝 Community Groups")

    st.write(
        "Connect with people, schools and organisations "
        "working towards environmental protection."
    )

    if not supabase:
        st.error("The database connection is unavailable.")
        return

    if not require_login():
        return

    user_id = st.session_state.get("user_id")

    # -----------------------------------------------
    # LOAD COMMUNITY GROUPS
    # -----------------------------------------------

    try:

        group_response = (
            supabase
            .table("community_groups")
            .select("*")
            .execute()
        )

        groups = group_response.data or []

    except Exception:

        st.error("Community groups could not be loaded.")
        return

    if not groups:

        show_empty_state(
            "There are no community groups available yet."
        )
        return

    # -----------------------------------------------
    # LOAD MEMBER'S EXISTING MEMBERSHIPS
    # -----------------------------------------------

    try:

        membership_response = (
            supabase
            .table("group_memberships")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        memberships = membership_response.data or []

    except Exception:

        st.error("Your membership information could not be loaded.")
        return

    membership_by_group = {}

    for membership in memberships:

        group_id = membership.get("group_id")

        if group_id:
            membership_by_group[group_id] = membership

    # -----------------------------------------------
    # GROUP SUMMARY
    # -----------------------------------------------

    st.subheader("Explore Environmental Groups")

    st.caption(
        f"{len(groups)} registered community group(s)"
    )

    # -----------------------------------------------
    # DISPLAY GROUPS
    # -----------------------------------------------

    for group in groups:

        group_id = group.get("id")

        if not group_id:
            continue

        group_name = (
            group.get("group_name")
            or group.get("name")
            or group.get("title")
            or "Environmental Community Group"
        )

        description = (
            group.get("description")
            or group.get("group_description")
            or "A community working towards environmental action."
        )

        membership = membership_by_group.get(group_id)

        with st.container(border=True):

            st.subheader(f"🌱 {group_name}")

            st.write(description)

            if group.get("location"):
                st.caption(
                    f"📍 {group.get('location')}"
                )

            st.divider()

            # ---------------------------------------
            # EXISTING MEMBERSHIP
            # ---------------------------------------

            if membership:

                status = membership.get(
                    "status",
                    "unknown"
                )

                if status == "approved":

                    st.success(
                        "You are an approved member of this group."
                    )

                elif status == "pending":

                    st.info(
                        "Your membership request is awaiting approval."
                    )

                elif status == "rejected":

                    st.warning(
                        "Your previous membership request was not approved."
                    )

                else:

                    st.caption(
                        f"Membership status: {status}"
                    )

            else:

                # -----------------------------------
                # REQUEST MEMBERSHIP
                # -----------------------------------

                if st.button(
                    "Request to Join",
                    key=f"join_group_{group_id}",
                    use_container_width=True
                ):

                    try:

                        supabase.table(
                            "group_memberships"
                        ).insert({
                            "group_id": group_id,
                            "user_id": user_id,
                            "status": "pending"
                        }).execute()

                        st.success(
                            "Your membership request has been submitted."
                        )

                        st.rerun()

                    except Exception:

                        st.error(
                            "Your request could not be submitted. "
                            "You may already have a membership request "
                            "or the group may not accept new members."
                        )

    st.divider()

    # -----------------------------------------------
    # MEMBERSHIP EXPLANATION
    # -----------------------------------------------

    eco_card(
        "Growing environmental communities",
        "Community groups provide opportunities for members "
        "to collaborate, exchange ideas and participate in "
        "environmental initiatives. Membership requests are "
        "subject to group approval.",
        "🤝"
    )

# =====================================================
# PAGE 12 — ENVIRONMENTAL CHALLENGES
# =====================================================

def challenges_page():

    section_heading(
        "Environmental Challenges",
        "Take part in practical activities that create positive environmental change."
    )

    if not require_login():
        return

    user_id = st.session_state.get("user_id")

    try:
        challenges_response = (
            supabase.table("community_challenges")
            .select("*")
            .execute()
        )

        challenges = challenges_response.data or []

    except Exception:
        st.error("We could not load environmental challenges.")
        return

    if not challenges:
        show_empty_state(
            "There are no environmental challenges available yet."
        )
        return

    try:
        participation_response = (
            supabase.table("challenge_participants")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        participations = participation_response.data or []

    except Exception:
        participations = []

    joined_ids = {
        str(item.get("challenge_id"))
        for item in participations
        if item.get("challenge_id") is not None
    }

    st.write("Explore the challenges below and choose one to participate in.")

    for challenge in challenges:

        challenge_id = challenge.get("id")
        challenge_name = (
            challenge.get("challenge_name")
            or challenge.get("title")
            or challenge.get("name")
            or "Environmental Challenge"
        )

        description = (
            challenge.get("description")
            or challenge.get("challenge_description")
            or "Help your community take environmental action."
        )

        status = challenge.get("status", "Available")
        start_date = challenge.get("start_date")
        end_date = challenge.get("end_date")

        with st.container(border=True):

            st.subheader(f"🌍 {challenge_name}")

            st.write(description)

            col1, col2 = st.columns(2)

            with col1:
                st.caption(f"Status: {status}")

            with col2:
                if end_date:
                    st.caption(f"Ends: {end_date}")

            if start_date:
                st.caption(f"Starts: {start_date}")

            if str(challenge_id) in joined_ids:

                st.success("You have joined this challenge.")

            elif challenge_id is not None:

                if st.button(
                    "Join Challenge",
                    key=f"join_challenge_{challenge_id}",
                    use_container_width=True
                ):

                    try:
                        supabase.table(
                            "challenge_participants"
                        ).insert({
                            "challenge_id": challenge_id,
                            "user_id": user_id
                        }).execute()

                        st.success("You have joined the challenge!")
                        st.rerun()

                    except Exception:
                        st.warning(
                            "We could not register your participation. "
                            "You may already be registered, or the database "
                            "may require additional information."
                        )

            else:
                st.caption("Participation is not available for this challenge yet.")

# =====================================================
# PAGE 13 — ACTION GALLERY
# =====================================================

def action_gallery_page():

    section_heading(
        "Action Gallery",
        "Discover environmental actions and community initiatives."
    )

    try:
        response = (
            supabase.table("environmental_actions")
            .select("*")
            .execute()
        )

        actions = response.data or []

    except Exception:
        st.error("We could not load the Action Gallery.")
        return

    public_actions = []

    for action in actions:

        status = str(
            action.get("status", "")
        ).lower()

        verification_status = str(
            action.get("verification_status", "")
        ).lower()

        if status in ["approved", "published", "verified"] or \
           verification_status in ["approved", "verified"]:

            public_actions.append(action)

    if not public_actions:

        show_empty_state(
            "No approved environmental actions are available yet. "
            "Check back as more community activities are verified."
        )

        return

    st.write(
        "Here are environmental activities recognised by the EcoLoop community."
    )

    for action in public_actions:

        title = (
            action.get("title")
            or action.get("action_name")
            or action.get("name")
            or "Community Environmental Action"
        )

        description = (
            action.get("description")
            or action.get("action_description")
            or "An environmental action shared by the community."
        )

        category = (
            action.get("category")
            or action.get("action_type")
            or "Environmental Action"
        )

        created_at = (
            action.get("created_at")
            or action.get("submitted_at")
        )

        with st.container(border=True):

            st.subheader(f"🌱 {title}")

            st.caption(f"Category: {category}")

            st.write(description)

            if created_at:
                st.caption(f"Submitted: {created_at}")

# =====================================================
# PAGE 14 — COLLECTION MANAGEMENT
# =====================================================

def collection_management_page():

    section_heading(
        "Collection Management",
        "View EcoLoop collection stations and recorded collection activity."
    )

    if not require_login():
        return

    # ---------------------------------------------
    # COLLECTION STATIONS
    # ---------------------------------------------

    st.subheader("📍 Collection Stations")

    try:
        stations = load_collection_stations()

    except Exception:
        stations = []

    if stations:

        for station in stations:

            station_code = station.get("station_code", "N/A")

            station_name = (
                station.get("station_name")
                or station_code
            )

            with st.container(border=True):

                st.markdown(f"**{station_name}**")

                st.caption(f"Station code: {station_code}")

    else:

        show_empty_state(
            "No collection stations are currently available."
        )

    # ---------------------------------------------
    # COLLECTION RECORDS
    # ---------------------------------------------

    st.divider()

    st.subheader("📦 Collection Records")

    try:
        records_response = (
            supabase.table("collection_records")
            .select("*")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        records = records_response.data or []

    except Exception:

        records = []

        st.info(
            "Collection records are not available through your current access."
        )

    if records:

        display_records = []

        for record in records:

            display_records.append({
                "Station": (
                    record.get("station_code")
                    or record.get("station_name")
                    or "N/A"
                ),
                "Material": (
                    record.get("material_type")
                    or record.get("material")
                    or "N/A"
                ),
                "Weight (kg)": (
                    record.get("weight")
                    or record.get("quantity")
                    or 0
                ),
                "Date": (
                    record.get("created_at")
                    or record.get("collected_at")
                    or "N/A"
                )
            })

        st.dataframe(
            pd.DataFrame(display_records),
            use_container_width=True,
            hide_index=True
        )

    else:

        show_empty_state(
            "No collection records are available yet."
        )

# =====================================================
# PAGE 15 — NOTIFICATIONS CENTRE
# =====================================================

def notifications_page():

    section_heading(
        "Notifications Centre",
        "Keep track of your EcoLoop activity and account updates."
    )

    if not require_login():
        return

    user_id = st.session_state.get("user_id")

    notification_items = []

    # ---------------------------------------------
    # WASTE CONTRIBUTION UPDATES
    # ---------------------------------------------

    try:
        waste_response = (
            supabase.table("waste_contributions")
            .select("*")
            .eq("user_id", user_id)
            .order("submitted_at", desc=True)
            .limit(20)
            .execute()
        )

        contributions = waste_response.data or []

        for item in contributions:

            status = str(
                item.get("verification_status", "pending")
            ).lower()

            material = item.get("material_type", "Waste")
            weight = item.get("weight", 0)

            if status == "verified":

                message = (
                    f"Your {material} contribution of {weight} kg "
                    "has been verified."
                )

                icon = "✅"

            elif status == "rejected":

                message = (
                    f"Your {material} contribution of {weight} kg "
                    "was not approved."
                )

                icon = "⚠️"

            else:

                message = (
                    f"Your {material} contribution of {weight} kg "
                    "is awaiting verification."
                )

                icon = "⏳"

            notification_items.append({
                "date": item.get("submitted_at", ""),
                "icon": icon,
                "message": message
            })

    except Exception:
        st.info("Waste contribution updates are currently unavailable.")

    # ---------------------------------------------
    # COMMUNITY GROUP UPDATES
    # ---------------------------------------------

    try:
        membership_response = (
            supabase.table("group_memberships")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        memberships = membership_response.data or []

        for membership in memberships:

            status = str(
                membership.get("status", "pending")
            ).lower()

            if status == "approved":

                message = "Your community group membership has been approved."
                icon = "🎉"

            elif status == "rejected":

                message = "Your community group membership was not approved."
                icon = "⚠️"

            else:

                message = "Your community group membership request is pending."
                icon = "⏳"

            notification_items.append({
                "date": membership.get("created_at", ""),
                "icon": icon,
                "message": message
            })

    except Exception:
        st.info("Community group updates are currently unavailable.")

    # ---------------------------------------------
    # DISPLAY NOTIFICATIONS
    # ---------------------------------------------

    st.divider()

    if notification_items:

        notification_items.sort(
            key=lambda item: str(item.get("date") or ""),
            reverse=True
        )

        for item in notification_items:

            with st.container(border=True):

                st.markdown(
                    f"### {item['icon']} {item['message']}"
                )

                if item["date"]:
                    st.caption(f"Date: {item['date']}")

    else:

        show_empty_state(
            "You have no activity updates yet. "
            "Your EcoLoop updates will appear here."
        )

    st.caption(
        "These updates are generated from your EcoLoop account activity. "
        "Push notifications are not enabled in this version."
    )

# =====================================================
# PAGE 16 — VERIFY CONTRIBUTIONS
# =====================================================

def verify_contributions_page():

    section_heading(
        "Verify Contributions",
        "Review and verify community waste contributions."
    )

    if not is_admin():
        st.error("Access denied. Administrator permissions are required.")
        return

    try:
        response = (
            supabase.table("waste_contributions")
            .select("*")
            .eq("verification_status", "pending")
            .order("submitted_at", desc=False)
            .execute()
        )

        contributions = response.data or []

    except Exception:
        st.error(
            "Pending contributions could not be loaded. "
            "Check the database permissions."
        )
        return

    if not contributions:

        show_empty_state(
            "There are no pending contributions to review."
        )

        return

    st.write(
        f"**{len(contributions)} contribution(s)** are awaiting review."
    )

    for contribution in contributions:

        contribution_id = contribution.get("id")

        with st.container(border=True):

            st.markdown(
                f"**Contribution ID:** `{contribution_id}`"
            )

            st.write(
                f"**User:** {contribution.get('user_id', 'N/A')}"
            )

            st.write(
                f"**Station:** {contribution.get('station_code', 'N/A')}"
            )

            st.write(
                f"**Material:** {contribution.get('material_type', 'N/A')}"
            )

            st.write(
                f"**Weight:** {contribution.get('weight', 0)} kg"
            )

            st.caption(
                f"Submitted: {contribution.get('submitted_at', 'N/A')}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Approve",
                    key=f"approve_{contribution_id}",
                    use_container_width=True
                ):

                    try:
                        (
                            supabase.table("waste_contributions")
                            .update({"verification_status": "verified"})
                            .eq("id", contribution_id)
                            .eq("verification_status", "pending")
                            .execute()
                        )

                        st.success("Contribution approved.")
                        st.rerun()

                    except Exception:
                        st.error(
                            "Approval failed. Check administrator "
                            "permissions and database verification rules."
                        )

            with col2:

                if st.button(
                    "Reject",
                    key=f"reject_{contribution_id}",
                    use_container_width=True
                ):

                    try:
                        (
                            supabase.table("waste_contributions")
                            .update({"verification_status": "rejected"})
                            .eq("id", contribution_id)
                            .eq("verification_status", "pending")
                            .execute()
                        )

                        st.warning("Contribution rejected.")
                        st.rerun()

                    except Exception:
                        st.error(
                            "Rejection failed. Check administrator "
                            "permissions and database verification rules."
                        )

# =====================================================
# PAGE 17 — ADMIN STUDIO
# =====================================================

def admin_studio_page():

    section_heading(
        "Admin Studio",
        "A central overview of EcoLoop Node activity and operations."
    )

    if not is_admin():
        st.error("Access denied. Administrator permissions are required.")
        return

    st.subheader("📊 Platform Overview")

    tables = {
        "Registered Members": "profiles",
        "Collection Stations": "collection_stations",
        "Waste Contributions": "waste_contributions",
        "Community Groups": "community_groups",
        "Environmental Actions": "environmental_actions",
        "Environmental Challenges": "community_challenges",
        "Collection Records": "collection_records"
    }

    metrics = {}

    for label, table_name in tables.items():

        try:
            response = (
                supabase.table(table_name)
                .select("*", count="exact")
                .limit(0)
                .execute()
            )

            metrics[label] = response.count or 0

        except Exception:
            metrics[label] = "Unavailable"

    metric_items = list(metrics.items())

    for index in range(0, len(metric_items), 2):

        col1, col2 = st.columns(2)

        with col1:
            label, value = metric_items[index]
            st.metric(label, value)

        if index + 1 < len(metric_items):

            with col2:
                label, value = metric_items[index + 1]
                st.metric(label, value)

    st.divider()

    st.subheader("⚙️ Administration")

    st.info(
        "Use the Verify Contributions page to review pending waste "
        "submissions. Other administrative operations remain subject "
        "to the permissions configured in Supabase."
    )

    st.caption(
        "This dashboard displays available database counts. "
        "It does not modify user accounts or database security settings."
    )

# =====================================================
# PAGE 18 — ABOUT NGIH
# =====================================================

def about_ngih_page():

    section_heading(
        "About Next Gen Impact Hub",
        "Building a generation of young people who lead, innovate and create impact."
    )

    st.markdown(
        f"## {NGIH_NAME}"
    )

    st.write(NGIH_MISSION)

    st.divider()

    st.subheader("Our Four Pillars")

    pillars = [
        (
            "🏛️ Governance & Civic Education",
            "Encouraging informed, responsible and active citizenship."
        ),
        (
            "🌍 Climate Action & Environment",
            "Promoting environmental protection, sustainability and climate action."
        ),
        (
            "💡 Business & Entrepreneurship",
            "Supporting enterprise, creativity and youth-led economic opportunities."
        ),
        (
            "🤖 Technology, Innovation, Media & Arts",
            "Using technology, innovation and creative expression to solve problems."
        )
    ]

    for title, description in pillars:

        with st.container(border=True):

            st.subheader(title)
            st.write(description)

    st.divider()

    st.subheader("About EcoLoop Node")

    st.write(
        "EcoLoop Node is an environmental technology initiative "
        "under NGIH's Climate Action & Environment pillar. "
        "It aims to encourage responsible waste management, "
        "community participation and measurable environmental action."
    )

    st.info(
        "Our vision is to turn everyday environmental action "
        "into meaningful community impact."
    )

    st.caption(f"Powered by {NGIH_NAME} (NGIH)")

# =====================================================
# PAGE 19 — SYSTEM DIAGNOSTICS
# =====================================================

def system_diagnostics_page():

    section_heading(
        "System Diagnostics",
        "Monitor the basic health and configuration of EcoLoop Node."
    )

    if not is_admin():
        st.error("Access denied. Administrator permissions are required.")
        return

    st.subheader("🔧 System Status")

    # ---------------------------------------------
    # APPLICATION STATUS
    # ---------------------------------------------

    st.metric("Application", APP_NAME)
    st.metric("Application Version", APP_VERSION)

    # ---------------------------------------------
    # DATABASE CONNECTION
    # ---------------------------------------------

    if supabase is not None:

        try:
            supabase.table("profiles").select("id").limit(1).execute()

            st.success("Database connection: Operational")

        except Exception as error:

            st.error("Database connection: Check required")

            st.caption(
                f"Error type: {type(error).__name__}"
            )

    else:

        st.error("Database connection: Not established")

        st.caption(
            f"Connection error type: {supabase_error or 'Unknown'}"
        )

    # ---------------------------------------------
    # SESSION STATUS
    # ---------------------------------------------

    st.divider()

    st.subheader("👤 Session Status")

    st.write(
        f"Login status: {'Logged in' if is_logged_in() else 'Logged out'}"
    )

    st.write(
        f"Administrator access: {'Yes' if is_admin() else 'No'}"
    )

    # ---------------------------------------------
    # CONFIGURATION
    # ---------------------------------------------

    st.divider()

    st.subheader("⚙️ Application Configuration")

    st.write(f"Application name: {APP_NAME}")

    st.write(f"Version: {APP_VERSION}")

    st.write("Database provider: Supabase")

    st.write("Interface framework: Streamlit")

    st.info(
        "This page performs basic connection checks only. "
        "It does not expose credentials, authentication tokens "
        "or private database information."
    )

    st.caption(
        "For technical errors, check the Streamlit application logs "
        "and Supabase project logs."
    )

# =====================================================
# FINAL SECTION — FOOTER AND APP ROUTER
# =====================================================

# ---------------------------------------------
# PAGE ROUTING
# ---------------------------------------------

PAGE_ROUTES = {

    "Home": home_page,

    "Login": login_form,
    "Register": registration_form,

    "EcoLoop Nodes": ecoloop_nodes_page,
    "Record Waste": record_waste_page,
    "Collection Management": collection_management_page,
    "Environmental Impact": environmental_impact_page,

    "Community Groups": community_groups_page,
    "Challenges": challenges_page,
    "Action Gallery": action_gallery_page,
    "Leaderboard": leaderboard_page,
    "Notifications Centre": notifications_page,

    "Explore & Learn": explore_learn_page,
    "Eco Quiz": eco_quiz_page,

    "Verify Contributions": verify_contributions_page,
    "Admin Studio": admin_studio_page,
    "System Diagnostics": system_diagnostics_page,

    "My Profile": account_page,
    "About NGIH": about_ngih_page
}


# ---------------------------------------------
# RENDER NAVIGATION
# ---------------------------------------------

render_navigation()
show_app_header()


# ---------------------------------------------
# DISPLAY SELECTED PAGE
# ---------------------------------------------

current_page = st.session_state.get(
    "current_page",
    "Home"
)

selected_page = PAGE_ROUTES.get(
    current_page,
    home_page
)

selected_page()

# ---------------------------------------------
# NGIH FOOTER — ECOLOOP NODE
# ---------------------------------------------

st.divider()

st.markdown("### ♻️ EcoLoop Node")

st.markdown("**Powered by Next Gen Impact Hub (NGIH)**")

st.caption("Designed by Munashe Roy Mutopa — Project Coordinator")

st.caption("Version 2.0")

st.caption("© 2026 Next Gen Impact Hub. All rights reserved.")
