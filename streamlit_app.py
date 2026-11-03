
import streamlit as st
import pandas as pd
import qrcode
from pathlib import Path
from io import BytesIO
from datetime import datetime
import re

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="EcoLoop Node 2.0",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOGO_FILE = "IMG-20261028-WA0000.jpg"

# ==================================================
# DESIGN SYSTEM
# ==================================================

st.markdown("""
<style>
.stApp {
    background: #F5F8F5;
    color: #24342A;
}

[data-testid="stHeader"] {
    background: #F5F8F5;
}

h1, h2, h3, h4 {
    color: #145C3A !important;
}

p, label, li {
    color: #293B30;
}

[data-testid="stSidebar"] {
    background: #123D2B;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] .stRadio label {
    color: #FFFFFF !important;
}

[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 18px;
    border: 1px solid #DCE8DF;
    border-radius: 13px;
}

[data-testid="stMetricLabel"] {
    color: #53685A !important;
}

[data-testid="stMetricValue"] {
    color: #145C3A !important;
}

.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"],
.stTextArea textarea {
    background: #FFFFFF !important;
    color: #24342A !important;
}

div.stButton > button,
div.stFormSubmitButton > button {
    background: #176B45;
    color: white !important;
    border-radius: 9px;
    border: none;
    min-height: 42px;
    font-weight: 600;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: #104D32;
    color: white !important;
}

.eco-footer {
    text-align: center;
    color: #52675A;
    padding: 25px 5px;
    border-top: 1px solid #DCE7DF;
    margin-top: 40px;
}

.eco-subtitle {
    color: #60756A;
    font-size: 15px;
}

div[data-testid="stExpander"] {
    background: #FFFFFF;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# SESSION DATA
# ==================================================

defaults = {
    "users": [],
    "records": [],
    "collected": [],
    "current_user": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

STATIONS = {
    "ECO001": "City Centre Station",
    "ECO002": "Community Recycling Station",
    "ECO003": "School Recycling Station"
}

MATERIALS = [
    "Plastic",
    "Paper",
    "Metal",
    "Glass",
    "Organic",
    "Electronic"
]

# ==================================================
# HELPER FUNCTIONS
# ==================================================

def approved_records():
    return [
        r for r in st.session_state.records
        if r["status"] == "Approved"
    ]


def total_weight():
    return sum(
        r["weight"] for r in approved_records()
    )


def user_points(username):
    return sum(
        r["points"]
        for r in approved_records()
        if r["username"] == username
    )


def make_qr(station_id):
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=3
    )
    qr.add_data(
        f"EcoLoop Node 2.0 | Station: {station_id}"
    )
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="#176B45",
        back_color="white"
    )

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def valid_email(email):
    return bool(
        re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)
    )


# ==================================================
# BRAND HEADER
# ==================================================

logo_col, brand_col = st.columns([1, 5])

with logo_col:
    if Path(LOGO_FILE).is_file():
        st.image(LOGO_FILE, width=125)
    else:
        st.markdown("## ♻️ NGIH")

with brand_col:
    st.markdown(
        "<h1 style='margin-bottom:0;'>EcoLoop Node 2.0</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p class='eco-subtitle'>"
        "Intelligent Waste Management & Recycling Coordination"
        "</p>",
        unsafe_allow_html=True
    )

st.divider()

# ==================================================
# NAVIGATION
# ==================================================

st.sidebar.markdown("## ♻️ EcoLoop Node")

if Path(LOGO_FILE).is_file():
    st.sidebar.image(LOGO_FILE, width=115)

st.sidebar.caption("Next Gen Impact Hub | NGIH")

page = st.sidebar.radio(
    "EXPLORE PLATFORM",
    [
        "Home",
        "Register",
        "My Profile",
        "Record Waste",
        "QR Stations",
        "Verify Contributions",
        "Leaderboard",
        "Collection Management",
        "Environmental Impact",
        "About"
    ]
)

st.sidebar.divider()

st.sidebar.markdown("### Platform information")
st.sidebar.success("Demo platform active")
st.sidebar.caption(
    "Digital demonstration. Secure accounts, shared database "
    "and physical sensors are future development stages."
)

# ==================================================
# HOME
# ==================================================

if page == "Home":

    st.title("Welcome to EcoLoop")
    st.write(
        "Turning waste into opportunity through technology, "
        "community participation and smarter recycling."
    )

    approved = approved_records()

    a, b, c, d = st.columns(4)

    a.metric("Registered Participants", len(st.session_state.users))
    b.metric("Approved Contributions", len(approved))
    c.metric("Waste Recovered", f"{total_weight():.1f} kg")
    d.metric("Collection Stations", len(STATIONS))

    st.divider()

    left, right = st.columns([1.4, 1])

    with left:
        st.subheader("Waste Recovery Overview")

        if approved:
            material_data = {}

            for record in approved:
                material_data[record["material"]] = (
                    material_data.get(record["material"], 0)
                    + record["weight"]
                )

            df = pd.DataFrame(
                list(material_data.items()),
                columns=["Material", "Weight (kg)"]
            )

            st.bar_chart(df.set_index("Material"))

        else:
            st.info(
                "No approved waste contributions yet. "
                "Your recovery data will appear here."
            )

    with right:
        st.subheader("How EcoLoop Works")

        st.markdown("""
        **01 — Register**

        Join the EcoLoop community.

        **02 — Separate**

        Sort waste by material.

        **03 — Contribute**

        Record your waste contribution.

        **04 — Verify**

        Contributions are checked.

        **05 — Recover**

        Organise waste for collection.

        **06 — Measure**

        Track environmental participation.
        """)

    st.divider()
    st.subheader("Our Digital Collection Network")

    cols = st.columns(3)

    for i, (station_id, name) in enumerate(STATIONS.items()):
        with cols[i]:
            st.markdown(f"### {station_id}")
            st.write(name)
            st.caption("Demonstration station")

# ==================================================
# REGISTRATION
# ==================================================

elif page == "Register":

    st.title("Create Your EcoLoop Profile")

    st.write(
        "Become part of a community working towards "
        "better waste management and environmental sustainability."
    )

    st.info(
        "Complete this form to create your demonstration profile. "
        "You can then record contributions and participate "
        "in EcoLoop activities."
    )

    with st.form("registration_form"):

        st.subheader("Personal Information")

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        username = st.text_input(
            "Choose a Username",
            placeholder="Example: EcoChampion01"
        )

        email = st.text_input(
            "Email Address",
            placeholder="Example: user@example.com"
        )

        st.subheader("Community Information")

        user_type = st.selectbox(
            "Account Type",
            [
                "Individual",
                "School",
                "University",
                "Community Organisation"
            ]
        )

        location = st.text_input(
            "Community or Area",
            placeholder="Enter your community"
        )

        st.caption(
            "This demonstration does not collect passwords. "
            "Do not enter sensitive personal information."
        )

        submitted = st.form_submit_button(
            "Create EcoLoop Profile",
            use_container_width=True
        )

        if submitted:

            if not all([
                full_name.strip(),
                username.strip(),
                email.strip(),
                location.strip()
            ]):
                st.error("Please complete all fields.")

            elif not valid_email(email.strip()):
                st.error("Please enter a valid email address.")

            elif any(
                u["username"].lower() == username.strip().lower()
                for u in st.session_state.users
            ):
                st.error("That username is already taken.")

            elif any(
                u["email"].lower() == email.strip().lower()
                for u in st.session_state.users
            ):
                st.error("This email is already registered.")

            else:

                st.session_state.users.append({
                    "name": full_name.strip(),
                    "username": username.strip(),
                    "email": email.strip(),
                    "type": user_type,
                    "location": location.strip(),
                    "joined": datetime.now().strftime("%Y-%m-%d")
                })

                st.success(
                    f"Welcome to EcoLoop, {full_name}!"
                )
                st.balloons()

# ==================================================
# MY PROFILE
# ==================================================

elif page == "My Profile":

    st.title("Participant Profiles")

    if not st.session_state.users:

        st.info("No participants have registered yet.")

    else:

        usernames = [
            u["username"] for u in st.session_state.users
        ]

        selected = st.selectbox(
            "Select demonstration profile",
            usernames
        )

        user = next(
            u for u in st.session_state.users
            if u["username"] == selected
        )

        st.subheader(user["name"])

        a, b, c = st.columns(3)

        a.metric("EcoPoints", user_points(selected))

        b.metric(
            "Approved Contributions",
            len([
                r for r in approved_records()
                if r["username"] == selected
            ])
        )

        c.metric(
            "Waste Recovered",
            f"{sum(r['weight'] for r in approved_records() if r['username'] == selected):.1f} kg"
        )

        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Account type:** {user['type']}")
        st.write(f"**Community:** {user['location']}")
        st.write(f"**Joined:** {user['joined']}")

        st.caption(
            "Profiles are demonstration records, not private authenticated accounts."
        )

# ==================================================
# RECORD WASTE
# ==================================================

elif page == "Record Waste":

    st.title("Record a Waste Contribution")

    st.write(
        "Submit details about waste delivered to an EcoLoop station."
    )

    if not st.session_state.users:

        st.warning(
            "Please create a participant profile first."
        )

    else:

        with st.form("waste_form"):

            selected_user = st.selectbox(
                "Select Participant",
                [
                    u["username"]
                    for u in st.session_state.users
                ]
            )

            material = st.selectbox(
                "Waste Material",
                MATERIALS
            )

            weight = st.number_input(
                "Weight (kg)",
                min_value=0.1,
                max_value=1000.0,
                value=1.0,
                step=0.1
            )

            station = st.selectbox(
                "Collection Station",
                list(STATIONS.keys()),
                format_func=lambda x: f"{x} — {STATIONS[x]}"
            )

            submitted = st.form_submit_button(
                "Submit Contribution",
                use_container_width=True
            )

            if submitted:

                record_id = (
                    f"ECO-{len(st.session_state.records) + 1:04d}"
                )

                st.session_state.records.append({
                    "id": record_id,
                    "username": selected_user,
                    "material": material,
                    "weight": float(weight),
                    "station": station,
                    "date": datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "status": "Pending",
                    "points": 0
                })

                st.success(
                    f"{record_id} submitted successfully for verification."
                )

# ==================================================
# QR STATIONS
# ==================================================

elif page == "QR Stations":

    st.title("EcoLoop Collection Stations")

    st.write(
        "Each digital station has its own identification QR code."
    )

    for station_id, station_name in STATIONS.items():

        with st.expander(
            f"{station_id} — {station_name}"
        ):

            qr_image = make_qr(station_id)

            st.image(qr_image, width=200)

            st.download_button(
                "Download QR Code",
                data=qr_image.getvalue(),
                file_name=f"{station_id}_QR.png",
                mime="image/png",
                key=f"qr_{station_id}"
            )

            st.caption(
                "This QR code identifies the station. "
                "It does not yet submit contributions automatically."
            )

# ==================================================
# VERIFY CONTRIBUTIONS
# ==================================================

elif page == "Verify Contributions":

    st.title("Contribution Verification")

    st.warning(
        "Demonstration coordinator interface. "
        "This page does not yet have administrator authentication."
    )

    pending = [
        r for r in st.session_state.records
        if r["status"] == "Pending"
    ]

    if not pending:

        st.info("No contributions are awaiting verification.")

    else:

        for record in pending:

            with st.container(border=True):

                st.markdown(f"### {record['id']}")

                st.write(f"Participant: {record['username']}")
                st.write(f"Material: {record['material']}")
                st.write(f"Weight: {record['weight']} kg")
                st.write(f"Station: {record['station']}")
                st.write(f"Submitted: {record['date']}")

                approve_col, reject_col = st.columns(2)

                with approve_col:

                    if st.button(
                        "Approve",
                        key=f"approve_{record['id']}"
                    ):

                        record["status"] = "Approved"
                        record["points"] = (
                            5 + int(record["weight"] * 2)
                        )

                        st.success("Contribution approved.")
                        st.rerun()

                with reject_col:

                    if st.button(
                        "Reject",
                        key=f"reject_{record['id']}"
                    ):

                        record["status"] = "Rejected"
                        st.warning("Contribution rejected.")
                        st.rerun()

# ==================================================
# LEADERBOARD
# ==================================================

elif page == "Leaderboard":

    st.title("EcoLoop Community Leaderboard")

    st.write(
        "Recognising community participation in waste recovery."
    )

    if not st.session_state.users:

        st.info("No participants registered yet.")

    else:

        ranking = []

        for user in st.session_state.users:

            ranking.append({
                "Participant": user["username"],
                "Account Type": user["type"],
                "Recovered Waste (kg)": sum(
                    r["weight"]
                    for r in approved_records()
                    if r["username"] == user["username"]
                ),
                "EcoPoints": user_points(user["username"])
            })

        ranking_df = pd.DataFrame(ranking)

        ranking_df = ranking_df.sort_values(
            "EcoPoints",
            ascending=False
        )

        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "EcoPoints are demonstration participation points, "
            "not cash rewards."
        )

# ==================================================
# COLLECTION MANAGEMENT
# ==================================================

elif page == "Collection Management":

    st.title("Collection Management")

    approved = approved_records()

    uncollected = [
        r for r in approved
        if r["id"] not in st.session_state.collected
    ]

    total_waiting = sum(
        r["weight"] for r in uncollected
    )

    st.metric(
        "Approved Waste Awaiting Collection",
        f"{total_waiting:.1f} kg"
    )

    if not uncollected:

        st.info("No approved waste is awaiting collection.")

    else:

        for station_id, station_name in STATIONS.items():

            station_records = [
                r for r in uncollected
                if r["station"] == station_id
            ]

            if station_records:

                st.subheader(
                    f"{station_id} — {station_name}"
                )

                for record in station_records:

                    st.write(
                        f"{record['id']} | "
                        f"{record['material']} | "
                        f"{record['weight']} kg"
                    )

                    if st.button(
                        "Mark as Collected",
                        key=f"collect_{record['id']}"
                    ):

                        st.session_state.collected.append(
                            record["id"]
                        )

                        st.success("Collection status updated.")
                        st.rerun()

# ==================================================
# ENVIRONMENTAL IMPACT
# ==================================================

elif page == "Environmental Impact":

    st.title("Environmental Impact Tracker")

    approved = approved_records()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Waste Recovered",
        f"{total_weight():.1f} kg"
    )

    col2.metric(
        "Material Categories",
        len(set(r["material"] for r in approved))
    )

    col3.metric(
        "Approved Contributions",
        len(approved)
    )

    if approved:

        material_data = {}

        for record in approved:

            material_data[record["material"]] = (
                material_data.get(record["material"], 0)
                + record["weight"]
            )

        impact_df = pd.DataFrame(
            list(material_data.items()),
            columns=["Material", "Weight (kg)"]
        )

        st.subheader("Material Recovery Breakdown")

        st.bar_chart(
            impact_df.set_index("Material")
        )

        st.dataframe(
            impact_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Environmental data will appear after contributions "
            "have been approved."
        )

    st.caption(
        "This dashboard reports recorded quantities. "
        "It does not claim verified carbon savings."
    )

# ==================================================
# ABOUT
# ==================================================

elif page == "About":

    st.title("About EcoLoop Node 2.0")

    st.markdown("""
    ### Rethinking Waste Management Through Technology

    EcoLoop Node 2.0 is an environmental technology initiative
    developed to improve waste separation, recycling participation
    and collection coordination.

    ### Our Mission

    To make waste management more accessible, organised and
    data-driven through affordable digital technology.

    ### Our Vision

    Communities where waste is recognised as a recoverable
    resource rather than simply a problem.

    ### Current Demonstration Features

    - Participant registration
    - Digital participant profiles
    - Waste contribution recording
    - QR-coded station identification
    - Contribution verification
    - Community leaderboard
    - Collection management
    - Environmental data tracking

    ### Future Development

    - ESP32 smart collection stations
    - Ultrasonic fill-level sensors
    - Weight measurement sensors
    - AI-assisted waste classification
    - Live collection notifications
    - Secure database and authentication
    - Integration with recycling organisations
    """)

    st.divider()

    st.subheader("Designed and Developed by")

    st.markdown("## Munashe R. Mutopa")

    st.write("An initiative of Next Gen Impact Hub (NGIH)")

# ==================================================
# FOOTER
# ==================================================

st.markdown("""
<div class="eco-footer">
    <strong>EcoLoop Node 2.0</strong><br>
    Designed and Developed by Munashe R. Mutopa<br>
    An initiative of Next Gen Impact Hub (NGIH)<br>
    Building smarter and more sustainable communities.
</div>
""", unsafe_allow_html=True)
