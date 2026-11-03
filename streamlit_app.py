import streamlit as st
import pandas as pd
import qrcode
import io
import uuid

from datetime import date, datetime
from supabase import create_client


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="EcoLoop Node 2.0",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# SUPABASE CONNECTION
# =====================================================

@st.cache_resource
def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


try:
    supabase = get_supabase_client()
    st.sidebar.success("Supabase client initialised")

except Exception as e:
    supabase = None

    st.sidebar.error(
        f"Supabase connection setup error: "
        f"{type(e).__name__}: {e}"
    )


# =====================================================
# SESSION STATE
# =====================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"# =====================================================
# ECOLOOP NODE 2.0 — VISUAL DESIGN
# =====================================================

st.markdown("""
<style>

/* MAIN APPLICATION */

.stApp {
    background-color: #F4F8F3;
    color: #173B2B;
    font-family: 'DM Sans', sans-serif;
}

/* MAIN CONTENT */

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1250px;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background-color: #123D2A;
    border-right: 2px solid #A5D65E;
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* SIDEBAR HEADER */

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #B9E769 !important;
}

/* SIDEBAR BUTTONS */

section[data-testid="stSidebar"] button {
    background-color: #20543B;
    border: 1px solid #6C9F55;
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
}

section[data-testid="stSidebar"] button:hover {
    background-color: #367B4D;
    border-color: #C3F078;
}

/* MAIN HEADINGS */

h1, h2, h3 {
    color: #17452F !important;
    font-weight: 750;
}

/* HERO SECTION */

.eco-hero {
    background: linear-gradient(
        120deg,
        #123D2A,
        #176044,
        #27836A
    );
    padding: 35px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 5px 18px rgba(18, 61, 42, 0.12);
}

.eco-hero h1 {
    color: #FFFFFF !important;
    font-size: 2.4rem;
    margin-bottom: 10px;
}

.eco-hero p {
    color: #E6F5E8;
    font-size: 1.05rem;
}

/* CARDS */

.eco-card {
    background-color: #FFFFFF;
    border: 1px solid #DCE9DC;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 3px 12px rgba(20, 65, 43, 0.06);
}

.eco-card h3 {
    color: #176044 !important;
}

/* METRIC CARDS */

.metric-card {
    background-color: #E8F3E7;
    border-left: 5px solid #83B94B;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 12px;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #17452F;
}

.metric-label {
    font-size: 0.9rem;
    color: #55745F;
}

/* BUTTONS */

.stButton > button {
    background-color: #176044;
    color: white;
    border: none;
    border-radius: 10px;
    min-height: 42px;
    font-weight: 650;
}

.stButton > button:hover {
    background-color: #27836A;
    color: white;
    border: none;
}

/* INPUT FIELDS */

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    border-radius: 9px;
}

/* DIVIDERS */

hr {
    border-color: #D8E6D8;
}

/* FOOTER */

.eco-footer {
    text-align: center;
    color: #65816D;
    padding: 25px 10px;
    font-size: 0.85rem;
}

/* DARK MODE SUPPORT */

@media (prefers-color-scheme: dark) {

    .stApp {
        background-color: #101C16;
        color: #E6F2E8;
    }

    h1, h2, h3 {
        color: #B9E769 !important;
    }

    .eco-card {
        background-color: #1B2D22;
        border-color: #34533D;
    }

    .metric-card {
        background-color: #243B2B;
    }

    .metric-value {
        color: #D5F2A5;
    }

    .metric-label {
        color: #B5CBB8;
    }
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# ECOLOOP BRANDING
# =====================================================

APP_NAME = "EcoLoop Node 2.0"

APP_TAGLINE = (
    "Turning everyday environmental action "
    "into measurable community impact."
)

NGIH_NAME = "Next Gen Impact Hub"
# =====================================================
# ECOLOOP NODE 2.0 — FOUR MAIN NAVIGATION CATEGORIES
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
        "Leaderboard"
    ],

    "Learn & Grow": [
        "Explore & Learn",
        "Eco Quiz"
    ],

    "Account": [
        "My Profile",
        "Login / Register"
    ],

    "Administration": [
        "Verify Contributions",
        "Admin Studio",
        "System Diagnostics"
    ]
}

st.sidebar.markdown("## ECOLOOP NODE 2.0")
st.sidebar.caption("Environmental action. Connected communities.")

# Main category selector
main_categories = [
    "Home",
    "EcoLoop",
    "Community",
    "Learn & Grow",
    "Account"
]

if is_admin():
    main_categories.append("Administration")

if "main_category" not in st.session_state:
    st.session_state.main_category = "Home"

if st.session_state.main_category not in main_categories:
    st.session_state.main_category = "Home"

main_category = st.sidebar.radio(
    "MAIN MENU",
    main_categories,
    key="main_category"
)

# Sub-navigation
subpages = NAVIGATION[main_category]

if len(subpages) == 1:
    selected_page = subpages[0]
else:
    selected_page = st.sidebar.radio(
        "EXPLORE",
        subpages,
        key=f"submenu_{main_category}"
    )

page = selected_page
st.session_state.current_page = page
# =====================================================
# REUSABLE DISPLAY FUNCTIONS
# =====================================================

def eco_card(title, description, icon="🌱"):

    st.markdown(
        f"""
        <div class="eco-card">
            <h3>{icon} {title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric_card(label, value, icon="🌍"):

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_page_header(title, subtitle):

    st.title(title)
    st.caption(subtitle)
    st.divider()


# =====================================================
# HOME DASHBOARD
# =====================================================

def home_page():

    st.markdown(
        f"""
        <div class="eco-hero">
            <h1>Welcome to EcoLoop ♻️</h1>
            <p>{APP_TAGLINE}</p>
            <p>
                Learn. Participate. Connect.
                Build a cleaner, more sustainable community.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Your environmental action starts here")

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card("Waste contributions", "0", "♻️")

    with col2:
        metric_card("Community actions", "0", "🌱")

    with col3:
        metric_card("Points earned", "0", "⭐")

    
    st.caption(
        "These are starter dashboard values. "
        "They will be replaced with verified database records "
        "as the relevant features are connected."
    )


    st.divider()

    st.subheader("Explore EcoLoop")

    col1, col2 = st.columns(2)

    with col1:

        eco_card(
            "Record Waste",
            "Submit recyclable waste contributions "
            "and track their verification status.",
            "♻️"
        )

        eco_card(
            "Eco Quiz",
            "Test your environmental knowledge "
            "and learn through interactive quizzes.",
            "🧠"
        )

        eco_card(
            "Community Groups",
            "Connect with people working towards "
            "environmental change.",
            "👥"
        )

    with col2:

        eco_card(
            "EcoLoop Nodes",
            "Explore community collection points "
            "and their available information.",
            "📍"
        )

        eco_card(
            "Action Gallery",
            "Discover and share environmental "
            "activities and community projects.",
            "📸"
        )

        eco_card(
            "Environmental Impact",
            "Explore recorded contributions and "
            "community environmental progress.",
            "🌍"
        )

    st.divider()

    st.subheader("Our purpose")

    st.markdown(
        """
        EcoLoop is a community-centred environmental platform
        designed to make sustainable action more accessible,
        measurable and collaborative.

        It connects environmental learning, waste management,
        youth participation and community initiatives in one place.
        """
    )

    st.markdown(
        f"""
        <div class="eco-footer">
            EcoLoop Node 2.0 | {NGIH_NAME}<br>
            Climate Action & Environment
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# DISPLAY HOME PAGE
# =====================================================
if page == "Home":
    home_page()


def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

# =====================================================
# SUPABASE AUTHENTICATION
# =====================================================

def save_auth_session(auth_response):

    if not auth_response.session or not auth_response.user:
        return False

    st.session_state.access_token = (
        auth_response.session.access_token
    )

    st.session_state.refresh_token = (
        auth_response.session.refresh_token
    )

    st.session_state.user_id = auth_response.user.id
    st.session_state.logged_in = True

    return True


def restore_auth_session():

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token or not refresh_token:
        st.session_state.logged_in = False
        st.session_state.user = None
        return

    try:
        supabase.auth.set_session(
            access_token,
            refresh_token
        )

        user_id = st.session_state.get("user_id")

        if user_id:
            result = (
                supabase.table("profiles")
                .select("*")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )

            profile = result.data[0] if result.data else None

            st.session_state.user = profile
            st.session_state.logged_in = True

    except Exception:
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_id = None


def register_user(email, password, full_name):

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })

        if save_auth_session(response):
            st.success("Account created successfully!")
            st.rerun()

        else:
            st.info(
                "Registration submitted. Check your email "
                "if email confirmation is enabled, then log in."
            )

    except Exception as e:
        st.error(f"Registration failed: {e}")


def login_user(email, password):

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if save_auth_session(response):
            st.success("Login successful!")
            st.rerun()

        else:
            st.error("Login did not return an active session.")

    except Exception as e:
        st.error(f"Login failed: {e}")


def logout_user():

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_id = None

    st.rerun()


# Restore the user's session on each app run.
if supabase is not None:
    restore_auth_session()


# =====================================================
# ACCOUNT PAGE
# =====================================================

def account_page():

    show_page_header(
        "My Profile",
        "Manage your EcoLoop account and personal information."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if st.session_state.logged_in:

        profile = st.session_state.user or {}

        st.success("You are logged in.")

        st.subheader(
            profile.get("full_name", "EcoLoop Member")
        )

        st.write(
            "**Email:**",
            profile.get("email", "Not available")
        )

        st.write(
            "**Account role:**",
            profile.get("role", "user")
        )

        st.write(
            "**User ID:**",
            st.session_state.user_id
        )

        st.divider()

        if st.button("Log out", use_container_width=True):
            logout_user()

        return

    login_tab, register_tab = st.tabs([
        "Log in",
        "Create account"
    ])

    with login_tab:

        st.subheader("Welcome back")

        with st.form("ecoloop_login_form"):

            email = st.text_input("Email address")

            password = st.text_input(
                "Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Log in",
                use_container_width=True
            )

            if submitted:

                if email.strip() and password:
                    login_user(email.strip(), password)
                else:
                    st.warning("Enter your email and password.")

    with register_tab:

        st.subheader("Join EcoLoop")

        with st.form("ecoloop_register_form"):

            full_name = st.text_input("Full name")

            email = st.text_input(
                "Email address",
                key="register_email"
            )

            password = st.text_input(
                "Create password",
                type="password",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create account",
                use_container_width=True
            )

            if submitted:

                if not full_name.strip() or not email.strip():
                    st.warning("Complete all required fields.")

                elif len(password) < 8:
                    st.warning(
                        "Your password must be at least 8 characters."
                    )

                elif password != confirm_password:
                    st.error("Your passwords do not match.")

                else:
                    register_user(
                        email.strip(),
                        password,
                        full_name.strip()
                    )


# =====================================================
# ACCOUNT PAGE ROUTING
# =====================================================

if page == "My Profile":
    account_page()

# =====================================================
# RECORD WASTE — SUPABASE INTEGRATION
# =====================================================

def record_waste_page():

    show_page_header(
        "Record Waste",
        "Record recyclable materials and track your contributions."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning("Please log in before recording waste.")
        st.info("Open My Profile to access your account.")
        return

    user_id = st.session_state.user_id

    # -------------------------------------------------
    # FETCH REGISTERED COLLECTION STATIONS
    # -------------------------------------------------

    try:
        station_response = (
            supabase.table("collection_stations")
            .select("station_code, station_name")
            .execute()
        )

        stations = station_response.data or []

    except Exception as e:
        st.error("Could not retrieve collection stations.")
        st.caption(str(e))
        return

    if not stations:
        st.warning(
            "No collection stations are currently available."
        )
        return

    station_options = {
        f"{station['station_name']} ({station['station_code']})":
        station["station_code"]
        for station in stations
    }

    # -------------------------------------------------
    # WASTE SUBMISSION FORM
    # -------------------------------------------------

    st.subheader("Submit a waste contribution")

    with st.form("waste_submission_form"):

        station_label = st.selectbox(
            "Select collection station",
            list(station_options.keys())
        )

        material_type = st.selectbox(
            "Material type",
            [
                "Plastic",
                "Paper",
                "Cardboard",
                "Glass",
                "Metal",
                "Electronic waste",
                "Other recyclable material"
            ]
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=0.01,
            max_value=10000.0,
            value=1.0,
            step=0.5
        )

        submitted = st.form_submit_button(
            "Submit contribution",
            use_container_width=True
        )

        if submitted:

            try:
                contribution = {
                    "user_id": user_id,
                    "station_code": station_options[station_label],
                    "material_type": material_type,
                    "weight": float(weight)
                }

                response = (
                    supabase.table("waste_contributions")
                    .insert(contribution)
                    .execute()
                )

                if response.data:

                    st.success(
                        "Your waste contribution was submitted!"
                    )

                    st.info(
                        "Status: Pending verification. "
                        "Points will be awarded after verification."
                    )

                    st.rerun()

                else:
                    st.error(
                        "The submission could not be confirmed."
                    )

            except Exception as e:

                st.error("Waste submission failed.")
                st.caption(str(e))

    # -------------------------------------------------
    # USER CONTRIBUTION HISTORY
    # -------------------------------------------------

    st.divider()

    st.subheader("My contribution history")

    try:

        history = (
            supabase.table("waste_contributions")
            .select(
                "id, station_code, material_type, "
                "weight, submitted_at, "
                "verification_status, points"
            )
            .eq("user_id", user_id)
            .order("submitted_at", desc=True)
            .execute()
        )

        records = history.data or []

        if records:

            history_df = pd.DataFrame(records)

            history_df = history_df.rename(
                columns={
                    "station_code": "Station",
                    "material_type": "Material",
                    "weight": "Weight (kg)",
                    "submitted_at": "Date submitted",
                    "verification_status": "Status",
                    "points": "Points"
                }
            )

            display_columns = [
                "Station",
                "Material",
                "Weight (kg)",
                "Date submitted",
                "Status",
                "Points"
            ]

            st.dataframe(
                history_df[display_columns],
                use_container_width=True,
                hide_index=True
            )

            pending = sum(
                1 for record in records
                if record.get("verification_status") == "pending"
            )

            verified = sum(
                1 for record in records
                if record.get("verification_status") == "verified"
            )

            col1, col2 = st.columns(2)

            with col1:
                metric_card(
                    "Pending contributions",
                    pending,
                    "⏳"
                )

            with col2:
                metric_card(
                    "Verified contributions",
                    verified,
                    "✅"
                )

        else:
            st.info(
                "You have not submitted any waste contributions yet."
            )

    except Exception as e:

        st.error("Could not load your contribution history.")
        st.caption(str(e))


# =====================================================
# RECORD WASTE PAGE ROUTING
# =====================================================

if page == "Record Waste":
    record_waste_page()

# =====================================================
# ECOLOOP NODES — COLLECTION POINT DIRECTORY
# =====================================================

def generate_station_qr(station_code):

    station_url = (
        "https://ecoloop-node-2-g2jtmgyszhvgynvmnzuo7d."
        "streamlit.app/?station="
        + str(station_code)
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4
    )

    qr.add_data(station_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="#17452F",
        back_color="white"
    )

    buffer = io.BytesIO()
    qr_image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def eco_nodes_page():

    show_page_header(
        "EcoLoop Nodes",
        "Discover community collection points and access their information."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning(
            "Please log in to view registered collection stations."
        )
        return

    # -------------------------------------------------
    # FETCH STATIONS
    # -------------------------------------------------

    try:

        response = (
            supabase.table("collection_stations")
            .select("*")
            .order("station_code")
            .execute()
        )

        stations = response.data or []

    except Exception as e:

        st.error("Could not load EcoLoop Nodes.")
        st.caption(str(e))
        return

    if not stations:

        st.info("No collection stations have been registered.")
        return

    # -------------------------------------------------
    # STATION DIRECTORY
    # -------------------------------------------------

    st.subheader("Registered collection points")

    st.caption(
        f"{len(stations)} registered station(s) found."
    )

    for station in stations:

        station_code = station.get(
            "station_code",
            "Unknown"
        )

        station_name = station.get(
            "station_name",
            "Unnamed collection station"
        )

        with st.container(border=True):

            col1, col2 = st.columns([3, 1])

            with col1:

                st.markdown(
                    f"### 📍 {station_name}"
                )

                st.write(
                    f"**Station code:** {station_code}"
                )

                st.caption(
                    "Registered EcoLoop collection point"
                )

            with col2:

                st.markdown(
                    "<h2 style='text-align:center;'>♻️</h2>",
                    unsafe_allow_html=True
                )

            with st.expander("View station QR code"):

                qr_buffer = generate_station_qr(
                    station_code
                )

                st.image(
                    qr_buffer,
                    caption=f"EcoLoop Node: {station_code}",
                    width=220
                )

                st.download_button(
                    label="Download station QR",
                    data=qr_buffer.getvalue(),
                    file_name=f"{station_code}_QR.png",
                    mime="image/png",
                    key=f"qr_{station_code}"
                )

    # -------------------------------------------------
    # NODE INFORMATION
    # -------------------------------------------------

    st.divider()

    st.subheader("Understanding EcoLoop Nodes")

    eco_card(
        "Community collection points",
        "Designated locations where community members "
        "can submit recyclable materials.",
        "📍"
    )

    eco_card(
        "Digital identification",
        "Each registered station has a unique station "
        "code and a QR code for identification.",
        "🔳"
    )

    eco_card(
        "Future smart monitoring",
        "Future development can introduce connected "
        "sensors to monitor collection capacity and "
        "station activity.",
        "📡"
    )

    st.info(
        "Current station information comes from the "
        "Supabase collection_stations table. "
        "Live fill-level monitoring is not yet connected."
    )


# =====================================================
# ECOLOOP NODES PAGE ROUTING
# =====================================================

if page == "EcoLoop Nodes":
    eco_nodes_page()

# =====================================================
# LEADERBOARD
# =====================================================

def leaderboard_page():

    show_page_header(
        "Leaderboard",
        "Recognising verified environmental contributions."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning("Please log in to access the leaderboard.")
        return

    st.subheader("Your contribution standing")

    st.info(
        "Your personal verified contribution points are "
        "available below. A public community leaderboard "
        "will require a secure database view that only "
        "exposes approved leaderboard information."
    )

    try:

        response = (
            supabase.table("waste_contributions")
            .select("weight, points, verification_status")
            .eq("user_id", st.session_state.user_id)
            .eq("verification_status", "verified")
            .execute()
        )

        records = response.data or []

        total_weight = sum(
            float(record.get("weight") or 0)
            for record in records
        )

        total_points = sum(
            int(record.get("points") or 0)
            for record in records
        )

        col1, col2 = st.columns(2)

        with col1:
            metric_card(
                "Verified waste (kg)",
                f"{total_weight:.2f}",
                "♻️"
            )

        with col2:
            metric_card(
                "Verified points",
                total_points,
                "⭐"
            )

        st.divider()

        st.subheader("Your achievements")

        if total_points >= 500:
            st.success("🌳 Eco Champion — 500+ points")

        elif total_points >= 200:
            st.success("🌱 Eco Contributor — 200+ points")

        elif total_points >= 50:
            st.success("♻️ Eco Starter — 50+ points")

        else:
            st.info(
                "Keep participating to unlock your first "
                "EcoLoop achievement."
            )

    except Exception as e:

        st.error("Could not retrieve your verified points.")
        st.caption(str(e))


# =====================================================
# ENVIRONMENTAL IMPACT
# =====================================================

def environmental_impact_page():

    show_page_header(
        "Environmental Impact",
        "Understand the impact of your verified contributions."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning(
            "Please log in to view your environmental impact."
        )
        return

    try:

        response = (
            supabase.table("waste_contributions")
            .select(
                "material_type, weight, points, "
                "verification_status, submitted_at"
            )
            .eq("user_id", st.session_state.user_id)
            .execute()
        )

        records = response.data or []

        verified_records = [
            record for record in records
            if record.get("verification_status") == "verified"
        ]

        pending_records = [
            record for record in records
            if record.get("verification_status") == "pending"
        ]

        rejected_records = [
            record for record in records
            if record.get("verification_status") == "rejected"
        ]

        total_weight = sum(
            float(record.get("weight") or 0)
            for record in verified_records
        )

        total_points = sum(
            int(record.get("points") or 0)
            for record in verified_records
        )

        # ---------------------------------------------
        # IMPACT METRICS
        # ---------------------------------------------

        col1, col2 = st.columns(2)

        with col1:
            metric_card(
                "Verified recyclable waste",
                f"{total_weight:.2f} kg",
                "♻️"
            )

        with col2:
            metric_card(
                "Points earned",
                total_points,
                "⭐"
            )

        col3, col4 = st.columns(2)

        with col3:
            metric_card(
                "Pending submissions",
                len(pending_records),
                "⏳"
            )

        with col4:
            metric_card(
                "Verified submissions",
                len(verified_records),
                "✅"
            )

        st.divider()

        # ---------------------------------------------
        # MATERIAL BREAKDOWN
        # ---------------------------------------------

        st.subheader("Verified material breakdown")

        if verified_records:

            material_data = {}

            for record in verified_records:

                material = record.get(
                    "material_type",
                    "Other"
                )

                weight = float(
                    record.get("weight") or 0
                )

                material_data[material] = (
                    material_data.get(material, 0) + weight
                )

            material_df = pd.DataFrame(
                [
                    {
                        "Material": material,
                        "Weight (kg)": round(weight, 2)
                    }
                    for material, weight in material_data.items()
                ]
            )

            st.bar_chart(
                material_df.set_index("Material")
            )

            st.dataframe(
                material_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Your verified material breakdown will "
                "appear after your first approved contribution."
            )

        st.divider()

        st.subheader("Your contribution journey")

        st.write(
            f"You have submitted **{len(records)}** "
            "waste contribution(s) in total."
        )

        st.write(
            f"**Verified:** {len(verified_records)}"
        )

        st.write(
            f"**Pending:** {len(pending_records)}"
        )

        st.write(
            f"**Rejected:** {len(rejected_records)}"
        )

        st.caption(
            "Impact figures are based on verified records "
            "in your account. They are not estimates of "
            "carbon savings or total community impact."
        )

    except Exception as e:

        st.error("Could not calculate environmental impact.")
        st.caption(str(e))


# =====================================================
# PAGE ROUTING
# =====================================================

if page == "Leaderboard":
    leaderboard_page()

if page == "Environmental Impact":
    environmental_impact_page()

# =====================================================
# EXPLORE & LEARN
# =====================================================

def explore_learn_page():

    show_page_header(
        "Explore & Learn",
        "Build your environmental knowledge and discover practical ways to make a difference."
    )

    learning_topics = [
        {
            "title": "Waste Management",
            "icon": "♻️",
            "description": (
                "Understand waste separation, recycling, "
                "reuse and responsible disposal."
            ),
            "content": (
                "Waste management involves collecting, "
                "sorting, treating and disposing of waste "
                "responsibly. Separating recyclable materials "
                "helps reduce pressure on landfills and "
                "supports a circular economy."
            )
        },
        {
            "title": "Climate Change",
            "icon": "🌍",
            "description": (
                "Learn about climate change, its causes "
                "and its effects on communities."
            ),
            "content": (
                "Climate change refers to long-term changes "
                "in temperatures and weather patterns. "
                "Human activities, particularly the burning "
                "of fossil fuels, are the main driver of "
                "recent global warming."
            )
        },
        {
            "title": "Biodiversity",
            "icon": "🌳",
            "description": (
                "Discover why plants, animals and ecosystems "
                "matter."
            ),
            "content": (
                "Biodiversity is the variety of life on Earth. "
                "Healthy ecosystems support food production, "
                "clean water, pollination and climate resilience."
            )
        },
        {
            "title": "Sustainable Communities",
            "icon": "🏘️",
            "description": (
                "Explore how communities can create "
                "healthier and more sustainable environments."
            ),
            "content": (
                "Sustainable communities use resources "
                "responsibly, encourage public participation "
                "and develop solutions that consider both "
                "present and future generations."
            )
        },
        {
            "title": "Water Conservation",
            "icon": "💧",
            "description": (
                "Understand the importance of protecting "
                "and conserving water."
            ),
            "content": (
                "Water conservation means using water "
                "efficiently and protecting water sources. "
                "Reducing unnecessary water use helps "
                "communities become more resilient to shortages."
            )
        },
        {
            "title": "Renewable Energy",
            "icon": "☀️",
            "description": (
                "Learn about solar, wind and other "
                "renewable energy sources."
            ),
            "content": (
                "Renewable energy comes from sources that "
                "are naturally replenished, such as sunlight, "
                "wind and flowing water. These sources can "
                "help reduce dependence on fossil fuels."
            )
        }
    ]

    st.subheader("Learning library")

    for topic in learning_topics:

        with st.expander(
            f"{topic['icon']} {topic['title']}"
        ):

            st.write(topic["description"])
            st.write(topic["content"])

    st.divider()

    st.subheader("Put knowledge into action")

    st.markdown(
        """
        Learning becomes meaningful when it leads to action.

        - Separate recyclable materials at home.
        - Participate in local environmental campaigns.
        - Share reliable environmental information.
        - Encourage responsible resource use.
        - Support community-led environmental initiatives.
        """
    )


# =====================================================
# ECO QUIZ — HELPER FUNCTIONS
# =====================================================

def get_quiz_value(row, possible_names, default=None):

    for name in possible_names:

        if row.get(name) is not None:
            return row.get(name)

    return default


def get_question_options(question):

    # Support either individual option columns
    # or an options array stored in the question row.

    options = question.get("options")

    if isinstance(options, dict):
        return {
            str(key): str(value)
            for key, value in options.items()
        }

    if isinstance(options, list):
        return {
            str(index + 1): str(value)
            for index, value in enumerate(options)
        }

    possible_columns = [
        ("A", ["option_a", "option1", "choice_a"]),
        ("B", ["option_b", "option2", "choice_b"]),
        ("C", ["option_c", "option3", "choice_c"]),
        ("D", ["option_d", "option4", "choice_d"])
    ]

    result = {}

    for label, column_names in possible_columns:

        value = get_quiz_value(
            question,
            column_names
        )

        if value is not None:
            result[label] = str(value)

    return result


# =====================================================
# ECO QUIZ
# =====================================================

def eco_quiz_page():

    show_page_header(
        "Eco Quiz",
        "Test your environmental knowledge and earn points through learning."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning("Please log in to participate in quizzes.")
        return

    user_id = st.session_state.user_id

    # -------------------------------------------------
    # LOAD AVAILABLE QUIZZES
    # -------------------------------------------------

    try:

        quiz_response = (
            supabase.table("quizzes")
            .select("*")
            .execute()
        )

        all_quizzes = quiz_response.data or []

        quizzes = [
            quiz for quiz in all_quizzes
            if quiz.get("is_active", quiz.get("active", True))
        ]

    except Exception as e:

        st.error("Could not load available quizzes.")
        st.caption(str(e))
        return

    if not quizzes:

        st.info("There are no active quizzes available yet.")
        return

    quiz_labels = {}

    for quiz in quizzes:

        quiz_id = quiz.get("id")

        title = get_quiz_value(
            quiz,
            ["title", "quiz_title", "name"],
            "Environmental Quiz"
        )

        description = get_quiz_value(
            quiz,
            ["description", "quiz_description"],
            ""
        )

        quiz_labels[f"{title} — {quiz_id}"] = quiz

    selected_label = st.selectbox(
        "Choose a quiz",
        list(quiz_labels.keys())
    )

    selected_quiz = quiz_labels[selected_label]
    quiz_id = selected_quiz.get("id")

    st.write(
        get_quiz_value(
            selected_quiz,
            ["description", "quiz_description"],
            "Test your environmental knowledge."
        )
    )

    # -------------------------------------------------
    # QUIZ SESSION STATE
    # -------------------------------------------------

    if "active_quiz_attempt" not in st.session_state:
        st.session_state.active_quiz_attempt = None

    if "active_quiz_questions" not in st.session_state:
        st.session_state.active_quiz_questions = []

    if "active_quiz_index" not in st.session_state:
        st.session_state.active_quiz_index = 0

    if "active_quiz_results" not in st.session_state:
        st.session_state.active_quiz_results = []

    if "active_quiz_id" not in st.session_state:
        st.session_state.active_quiz_id = None

    attempt = st.session_state.active_quiz_attempt

    # -------------------------------------------------
    # START QUIZ
    # -------------------------------------------------

    if attempt is None:

        if st.button(
            "Start quiz",
            use_container_width=True
        ):

            try:

                question_response = (
                    supabase.table("quiz_questions")
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

                attempt_response = (
                    supabase.table("quiz_attempts")
                    .insert({
                        "user_id": user_id,
                        "quiz_id": quiz_id
                    })
                    .execute()
                )

                if not attempt_response.data:
                    st.error("Could not start your quiz attempt.")
                    return

                attempt_id = attempt_response.data[0]["id"]

                st.session_state.active_quiz_attempt = attempt_id
                st.session_state.active_quiz_questions = questions
                st.session_state.active_quiz_index = 0
                st.session_state.active_quiz_results = []
                st.session_state.active_quiz_id = quiz_id

                st.rerun()

            except Exception as e:

                st.error("Could not start the quiz.")
                st.caption(str(e))

        return

    # -------------------------------------------------
    # ENSURE THE ACTIVE QUIZ MATCHES THE SELECTED QUIZ
    # -------------------------------------------------

    if st.session_state.active_quiz_id != quiz_id:

        st.warning(
            "You have an unfinished quiz. Finish it before "
            "starting another quiz."
        )
        return

    questions = st.session_state.active_quiz_questions
    question_index = st.session_state.active_quiz_index

    # -------------------------------------------------
    # DISPLAY QUESTIONS
    # -------------------------------------------------

    if question_index < len(questions):

        question = questions[question_index]

        question_text = get_question_value = get_quiz_value(
            question,
            ["question_text", "question", "text"],
            "Question"
        )

        options = get_question_options(question)

        st.progress(
            (question_index + 1) / len(questions)
        )

        st.caption(
            f"Question {question_index + 1} of {len(questions)}"
        )

        st.subheader(str(question_text))

        if not options:

            st.error(
                "This question has no recognised answer options. "
                "Please check its database structure."
            )
            return

        option_labels = [
            f"{key}. {value}"
            for key, value in options.items()
        ]

        selected_option = st.radio(
            "Choose your answer",
            option_labels,
            key=f"quiz_question_{question['id']}"
        )

        if st.button(
            "Submit answer",
            use_container_width=True,
            key=f"submit_quiz_{question['id']}"
        ):

            selected_key = selected_option.split(".", 1)[0]

            try:

                result_response = supabase.rpc(
                    "submit_quiz_answer",
                    {
                        "p_attempt_id": st.session_state.active_quiz_attempt,
                        "p_question_id": question["id"],
                        "p_selected_option": selected_key
                    }
                ).execute()

                result = result_response.data

                if isinstance(result, list) and result:
                    result = result[0]

                if not isinstance(result, dict):
                    st.error("The quiz returned an unexpected response.")
                    return

                st.session_state.active_quiz_results.append(result)

                st.session_state.active_quiz_index += 1

                st.rerun()

            except Exception as e:

                st.error("Your answer could not be submitted.")
                st.caption(str(e))

    # -------------------------------------------------
    # FINISH QUIZ
    # -------------------------------------------------

    else:

        st.subheader("Quiz completed!")

        try:

            finish_response = supabase.rpc(
                "finish_quiz_attempt",
                {
                    "p_attempt_id": st.session_state.active_quiz_attempt
                }
            ).execute()

            st.success(
                "Your quiz has been completed and your result "
                "has been recorded."
            )

            if finish_response.data is not None:
                st.write(finish_response.data)

            st.caption(
                "Points are awarded by the database according "
                "to the configured scoring rules."
            )

            if st.button(
                "Return to quiz selection",
                use_container_width=True
            ):

                st.session_state.active_quiz_attempt = None
                st.session_state.active_quiz_questions = []
                st.session_state.active_quiz_index = 0
                st.session_state.active_quiz_results = []
                st.session_state.active_quiz_id = None

                st.rerun()

        except Exception as e:

            st.error("Could not finish the quiz.")
            st.caption(str(e))


# =====================================================
# PAGE ROUTING
# =====================================================

if page == "Explore & Learn":
    explore_learn_page()

if page == "Eco Quiz":
    eco_quiz_page()

# =====================================================
# ACTION GALLERY
# =====================================================

def action_gallery_page():

    show_page_header(
        "Action Gallery",
        "Showcase environmental initiatives and community action."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning("Please log in to participate in the Action Gallery.")
        return

    user_id = st.session_state.user_id

    # -------------------------------------------------
    # LOAD ENVIRONMENTAL ACTIONS
    # -------------------------------------------------

    st.subheader("Environmental activities")

    try:

        actions_response = (
            supabase.table("environmental_actions")
            .select("*")
            .execute()
        )

        actions = actions_response.data or []

    except Exception as e:

        st.error("Could not load environmental activities.")
        st.caption(str(e))
        actions = []

    if actions:

        for action in actions:

            title = get_quiz_value(
                action,
                ["title", "action_name", "name"],
                "Environmental activity"
            )

            description = get_quiz_value(
                action,
                ["description", "details"],
                "Community environmental initiative."
            )

            category = get_quiz_value(
                action,
                ["category", "action_type"],
                "Community action"
            )

            with st.container(border=True):

                st.markdown(f"### 🌱 {title}")

                st.caption(f"Category: {category}")

                st.write(description)

    else:

        st.info(
            "No environmental activities are currently available."
        )

    st.divider()

    # -------------------------------------------------
    # SUBMIT AN ENVIRONMENTAL ACTION
    # -------------------------------------------------

    st.subheader("Share your environmental action")

    with st.form("environmental_action_submission"):

        action_title = st.text_input(
            "Activity title"
        )

        action_description = st.text_area(
            "Describe the activity",
            placeholder=(
                "What did you do? Where did it happen? "
                "What was the community benefit?"
            )
        )

        action_category = st.selectbox(
            "Activity category",
            [
                "Community clean-up",
                "Tree planting",
                "Waste recycling",
                "Environmental education",
                "Water conservation",
                "Biodiversity protection",
                "Other"
            ]
        )

        submitted = st.form_submit_button(
            "Submit activity",
            use_container_width=True
        )

        if submitted:

            if not action_title.strip():
                st.warning("Enter an activity title.")

            elif not action_description.strip():
                st.warning("Describe your environmental activity.")

            else:

                st.info(
                    "Your activity is ready for submission. "
                    "The database column structure must be confirmed "
                    "before this form can write a record."
                )

    st.divider()

    # -------------------------------------------------
    # USER ACTION HISTORY
    # -------------------------------------------------

    st.subheader("My environmental activities")

    try:

        my_actions = (
            supabase.table("user_actions")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        records = my_actions.data or []

        if records:

            st.dataframe(
                pd.DataFrame(records),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Your submitted environmental actions "
                "will appear here."
            )

    except Exception as e:

        st.warning("Could not load your activity history.")
        st.caption(str(e))


# =====================================================
# PAGE ROUTING
# =====================================================

if page == "Action Gallery":
    action_gallery_page()

# =====================================================
# COMMUNITY GROUPS
# =====================================================

def community_groups_page():

    show_page_header(
        "Community Groups",
        "Connect with people creating environmental change."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning("Please log in to access community groups.")
        return

    user_id = st.session_state.user_id

    # -------------------------------------------------
    # LOAD COMMUNITY GROUPS
    # -------------------------------------------------

    st.subheader("Discover groups")

    try:

        groups_response = (
            supabase.table("community_groups")
            .select("*")
            .execute()
        )

        groups = groups_response.data or []

    except Exception as e:

        st.error("Could not load community groups.")
        st.caption(str(e))
        return

    if not groups:

        st.info(
            "No community groups are currently available."
        )

    else:

        st.caption(f"{len(groups)} group(s) available.")

        for group in groups:

            group_id = group.get("id")

            group_name = get_quiz_value(
                group,
                ["group_name", "name", "title"],
                "Community Group"
            )

            description = get_quiz_value(
                group,
                ["description", "group_description"],
                "A community environmental initiative."
            )

            category = get_quiz_value(
                group,
                ["category", "focus_area"],
                "Environmental action"
            )

            with st.container(border=True):

                st.markdown(f"### 👥 {group_name}")

                st.write(description)

                st.caption(f"Focus: {category}")

                st.caption(f"Group reference: {group_id}")

    st.divider()

    # -------------------------------------------------
    # USER MEMBERSHIPS
    # -------------------------------------------------

    st.subheader("My group memberships")

    try:

        membership_response = (
            supabase.table("group_memberships")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        memberships = membership_response.data or []

        if memberships:

            membership_df = pd.DataFrame(memberships)

            st.dataframe(
                membership_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "You have not joined or requested to join "
                "a community group yet."
            )

    except Exception as e:

        st.warning("Could not retrieve your memberships.")
        st.caption(str(e))

    st.divider()

    # -------------------------------------------------
    # GROUP PARTICIPATION INFORMATION
    # -------------------------------------------------

    st.subheader("How group participation works")

    eco_card(
        "Discover",
        "Explore groups and find initiatives that match "
        "your environmental interests.",
        "🔎"
    )

    eco_card(
        "Request membership",
        "Members can request to join groups. "
        "Requests are subject to group approval.",
        "📝"
    )

    eco_card(
        "Lead initiatives",
        "Approved group leaders can coordinate activities "
        "and organise community participation.",
        "🌱"
    )

    st.info(
        "Group creation and membership request submission "
        "will be activated after confirming the exact "
        "database column names and policies."
    )


# =====================================================
# PAGE ROUTING
# =====================================================

if page == "Community Groups":
    community_groups_page()

# =====================================================
# COLLECTION MANAGEMENT
# =====================================================

def collection_management_page():

    show_page_header(
        "Collection Management",
        "View collection stations and manage collection records."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not st.session_state.logged_in:
        st.warning("Please log in to access collection management.")
        return

    # -------------------------------------------------
    # COLLECTION STATIONS
    # -------------------------------------------------

    st.subheader("Collection stations")

    try:

        station_response = (
            supabase.table("collection_stations")
            .select("*")
            .execute()
        )

        stations = station_response.data or []

        if stations:

            station_df = pd.DataFrame(stations)

            st.dataframe(
                station_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No registered stations found.")

    except Exception as e:

        st.error("Could not retrieve collection stations.")
        st.caption(str(e))

    st.divider()

    # -------------------------------------------------
    # COLLECTION RECORDS
    # -------------------------------------------------

    st.subheader("Collection records")

    try:

        records_response = (
            supabase.table("collection_records")
            .select("*")
            .execute()
        )

        records = records_response.data or []

        if records:

            records_df = pd.DataFrame(records)

            st.dataframe(
                records_df,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "Records displayed are subject to the "
                "access permissions configured in Supabase."
            )

        else:

            st.info(
                "No collection records are available "
                "for your account."
            )

    except Exception as e:

        st.warning("Could not retrieve collection records.")
        st.caption(str(e))

    st.divider()

    # -------------------------------------------------
    # COLLECTION RECORD SUBMISSION
    # -------------------------------------------------

    st.subheader("Record a collection activity")

    st.info(
        "Collection record submission will be enabled "
        "after confirming the exact collection_records "
        "table columns and authorised submission roles."
    )

    eco_card(
        "Station monitoring",
        "Keep track of registered collection locations "
        "and their recorded activity.",
        "📍"
    )

    eco_card(
        "Collection records",
        "Maintain a record of collection activities "
        "for accountability and reporting.",
        "📋"
    )

    eco_card(
        "Community coordination",
        "Support coordination between collection points "
        "and participating community members.",
        "🤝"
    )


# =====================================================
# PAGE ROUTING
# =====================================================

if page == "Collection Management":
    collection_management_page()

# =====================================================
# ADMIN ACCESS CONTROL
# =====================================================

def is_admin():

    if not st.session_state.get("logged_in"):
        return False

    profile = st.session_state.get("user") or {}

    return profile.get("role") == "admin"


def admin_access_required():

    if not st.session_state.logged_in:
        st.warning("Please log in first.")
        return False

    if not is_admin():
        st.error(
            "Access restricted. Administrator permissions "
            "are required."
        )
        return False

    return True


# =====================================================
# VERIFY CONTRIBUTIONS
# =====================================================

def verify_contributions_page():

    show_page_header(
        "Verify Contributions",
        "Review submitted waste contributions and their verification status."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not admin_access_required():
        return

    # -------------------------------------------------
    # PENDING CONTRIBUTIONS
    # -------------------------------------------------

    st.subheader("Pending contributions")

    try:

        response = (
            supabase.table("waste_contributions")
            .select(
                "id, user_id, station_code, material_type, "
                "weight, submitted_at, verification_status"
            )
            .eq("verification_status", "pending")
            .order("submitted_at", desc=True)
            .execute()
        )

        pending_records = response.data or []

        if pending_records:

            st.caption(
                f"{len(pending_records)} contribution(s) "
                "awaiting review."
            )

            pending_df = pd.DataFrame(pending_records)

            st.dataframe(
                pending_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success("There are no pending contributions.")

    except Exception as e:

        st.error("Could not load pending contributions.")
        st.caption(str(e))

    st.divider()

    # -------------------------------------------------
    # VERIFICATION WORKFLOW
    # -------------------------------------------------

    st.subheader("Verification workflow")

    st.info(
        "The review interface is available, but approval "
        "and rejection actions are not enabled yet. "
        "We must first confirm the database scoring rules "
        "and point transaction workflow."
    )

    eco_card(
        "Review",
        "Examine the contribution details and supporting "
        "information before making a decision.",
        "🔎"
    )

    eco_card(
        "Verify",
        "Confirm that the contribution meets the platform's "
        "verification requirements.",
        "✅"
    )

    eco_card(
        "Award points",
        "Award points through the authorised scoring workflow "
        "after a successful verification.",
        "⭐"
    )


# =====================================================
# ADMIN STUDIO
# =====================================================

def admin_studio_page():

    show_page_header(
        "Admin Studio",
        "Administrator workspace for EcoLoop platform oversight."
    )

    if supabase is None:
        st.error("Supabase is not connected.")
        return

    if not admin_access_required():
        return

    st.success("Administrator access confirmed.")

    # -------------------------------------------------
    # PLATFORM OVERVIEW
    # -------------------------------------------------

    st.subheader("Platform overview")

    try:

        contributions = (
            supabase.table("waste_contributions")
            .select("id, verification_status")
            .execute()
        )

        records = contributions.data or []

        total = len(records)

        pending = sum(
            1 for item in records
            if item.get("verification_status") == "pending"
        )

        verified = sum(
            1 for item in records
            if item.get("verification_status") == "verified"
        )

        rejected = sum(
            1 for item in records
            if item.get("verification_status") == "rejected"
        )

        col1, col2 = st.columns(2)

        with col1:
            metric_card("Total submissions", total, "📋")

        with col2:
            metric_card("Pending review", pending, "⏳")

        col3, col4 = st.columns(2)

        with col3:
            metric_card("Verified", verified, "✅")

        with col4:
            metric_card("Rejected", rejected, "❌")

    except Exception as e:

        st.warning("Could not load platform statistics.")
        st.caption(str(e))

    st.divider()

    # -------------------------------------------------
    # ADMIN MODULES
    # -------------------------------------------------

    st.subheader("Administration modules")

    eco_card(
        "Contribution verification",
        "Review and verify environmental contributions.",
        "♻️"
    )

    eco_card(
        "Community oversight",
        "Support responsible management of community groups.",
        "👥"
    )

    eco_card(
        "Quiz management",
        "Manage environmental learning and quiz content.",
        "🧠"
    )

    eco_card(
        "Environmental reporting",
        "Monitor recorded activities and platform progress.",
        "🌍"
    )

    st.warning(
        "Administrator-only access is enforced in the app "
        "interface. Supabase Row Level Security must also "
        "enforce the same permissions on every database action."
    )


# =====================================================
# PAGE ROUTING
# =====================================================

if page == "Verify Contributions":
    verify_contributions_page()

if page == "Admin Studio":
    admin_studio_page()

# =====================================================
# ABOUT NGIH
# =====================================================

def about_ngih_page():

    show_page_header(
        "About NGIH",
        "The organisation behind EcoLoop Node 2.0."
    )

    st.markdown(
        """
        <div class="eco-hero">
            <h1>Next Gen Impact Hub</h1>
            <p>
                Creating a generation of youth who lead and
                influence across governance, economy,
                environment and technology.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Who we are")

    st.write(
        """
        Next Gen Impact Hub (NGIH) is a youth-centred
        initiative focused on developing young people
        as active participants in shaping their communities
        and contributing to sustainable development.
        """
    )

    st.write(
        """
        NGIH seeks to create opportunities for young people
        to learn, innovate, participate and lead across
        different areas of society.
        """
    )

    st.divider()

    st.subheader("Our four pillars")

    col1, col2 = st.columns(2)

    with col1:

        eco_card(
            "Governance & Civic Education",
            "Promoting informed citizenship, accountability "
            "and meaningful youth participation.",
            "🏛️"
        )

        eco_card(
            "Climate Action & Environment",
            "Encouraging environmental responsibility, "
            "community resilience and sustainable practices.",
            "🌍"
        )

    with col2:

        eco_card(
            "Business & Entrepreneurship",
            "Supporting innovation, enterprise development "
            "and youth economic participation.",
            "💼"
        )

        eco_card(
            "Technology, Innovation, Media & Arts",
            "Using creativity, digital tools and innovation "
            "to address community challenges.",
            "💡"
        )

    st.divider()

    st.subheader("About EcoLoop")

    st.write(
        """
        EcoLoop Node 2.0 is an environmental technology
        initiative under NGIH's Climate Action & Environment
        pillar.

        It aims to connect environmental education,
        responsible waste management, community participation
        and digital innovation through one accessible platform.
        """
    )

    st.divider()

    st.subheader("Our approach")

    st.markdown(
        """
        - **Learn:** Make environmental knowledge accessible.
        - **Participate:** Encourage practical community action.
        - **Connect:** Bring people and initiatives together.
        - **Measure:** Track verified contributions and progress.
        - **Innovate:** Explore technology-driven environmental solutions.
        """
    )

    st.markdown(
        f"""
        <div class="eco-footer">
            <strong>{APP_NAME}</strong><br>
            An initiative of {NGIH_NAME}<br>
            Climate Action & Environment
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# FINAL PAGE ROUTING
# =====================================================

if page == "About NGIH":
    about_ngih_page()


# =====================================================
# APPLICATION FOOTER
# =====================================================

if page != "Home" and page != "About NGIH":

    st.markdown(
        f"""
        <div class="eco-footer">
            {APP_NAME} | {NGIH_NAME}<br>
            Building sustainable communities through
            youth participation and innovation.
        </div>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# ECOLOOP NODE 2.0 — SYSTEM DIAGNOSTICS
# =====================================================

def system_diagnostics_page():

    show_page_header(
        "System Diagnostics",
        "Check the main application connections."
    )

    st.subheader("Application status")

    # Supabase connection
    if supabase is not None:
        st.success("Supabase client initialised.")
    else:
        st.error("Supabase connection is unavailable.")

    # Authentication status
    if st.session_state.get("logged_in", False):

        st.success("A user is signed in.")

        user = st.session_state.get("user")

        if user:
            st.write("User ID:", user.id)

        profile = st.session_state.get("profile")

        if profile:
            st.write(
                "Profile:",
                profile.get("full_name", "Name not provided")
            )
            st.write(
                "Account role:",
                profile.get("role", "Not assigned")
            )
        else:
            st.warning("No profile information was loaded.")

    else:
        st.info("No user is currently signed in.")

    st.divider()

    st.subheader("Database connection test")

    if st.button("Test database connection"):

        if supabase is None:
            st.error("Supabase client is unavailable.")

        else:
            try:
                result = (
                    supabase
                    .table("collection_stations")
                    .select("station_code")
                    .limit(1)
                    .execute()
                )

                st.success("Database query completed.")

                if result.data:
                    st.write("A collection station was found.")
                else:
                    st.warning(
                        "The query worked, but no station was returned."
                    )

            except Exception as e:
                st.error("Database query failed.")
                st.code(str(e))


# =====================================================
# DIAGNOSTICS ROUTE
# =====================================================

if page == "System Diagnostics":
    system_diagnostics_page()
