
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
    page_title="EcoLoop Node",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# ECOLOOP BRANDING
# =====================================================

APP_NAME = "EcoLoop Node"

APP_TAGLINE = (
    "Turning everyday environmental action "
    "into measurable community impact."
)

NGIH_NAME = "Next Gen Impact Hub"


# =====================================================
# SUPABASE CONNECTION
# =====================================================

def get_supabase_client():

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


try:

    supabase = get_supabase_client()

    st.sidebar.success(
        "Supabase client initialised"
    )

except Exception as e:

    supabase = None

    st.sidebar.error(
        f"Supabase connection error: {type(e).__name__}"
    )


# =====================================================
# INITIAL SESSION STATE
# =====================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "user": None,
    "user_id": None,
    "access_token": None,
    "refresh_token": None,
    "current_page": "Home",
    "main_category": "Home",
    "active_quiz_attempt": None,
    "active_quiz_questions": [],
    "active_quiz_index": 0,
    "active_quiz_results": [],
    "active_quiz_id": None
}

for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:
        st.session_state[key] = value
# =====================================================
# ECOLOOP VISUAL DESIGN
# =====================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    font-family: 'DM Sans', sans-serif;
}

/* Main content spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Headings */
h1, h2, h3 {
    font-weight: 700;
}

/* Buttons */
.stButton > button {
    border-radius: 12px;
    border: none;
    background: #176B45;
    color: white;
    font-weight: 600;
    padding: 0.55rem 1rem;
    transition: 0.2s ease;
}

.stButton > button:hover {
    background: #218653;
    color: white;
    border: none;
}

/* Form inputs */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] {
    border-radius: 10px;
}

/* Cards */
.eco-card {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128, 128, 128, 0.18);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128, 128, 128, 0.18);
    border-radius: 14px;
    padding: 16px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128, 128, 128, 0.18);
}

/* Sidebar navigation buttons */
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    justify-content: flex-start;
    border-radius: 10px;
    margin-bottom: 4px;
}

/* EcoLoop accent colours */
.eco-green {
    color: #176B45;
}

.eco-lime {
    color: #A8D94F;
}

.eco-teal {
    color: #159B91;
}

.eco-amber {
    color: #E6A23C;
}

/* App branding */
.eco-brand {
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.7px;
}

.eco-tagline {
    font-size: 0.9rem;
    opacity: 0.75;
}

/* Images */
img {
    border-radius: 12px;
}

/* Mobile layout */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .eco-brand {
        font-size: 1.5rem;
    }
}

</style>
""")

# =====================================================
# SESSION MANAGEMENT
# =====================================================

def set_user_session(auth_response):

    auth_user = auth_response.user
    auth_session = auth_response.session

    st.session_state.logged_in = True
    st.session_state.user_id = str(auth_user.id)
    st.session_state.access_token = auth_session.access_token
    st.session_state.refresh_token = auth_session.refresh_token

    load_user_profile()


def load_user_profile():

    if not supabase or not st.session_state.user_id:
        st.session_state.user = None
        return

    try:

        response = (
            supabase.table("profiles")
            .select("*")
            .eq("id", st.session_state.user_id)
            .single()
            .execute()
        )

        st.session_state.user = response.data

    except Exception:
        st.session_state.user = None


def restore_auth_session():

    if not supabase:
        return

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token or not refresh_token:
        return

    try:

        supabase.auth.set_session(
            access_token,
            refresh_token
        )

        auth_user = supabase.auth.get_user()

        if auth_user and auth_user.user:

            st.session_state.logged_in = True
            st.session_state.user_id = str(auth_user.user.id)

            load_user_profile()

        else:
            clear_user_session()

    except Exception:
        clear_user_session()


def clear_user_session():

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None


def is_logged_in():

    return (
        st.session_state.get("logged_in", False)
        and st.session_state.get("user_id") is not None
    )


def is_admin():

    profile = st.session_state.get("user")

    if not profile:
        return False

    return profile.get("role") == "admin"


# Restore an existing login when the app reruns
if supabase and not st.session_state.logged_in:

    restore_auth_session()

# =====================================================
# ECOLOOP MAIN NAVIGATION
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
        "About NGIH"
    ]
}


def render_navigation():

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        "## ♻️ EcoLoop Node"
    )

    st.sidebar.caption(
        "Turning everyday environmental action into measurable community impact."
    )

    st.sidebar.markdown("---")

    # Main categories
    for category in NAVIGATION:

        if st.sidebar.button(
            category,
            key=f"nav_category_{category}",
            use_container_width=True
        ):

            st.session_state.main_category = category
            st.session_state.current_page = NAVIGATION[category][0]

            st.rerun()

    st.sidebar.markdown("---")

    # Pages within the selected category
    selected_category = st.session_state.get(
        "main_category",
        "Home"
    )

    st.sidebar.markdown(
        f"### {selected_category}"
    )

    for page in NAVIGATION[selected_category]:

        if st.sidebar.button(
            page,
            key=f"nav_page_{page}",
            use_container_width=True
        ):

            st.session_state.current_page = page
            st.rerun()

    # Administration is only visible to admins
    if is_admin():

        st.sidebar.markdown("---")
        st.sidebar.markdown("### Administration")

        admin_pages = [
            "Verify Contributions",
            "Admin Studio",
            "System Diagnostics"
        ]

        for page in admin_pages:

            if st.sidebar.button(
                page,
                key=f"nav_admin_{page}",
                use_container_width=True
            ):

                st.session_state.main_category = "Administration"
                st.session_state.current_page = page
                st.rerun()

    st.sidebar.markdown("---")

    if is_logged_in():

        profile = st.session_state.get("user") or {}

        st.sidebar.caption(
            f"Logged in as {profile.get('full_name', 'User')}"
        )

    else:

        st.sidebar.caption("You are browsing as a guest.")

selected_category = st.session_state.get(
    "main_category",
    "Home"
)

if selected_category not in NAVIGATION:
    selected_category = "Home"

# =====================================================
# REUSABLE DISPLAY COMPONENTS
# =====================================================

def section_heading(title, description=None):

    st.markdown(f"## {title}")

    if description:
        st.caption(description)


def eco_card(title, description, icon="♻️"):

    st.markdown(
        f"""
        <div class="eco-card">
            <h3>{icon} {title}</h3>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_empty_state(message):

    st.info(message)


def get_table_count(table_name, user_id=None):

    if not supabase:
        return 0

    try:

        query = supabase.table(table_name).select(
            "id",
            count="exact"
        )

        if user_id:
            query = query.eq("user_id", user_id)

        response = query.execute()

        return response.count or 0

    except Exception:
        return 0


# =====================================================
# HOME DASHBOARD
# =====================================================

def home_page():

    st.markdown(
        f"""
        <div class="eco-brand">{APP_NAME} ♻️</div>
        <p class="eco-tagline">{APP_TAGLINE}</p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    if is_logged_in():

        profile = st.session_state.get("user") or {}

        full_name = profile.get("full_name", "EcoLoop Member")

        st.subheader(f"Welcome back, {full_name}!")

        st.write(
            "Your environmental actions contribute to a cleaner "
            "and more sustainable community."
        )

        user_id = st.session_state.user_id

        contributions = get_table_count(
            "waste_contributions",
            user_id
        )

        actions = get_table_count(
            "user_actions",
            user_id
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Waste Contributions",
                contributions
            )

        with col2:
            st.metric(
                "Environmental Actions",
                actions
            )

    else:

        st.subheader("Welcome to EcoLoop Node!")

        st.write(
            "A community-driven environmental platform that "
            "connects everyday action with measurable impact."
        )

        st.info(
            "Create an account or log in to record contributions, "
            "participate in community activities and track your impact."
        )

    st.markdown("---")

    section_heading(
        "Explore EcoLoop",
        "Discover the different ways to participate."
    )

    col1, col2 = st.columns(2)

    with col1:

        eco_card(
            "EcoLoop Nodes",
            "Discover environmental collection points.",
            "📍"
        )

        eco_card(
            "Record Waste",
            "Submit details of your recyclable waste contributions.",
            "♻️"
        )

    with col2:

        eco_card(
            "Community",
            "Connect with others and participate in environmental activities.",
            "🌍"
        )

        eco_card(
            "Learn & Grow",
            "Build environmental knowledge through learning and quizzes.",
            "📚"
        )

    st.markdown("---")

    section_heading(
        "Our Purpose",
        "Small actions can create measurable community impact."
    )

    st.write(
        "EcoLoop Node is an environmental technology initiative "
        "under the Climate Action & Environment pillar of "
        "Next Gen Impact Hub (NGIH)."
        )

# =====================================================
# ACCOUNT: LOGIN, REGISTRATION AND PROFILE
# =====================================================

def login_form():

    st.subheader("Login")

    with st.form("ecoloop_login_form"):

        email = st.text_input("Email address")

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Login",
            use_container_width=True
        )

    if submitted:

        if not email or not password:

            st.warning("Please enter your email and password.")

        elif not supabase:

            st.error("Database connection is unavailable.")

        else:

            try:

                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if response.session:

                    set_user_session(response)

                    st.success("Login successful!")
                    st.rerun()

                else:

                    st.error("Login could not be completed.")

            except Exception:

                st.error(
                    "Login failed. Please check your details and try again."
                )


def registration_form():

    st.subheader("Create an Account")

    with st.form("ecoloop_registration_form"):

        full_name = st.text_input("Full name")

        email = st.text_input("Email address")

        password = st.text_input(
            "Create password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Register",
            use_container_width=True
        )

    if submitted:

        if not full_name or not email or not password:

            st.warning("Please complete all fields.")

        elif password != confirm_password:

            st.warning("Your passwords do not match.")

        elif len(password) < 8:

            st.warning("Your password must have at least 8 characters.")

        elif not supabase:

            st.error("Database connection is unavailable.")

        else:

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

                if response.session:

                    set_user_session(response)

                    supabase.table("profiles").update({
                        "full_name": full_name
                    }).eq(
                        "id",
                        str(response.user.id)
                    ).execute()

                    st.success("Your account has been created!")
                    st.rerun()

                else:

                    st.success(
                        "Registration submitted. Check your email "
                        "if email confirmation is required."
                    )

            except Exception:

                st.error(
                    "Registration failed. Please check your details "
                    "or try another email address."
                )


def account_page():

    st.title("My Account")

    if not is_logged_in():

        st.write(
            "Join EcoLoop Node or log in to access your account."
        )

        tab1, tab2 = st.tabs([
            "Login",
            "Register"
        ])

        with tab1:
            login_form()

        with tab2:
            registration_form()

    else:

        profile = st.session_state.get("user") or {}

        st.subheader("My Profile")

        st.write(
            f"**Full name:** {profile.get('full_name', 'Not provided')}"
        )

        st.write(
            f"**Email:** {profile.get('email', 'Not provided')}"
        )

        st.write(
            f"**Account role:** {profile.get('role', 'user')}"
        )

        st.markdown("---")

        st.subheader("Update Profile")

        with st.form("ecoloop_profile_form"):

            new_name = st.text_input(
                "Full name",
                value=profile.get("full_name") or ""
            )

            submitted = st.form_submit_button(
                "Save Changes"
            )

        if submitted:

            if not new_name.strip():

                st.warning("Your name cannot be empty.")

            else:

                try:

                    supabase.table("profiles").update({
                        "full_name": new_name.strip()
                    }).eq(
                        "id",
                        st.session_state.user_id
                    ).execute()

                    load_user_profile()

                    st.success("Your profile has been updated.")
                    st.rerun()

                except Exception:

                    st.error("Unable to update your profile.")

        st.markdown("---")

        if st.button(
            "Logout",
            use_container_width=True
        ):

            try:
                supabase.auth.sign_out()
            except Exception:
                pass

            clear_user_session()
            st.rerun()


# =====================================================
# ECOLOOP NODES
# =====================================================

def generate_station_qr(station_code):

    app_url = (
        "https://ecoloop-node-2-g2jtmgyszhvgynvmnzuo7d.streamlit.app/"
        f"?station={station_code}"
    )

    qr = qrcode.make(app_url)

    image_buffer = io.BytesIO()
    qr.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    return image_buffer


def ecoloop_nodes_page():

    st.title("📍 EcoLoop Nodes")

    st.write(
        "Explore registered environmental collection stations "
        "and use their QR codes to access station information."
    )

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    try:

        response = (
            supabase.table("collection_stations")
            .select("*")
            .order("station_code")
            .execute()
        )

        stations = response.data or []

    except Exception:

        st.error(
            "Unable to load EcoLoop Nodes. "
            "Please check your database connection and permissions."
        )
        return

    if not stations:

        show_empty_state(
            "No collection stations have been registered yet."
        )
        return

    st.markdown("---")

    st.subheader(
        f"Registered Collection Stations: {len(stations)}"
    )

    for station in stations:

        station_name = station.get(
            "station_name",
            "Unnamed Station"
        )

        station_code = station.get(
            "station_code",
            "No code"
        )

        with st.container(border=True):

            col1, col2 = st.columns([2, 1])

            with col1:

                st.subheader(f"📍 {station_name}")

                st.write(
                    f"**Station code:** {station_code}"
                )

                st.caption(
                    "EcoLoop Node collection point"
                )

            with col2:

                if station_code != "No code":

                    qr_image = generate_station_qr(
                        station_code
                    )

                    st.image(
                        qr_image,
                        caption=f"QR code: {station_code}",
                        width=150
                    )

                    st.download_button(
                        label="Download QR Code",
                        data=qr_image.getvalue(),
                        file_name=f"{station_code}_QR.png",
                        mime="image/png",
                        key=f"download_qr_{station_code}"
                    )


# =====================================================
# RECORD WASTE CONTRIBUTIONS
# =====================================================

def record_waste_page():

    st.title("♻️ Record Waste")

    st.write(
        "Record your recyclable waste contribution "
        "and help track environmental action."
    )

    if not is_logged_in():

        st.warning(
            "Please log in to record a waste contribution."
        )
        return

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    # Load registered collection stations
    try:

        station_response = (
            supabase.table("collection_stations")
            .select("station_code, station_name")
            .order("station_code")
            .execute()
        )

        stations = station_response.data or []

    except Exception:

        st.error("Unable to load collection stations.")
        return

    if not stations:

        st.info(
            "There are currently no registered collection stations."
        )
        return

    station_options = {
        f"{station['station_name']} ({station['station_code']})":
        station["station_code"]
        for station in stations
    }

    with st.form("record_waste_form"):

        st.subheader("Contribution Details")

        station_label = st.selectbox(
            "Select EcoLoop Node",
            list(station_options.keys())
        )

        material_type = st.selectbox(
            "Material Type",
            [
                "Plastic",
                "Paper",
                "Cardboard",
                "Glass",
                "Metal",
                "Organic Waste",
                "Electronic Waste",
                "Other"
            ]
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=0.1,
            max_value=10000.0,
            value=1.0,
            step=0.1
        )

        submitted = st.form_submit_button(
            "Submit Contribution",
            use_container_width=True
        )

    if submitted:

        station_code = station_options[station_label]

        try:

            supabase.table("waste_contributions").insert({
                "user_id": st.session_state.user_id,
                "station_code": station_code,
                "material_type": material_type,
                "weight": weight,
                "verification_status": "pending",
                "points": 0
            }).execute()

            st.success(
                "Your contribution has been submitted successfully!"
            )

            st.info(
                "Your contribution is pending verification. "
                "Points will only be awarded after approval."
            )

            st.rerun()

        except Exception:

            st.error(
                "Unable to submit your contribution. "
                "Please check your details and try again."
        )


# =====================================================
# ENVIRONMENTAL IMPACT
# =====================================================

def environmental_impact_page():

    st.title("🌍 Environmental Impact")

    st.write(
        "Track the measurable impact of your environmental contributions."
    )

    if not is_logged_in():

        st.warning("Please log in to view your environmental impact.")
        return

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    try:

        response = (
            supabase.table("waste_contributions")
            .select("weight, points, verification_status")
            .eq("user_id", st.session_state.user_id)
            .eq("verification_status", "verified")
            .execute()
        )

        contributions = response.data or []

    except Exception:

        st.error("Unable to retrieve your environmental impact data.")
        return

    total_weight = sum(
        float(item.get("weight") or 0)
        for item in contributions
    )

    total_points = sum(
        int(item.get("points") or 0)
        for item in contributions
    )

    total_contributions = len(contributions)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Verified Contributions",
            total_contributions
        )

    with col2:
        st.metric(
            "Waste Recovered",
            f"{total_weight:,.2f} kg"
        )

    with col3:
        st.metric(
            "Points Earned",
            total_points
        )

    st.markdown("---")

    st.subheader("Your Contribution History")

    if contributions:

        history = pd.DataFrame(contributions)

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

    else:

        show_empty_state(
            "You do not have any verified waste contributions yet. "
            "Record a contribution to start tracking your impact."
        )


# =====================================================
# LEADERBOARD
# =====================================================

def leaderboard_page():

    st.title("🏆 Community Leaderboard")

    st.write(
        "Recognising members contributing to environmental action "
        "through verified waste recovery."
    )

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    try:

        contribution_response = (
            supabase.table("waste_contributions")
            .select("user_id, weight, points")
            .eq("verification_status", "verified")
            .execute()
        )

        profile_response = (
            supabase.table("profiles")
            .select("id, full_name")
            .execute()
        )

        contributions = contribution_response.data or []
        profiles = profile_response.data or []

    except Exception:

        st.error(
            "Unable to load the leaderboard. "
            "Please check database permissions."
        )
        return

    if not contributions:

        show_empty_state(
            "The leaderboard will appear when members have verified "
            "waste contributions."
        )
        return

    contributions_df = pd.DataFrame(contributions)
    profiles_df = pd.DataFrame(profiles)

    leaderboard = (
        contributions_df
        .groupby("user_id", as_index=False)
        .agg(
            contributions=("user_id", "count"),
            total_weight=("weight", "sum"),
            total_points=("points", "sum")
        )
    )

    if not profiles_df.empty:

        leaderboard = leaderboard.merge(
            profiles_df,
            left_on="user_id",
            right_on="id",
            how="left"
        )

    else:

        leaderboard["full_name"] = "EcoLoop Member"

    leaderboard["full_name"] = (
        leaderboard["full_name"]
        .fillna("EcoLoop Member")
    )

    leaderboard = leaderboard.sort_values(
        by=["total_points", "total_weight"],
        ascending=[False, False]
    ).reset_index(drop=True)

    leaderboard.index = leaderboard.index + 1

    leaderboard = leaderboard.rename(
        columns={
            "full_name": "Member",
            "contributions": "Verified Contributions",
            "total_weight": "Waste Recovered (kg)",
            "total_points": "Points"
        }
    )

    st.dataframe(
        leaderboard[
            [
                "Member",
                "Verified Contributions",
                "Waste Recovered (kg)",
                "Points"
            ]
        ],
        use_container_width=True
    )


# =====================================================
# EXPLORE & LEARN
# =====================================================

def explore_learn_page():

    st.title("📚 Explore & Learn")

    st.write(
        "Build your environmental knowledge and discover "
        "how everyday choices can support a sustainable future."
    )

    learning_topics = [
        {
            "title": "Waste Management",
            "icon": "♻️",
            "description": (
                "Learn about waste separation, recycling, "
                "reuse and responsible disposal."
            )
        },
        {
            "title": "Climate Action",
            "icon": "🌍",
            "description": (
                "Understand climate change, its effects "
                "and practical community responses."
            )
        },
        {
            "title": "Circular Economy",
            "icon": "🔄",
            "description": (
                "Explore how materials can remain in use "
                "through repair, reuse and recycling."
            )
        },
        {
            "title": "Environmental Conservation",
            "icon": "🌱",
            "description": (
                "Discover ways to protect natural resources "
                "and local ecosystems."
            )
        },
        {
            "title": "Community Participation",
            "icon": "🤝",
            "description": (
                "Learn how individuals and communities "
                "can work together for environmental improvement."
            )
        },
        {
            "title": "Sustainable Living",
            "icon": "💡",
            "description": (
                "Explore practical habits that can reduce "
                "waste and environmental pressure."
            )
        }
    ]

    for start in range(0, len(learning_topics), 2):

        col1, col2 = st.columns(2)

        for column, topic in zip(
            [col1, col2],
            learning_topics[start:start + 2]
        ):

            with column:

                eco_card(
                    topic["title"],
                    topic["description"],
                    topic["icon"]
                )


# =====================================================
# ECO QUIZ
# =====================================================

def eco_quiz_page():

    st.title("🧠 Eco Quiz")

    st.write(
        "Test your environmental knowledge and earn points "
        "through completed quizzes."
    )

    if not is_logged_in():

        st.warning("Please log in to participate in Eco Quiz.")
        return

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    # Load available quizzes
    try:

        quiz_response = (
            supabase.table("quizzes")
            .select("*")
            .execute()
        )

        quizzes = quiz_response.data or []

    except Exception:

        st.error("Unable to load quizzes.")
        return

    if not quizzes:

        show_empty_state(
            "There are no quizzes available at the moment."
        )
        return

    # Only show active quizzes
    quizzes = [
        quiz for quiz in quizzes
        if quiz.get("is_active", True)
    ]

    if not quizzes:

        show_empty_state(
            "There are currently no active quizzes."
        )
        return

    quiz_options = {
        quiz.get("title", f"Quiz {index + 1}"): quiz
        for index, quiz in enumerate(quizzes)
    }

    selected_title = st.selectbox(
        "Choose a quiz",
        list(quiz_options.keys())
    )

    selected_quiz = quiz_options[selected_title]
    quiz_id = selected_quiz.get("id")

    st.write(
        selected_quiz.get(
            "description",
            "Test your knowledge of environmental sustainability."
        )
    )

    if st.button(
        "Start Quiz",
        use_container_width=True
    ):

        try:

            attempt_response = (
                supabase.table("quiz_attempts")
                .insert({
                    "user_id": st.session_state.user_id,
                    "quiz_id": quiz_id
                })
                .execute()
            )

            attempt = attempt_response.data[0]

            st.session_state.active_quiz_attempt = attempt["id"]
            st.session_state.active_quiz_id = quiz_id
            st.session_state.active_quiz_index = 0
            st.session_state.active_quiz_results = []

            question_response = (
                supabase.table("quiz_questions")
                .select("*")
                .eq("quiz_id", quiz_id)
                .execute()
            )

            st.session_state.active_quiz_questions = (
                question_response.data or []
            )

            st.rerun()

        except Exception:

            st.error(
                "Unable to start this quiz. "
                "Please try again or contact the administrator."
            )

    # Display an active quiz attempt
    attempt_id = st.session_state.get(
        "active_quiz_attempt"
    )

    questions = st.session_state.get(
        "active_quiz_questions",
        []
    )

    if not attempt_id:
        return

    if not questions:

        st.warning("This quiz does not contain any questions.")
        return

    question_index = st.session_state.active_quiz_index

    if question_index >= len(questions):

        try:

            finish_response = supabase.rpc(
                "finish_quiz_attempt",
                {
                    "p_attempt_id": attempt_id
                }
            ).execute()

            st.success("Quiz completed!")

            st.write(
                "Your answers have been submitted and your score "
                "has been calculated."
            )

            st.write(finish_response.data)

            st.session_state.active_quiz_attempt = None
            st.session_state.active_quiz_questions = []
            st.session_state.active_quiz_index = 0
            st.session_state.active_quiz_results = []
            st.session_state.active_quiz_id = None

        except Exception:

            st.error(
                "Unable to finish your quiz. "
                "Please try again."
            )

        return

    question = questions[question_index]

    question_text = question.get(
        "question_text",
        question.get("question", "Question")
    )

    options = question.get("options", [])

    if isinstance(options, dict):
        options = list(options.values())

    if not isinstance(options, list) or not options:

        st.error(
            "This question has no readable answer options."
        )
        return

    st.progress(
        (question_index + 1) / len(questions)
    )

    st.subheader(
        f"Question {question_index + 1} of {len(questions)}"
    )

    st.write(question_text)

    selected_option = st.radio(
        "Choose your answer",
        options,
        key=f"eco_quiz_answer_{attempt_id}_{question_index}"
    )

    if st.button(
        "Submit Answer",
        use_container_width=True
    ):

        try:

            answer_response = supabase.rpc(
                "submit_quiz_answer",
                {
                    "p_attempt_id": attempt_id,
                    "p_question_id": question["id"],
                    "p_selected_option": str(selected_option)
                }
            ).execute()

            st.session_state.active_quiz_results.append(
                answer_response.data
            )

            st.session_state.active_quiz_index += 1

            st.rerun()

        except Exception:

            st.error(
                "Unable to submit your answer. "
                "Please try again."
        )


# =====================================================
# COMMUNITY GROUPS
# =====================================================

def community_groups_page():

    st.title("🤝 Community Groups")

    st.write(
        "Connect with people working together to create "
        "cleaner and more sustainable communities."
    )

    if not supabase:
        st.error("Database connection is unavailable.")
        return

    try:
        response = (
            supabase.table("community_groups")
            .select("*")
            .execute()
        )

        groups = response.data or []

    except Exception:
        st.error("Unable to load community groups.")
        return

    if not groups:
        show_empty_state(
            "There are no community groups available yet."
        )
        return

    for group in groups:

        group_name = (
            group.get("group_name")
            or group.get("name")
            or "Community Group"
        )

        description = group.get(
            "description",
            "A community working towards environmental improvement."
        )

        with st.container(border=True):

            st.subheader(f"🌱 {group_name}")
            st.write(description)

            if group.get("location"):
                st.caption(f"Location: {group['location']}")

            if is_logged_in():

                group_id = group.get("id")

                if group_id and st.button(
                    "Request to Join",
                    key=f"join_group_{group_id}"
                ):

                    try:

                        supabase.table("group_memberships").insert({
                            "group_id": group_id,
                            "user_id": st.session_state.user_id,
                            "status": "pending"
                        }).execute()

                        st.success(
                            "Your membership request has been submitted."
                        )

                    except Exception:

                        st.error(
                            "Unable to submit your request. "
                            "You may already have a membership request."
                        )

            else:

                st.caption("Log in to request group membership.")


# =====================================================
# COMMUNITY CHALLENGES
# =====================================================

def challenges_page():

    st.title("🌍 Community Challenges")

    st.write(
        "Discover activities that encourage individuals "
        "and communities to take environmental action."
    )

    if not supabase:
        st.error("Database connection is unavailable.")
        return

    try:

        response = (
            supabase.table("community_challenges")
            .select("*")
            .execute()
        )

        challenges = response.data or []

    except Exception:

        st.error("Unable to load community challenges.")
        return

    if not challenges:

        show_empty_state(
            "No community challenges have been published yet."
        )
        return

    for challenge in challenges:

        title = (
            challenge.get("title")
            or challenge.get("challenge_name")
            or "Community Challenge"
        )

        description = challenge.get(
            "description",
            "Take part in a community environmental activity."
        )

        with st.container(border=True):

            st.subheader(f"🌿 {title}")
            st.write(description)

            if challenge.get("start_date"):
                st.caption(
                    f"Starts: {challenge['start_date']}"
                )

            if challenge.get("end_date"):
                st.caption(
                    f"Ends: {challenge['end_date']}"
                )

            if challenge.get("status"):
                st.caption(
                    f"Status: {challenge['status']}"
                )


# =====================================================
# ACTION GALLERY
# =====================================================

def action_gallery_page():

    st.title("📸 Environmental Action Gallery")

    st.write(
        "Explore environmental activities, community initiatives "
        "and actions that inspire positive change."
    )

    if not supabase:
        st.error("Database connection is unavailable.")
        return

    try:

        response = (
            supabase.table("environmental_actions")
            .select("*")
            .execute()
        )

        actions = response.data or []

    except Exception:

        st.error("Unable to load environmental activities.")
        return

    if not actions:

        show_empty_state(
            "The Action Gallery is waiting for its first "
            "environmental activities."
        )
        return

    st.markdown("---")

    st.subheader("Community Environmental Activities")

    for action in actions:

        title = (
            action.get("title")
            or action.get("action_name")
            or action.get("name")
            or "Environmental Activity"
        )

        description = action.get(
            "description",
            "A community environmental initiative."
        )

        status = action.get("status", "Published")

        with st.container(border=True):

            st.subheader(f"🌱 {title}")

            st.write(description)

            if action.get("location"):
                st.caption(
                    f"📍 {action['location']}"
                )

            if action.get("created_at"):
                st.caption(
                    f"Added: {str(action['created_at'])[:10]}"
                )

            st.caption(f"Status: {status}")


# =====================================================
# COLLECTION MANAGEMENT
# =====================================================

def collection_management_page():

    st.title("🚛 Collection Management")

    st.write(
        "View collection stations and available collection records "
        "to support organised waste recovery."
    )

    if not is_logged_in():

        st.warning(
            "Please log in to access collection management."
        )
        return

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    st.markdown("---")

    # Collection stations
    st.subheader("Registered Collection Stations")

    try:

        station_response = (
            supabase.table("collection_stations")
            .select("*")
            .execute()
        )

        stations = station_response.data or []

        if stations:

            st.dataframe(
                pd.DataFrame(stations),
                use_container_width=True,
                hide_index=True
            )

        else:

            show_empty_state(
                "No collection stations are currently registered."
            )

    except Exception:

        st.error("Unable to retrieve collection stations.")

    st.markdown("---")

    # Collection records
    st.subheader("Collection Records")

    try:

        records_response = (
            supabase.table("collection_records")
            .select("*")
            .execute()
        )

        records = records_response.data or []

        if records:

            st.dataframe(
                pd.DataFrame(records),
                use_container_width=True,
                hide_index=True
            )

        else:

            show_empty_state(
                "No collection records are available yet."
            )

    except Exception:

        st.info(
            "Collection records are not currently available "
            "to this account."
        )

    st.markdown("---")

    st.caption(
        "Collection record creation, assignment and verification "
        "will be connected after confirming the existing database "
        "columns and permissions."
            )


# =====================================================
# ADMIN: VERIFY CONTRIBUTIONS
# =====================================================

def verify_contributions_page():

    st.title("🛡️ Verify Contributions")

    if not is_admin():

        st.error("You do not have permission to access this page.")
        return

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    st.write(
        "Review waste contributions submitted by EcoLoop members."
    )

    try:

        response = (
            supabase.table("waste_contributions")
            .select("*")
            .eq("verification_status", "pending")
            .order("submitted_at", desc=True)
            .execute()
        )

        pending = response.data or []

    except Exception:

        st.error("Unable to retrieve pending contributions.")
        return

    st.metric("Pending Contributions", len(pending))

    if not pending:

        show_empty_state(
            "There are no pending contributions to review."
        )
        return

    for contribution in pending:

        contribution_id = contribution.get("id")

        with st.container(border=True):

            st.subheader(
                f"Contribution: {str(contribution_id)[:8]}"
            )

            st.write(
                f"**Member ID:** {contribution.get('user_id', 'Unknown')}"
            )

            st.write(
                f"**Station:** {contribution.get('station_code', 'Unknown')}"
            )

            st.write(
                f"**Material:** {contribution.get('material_type', 'Unknown')}"
            )

            st.write(
                f"**Weight:** {contribution.get('weight', 0)} kg"
            )

            st.write(
                f"**Submitted:** {contribution.get('submitted_at', 'Unknown')}"
            )

            st.caption(
                "Review the contribution before making a decision."
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Approve",
                    key=f"approve_{contribution_id}",
                    use_container_width=True
                ):

                    try:

                        supabase.table("waste_contributions").update({
                            "verification_status": "verified"
                        }).eq(
                            "id",
                            contribution_id
                        ).eq(
                            "verification_status",
                            "pending"
                        ).execute()

                        st.success("Contribution approved.")
                        st.rerun()

                    except Exception:

                        st.error(
                            "Approval failed. Check administrator permissions."
                        )

            with col2:

                if st.button(
                    "Reject",
                    key=f"reject_{contribution_id}",
                    use_container_width=True
                ):

                    try:

                        supabase.table("waste_contributions").update({
                            "verification_status": "rejected"
                        }).eq(
                            "id",
                            contribution_id
                        ).eq(
                            "verification_status",
                            "pending"
                        ).execute()

                        st.success("Contribution rejected.")
                        st.rerun()

                    except Exception:

                        st.error(
                            "Rejection failed. Check administrator permissions."
                        )


# =====================================================
# ADMIN: ADMIN STUDIO
# =====================================================

def admin_studio_page():

    st.title("⚙️ Admin Studio")

    if not is_admin():

        st.error("You do not have permission to access this page.")
        return

    if not supabase:

        st.error("Database connection is unavailable.")
        return

    st.write(
        "An overview of EcoLoop Node platform activity."
    )

    table_names = [
        ("Registered Profiles", "profiles"),
        ("Collection Stations", "collection_stations"),
        ("Waste Contributions", "waste_contributions"),
        ("Community Groups", "community_groups"),
        ("Environmental Actions", "environmental_actions"),
        ("Community Challenges", "community_challenges")
    ]

    columns = st.columns(3)

    for index, (label, table_name) in enumerate(table_names):

        count = get_table_count(table_name)

        with columns[index % 3]:

            st.metric(label, count)


# =====================================================
# ABOUT NEXT GEN IMPACT HUB
# =====================================================

def about_ngih_page():

    st.title("🌍 About Next Gen Impact Hub")

    st.write(
        "Next Gen Impact Hub (NGIH) is a youth-focused initiative "
        "committed to creating opportunities for young people to "
        "lead, innovate and influence positive change."
    )

    st.markdown("---")

    st.subheader("Our Mission")

    st.write(
        "To create a generation of youth who lead and influence "
        "across governance, economy, environment and technology."
    )

    st.markdown("---")

    st.subheader("Our Four Pillars")

    pillars = [
        (
            "Governance & Civic Education",
            "Promoting informed, active and responsible citizenship."
        ),
        (
            "Climate Action & Environment",
            "Encouraging environmental responsibility and sustainable communities."
        ),
        (
            "Business & Entrepreneurship",
            "Supporting innovation, enterprise and economic participation."
        ),
        (
            "Technology, Innovation, Media & Arts",
            "Using creativity and technology to develop solutions and amplify ideas."
        )
    ]

    for title, description in pillars:

        eco_card(
            title,
            description,
            "✦"
        )

    st.markdown("---")

    st.subheader("EcoLoop Node")

    st.write(
        "EcoLoop Node is an environmental technology initiative "
        "under NGIH's Climate Action & Environment pillar. "
        "It connects environmental action, community participation, "
        "learning and measurable impact."
    )


# =====================================================
# SYSTEM DIAGNOSTICS
# =====================================================

def system_diagnostics_page():

    st.title("🔧 System Diagnostics")

    if not is_admin():

        st.error("Administrator access is required.")
        return

    st.write(
        "A basic overview of the application's connection status."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        if supabase:

            st.success("Supabase client initialised")

        else:

            st.error("Supabase client unavailable")

    with col2:

        if is_logged_in():

            st.success("User session active")

        else:

            st.warning("No active user session")

    st.markdown("---")

    st.subheader("Application Information")

    st.write(f"**Application:** {APP_NAME}")

    st.write(f"**Organisation:** {NGIH_NAME}")

    st.write(
        f"**Authenticated user:** "
        f"{st.session_state.get('user_id') or 'None'}"
    )

    st.write(
        f"**Account role:** "
        f"{(st.session_state.get('user') or {}).get('role', 'Guest')}"
    )

    st.caption(
        "These diagnostics report basic application state. "
        "They do not replace a full security or database audit."
    )
