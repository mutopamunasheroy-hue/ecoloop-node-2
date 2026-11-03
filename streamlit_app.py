
import streamlit as st
import pandas as pd
import qrcode
from pathlib import Path
from io import BytesIO
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="EcoLoop Node 2.0",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOGO_FILE = "IMG-20261028-WA0000.jpg"

# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #F4F8F5;
}
h1, h2, h3 {
    color: #176B45;
}
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E0EAE3;
}
div.stButton > button {
    background-color: #176B45;
    color: white;
    border-radius: 8px;
    border: none;
    min-height: 42px;
}
div.stButton > button:hover {
    background-color: #104D32;
    color: white;
}
.eco-footer {
    text-align: center;
    color: #60756A;
    padding: 25px 5px 10px 5px;
    border-top: 1px solid #DCE7DF;
    margin-top: 35px;
}
.small-note {
    color: #60756A;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SESSION DATA
# --------------------------------------------------

if "users" not in st.session_state:
    st.session_state.users = []

if "records" not in st.session_state:
    st.session_state.records = []

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "collected" not in st.session_state:
    st.session_state.collected = []

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

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def approved_records():
    return [
        r for r in st.session_state.records
        if r["status"] == "Approved"
    ]


def total_weight():
    return sum(
        r["weight"] for r in approved_records()
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


def get_points(user):
    return sum(
        r["points"]
        for r in approved_records()
        if r["user"] == user
    )


def get_user_names():
    return [u["name"] for u in st.session_state.users]


# --------------------------------------------------
# HEADER AND BRANDING
# --------------------------------------------------

logo_col, title_col = st.columns([1, 5])

with logo_col:
    if Path(LOGO_FILE).is_file():
        st.image(LOGO_FILE, width=125)
    else:
        st.markdown("## ♻️ NGIH")

with title_col:
    st.markdown(
        "<h1 style='margin-bottom:0;'>EcoLoop Node 2.0</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#60756A;margin-top:0;'>"
        "Smart Waste Management & Recycling Coordination"
        "</p>",
        unsafe_allow_html=True
    )

st.divider()

# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.markdown("## ♻️ EcoLoop Node")

if Path(LOGO_FILE).is_file():
    st.sidebar.image(LOGO_FILE, width=100)

st.sidebar.caption("An NGIH environmental technology initiative")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Home Dashboard",
        "User Registration",
        "Record Waste",
        "Station QR Codes",
        "Contribution Verification",
        "Leaderboard",
        "Collection Management",
        "Environmental Impact",
        "About EcoLoop"
    ]
)

st.sidebar.divider()

st.sidebar.markdown("### Platform status")
st.sidebar.success("Demonstration mode")
st.sidebar.caption(
    "Hardware sensors and live multi-user storage "
    "are planned for future development."
)

# --------------------------------------------------
# HOME DASHBOARD
# --------------------------------------------------

if page == "Home Dashboard":

    st.title("Welcome to EcoLoop")
    st.write(
        "A smarter approach to waste separation, "
        "recycling participation and collection coordination."
    )

    approved = approved_records()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Registered Users",
        len(st.session_state.users)
    )

    col2.metric(
        "Approved Contributions",
        len(approved)
    )

    col3.metric(
        "Waste Recovered",
        f"{total_weight():.1f} kg"
    )

    col4.metric(
        "Collection Stations",
        len(STATIONS)
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Waste Recovery Overview")

        if approved:
            material_data = {}

            for r in approved:
                material_data[r["material"]] = (
                    material_data.get(r["material"], 0)
                    + r["weight"]
                )

            chart_df = pd.DataFrame(
                list(material_data.items()),
                columns=["Material", "Weight (kg)"]
            )

            st.bar_chart(
                chart_df.set_index("Material")
            )
        else:
            st.info(
                "No approved contributions yet. "
                "Start by recording a contribution."
            )

    with right:
        st.subheader("How EcoLoop Works")

        st.markdown("""
        1. **Register:** Join the EcoLoop community.
        2. **Separate:** Sort waste by material.
        3. **Contribute:** Record your waste contribution.
        4. **Verify:** Contributions are checked.
        5. **Collect:** Waste is organised for collection.
        6. **Measure:** Track recycling participation.
        """)

    st.divider()
    st.subheader("Our Collection Stations")

    station_cols = st.columns(3)

    for i, (station_id, station_name) in enumerate(
        STATIONS.items()
    ):
        with station_cols[i]:
            st.markdown(f"### {station_id}")
            st.write(station_name)
            st.caption("Digital demonstration station")

# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

elif page == "User Registration":

    st.title("Join the EcoLoop Community")

    st.write(
        "Register to participate in waste recovery "
        "and environmental activities."
    )

    with st.form("registration_form"):

        name = st.text_input("Full name")

        email = st.text_input("Email address")

        user_type = st.selectbox(
            "Account type",
            [
                "Individual",
                "School",
                "University",
                "Community Organisation"
            ]
        )

        location = st.text_input(
            "Community or area"
        )

        submitted = st.form_submit_button(
            "Register"
        )

        if submitted:

            if not name.strip() or not email.strip():
                st.error(
                    "Please enter your name and email."
                )

            elif any(
                u["email"].lower() == email.strip().lower()
                for u in st.session_state.users
            ):
                st.warning(
                    "This email is already registered."
                )

            else:
                st.session_state.users.append({
                    "name": name.strip(),
                    "email": email.strip(),
                    "type": user_type,
                    "location": location.strip()
                })

                st.success(
                    f"Welcome to EcoLoop, {name}!"
                )

# --------------------------------------------------
# RECORD WASTE
# --------------------------------------------------

elif page == "Record Waste":

    st.title("Record a Waste Contribution")

    if not st.session_state.users:

        st.warning(
            "Please register a user before recording waste."
        )

    else:

        with st.form("waste_form"):

            selected_user = st.selectbox(
                "Contributor",
                get_user_names()
            )

            material = st.selectbox(
                "Waste material",
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
                "Collection station",
                list(STATIONS.keys())
            )

            submitted = st.form_submit_button(
                "Submit Contribution"
            )

            if submitted:

                record_id = (
                    f"ECO-{len(st.session_state.records) + 1:04d}"
                )

                st.session_state.records.append({
                    "id": record_id,
                    "user": selected_user,
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
                    f"Contribution {record_id} submitted "
                    "for verification."
                )

    st.caption(
        "Contributions remain pending until verified."
    )

# --------------------------------------------------
# STATION QR CODES
# --------------------------------------------------

elif page == "Station QR Codes":

    st.title("EcoLoop Digital Collection Stations")

    st.write(
        "Each demonstration station has a unique QR code "
        "for identification."
    )

    for station_id, station_name in STATIONS.items():

        with st.expander(
            f"{station_id} — {station_name}"
        ):

            qr_image = make_qr(station_id)

            st.image(qr_image, width=190)

            st.download_button(
                label=f"Download {station_id} QR Code",
                data=qr_image.getvalue(),
                file_name=f"{station_id}_QR.png",
                mime="image/png",
                key=f"download_{station_id}"
            )

            st.caption(
                "Demonstration QR code. It identifies the "
                "station but does not yet submit data automatically."
            )

# --------------------------------------------------
# CONTRIBUTION VERIFICATION
# --------------------------------------------------

elif page == "Contribution Verification":

    st.title("Contribution Verification")

    st.warning(
        "Demonstration coordinator interface. "
        "This version does not have secure administrator login."
    )

    pending = [
        r for r in st.session_state.records
        if r["status"] == "Pending"
    ]

    if not pending:

        st.info("There are no pending contributions.")

    else:

        for record in pending:

            with st.container(border=True):

                st.markdown(
                    f"### {record['id']} — {record['user']}"
                )

                st.write(
                    f"Material: {record['material']}"
                )

                st.write(
                    f"Weight: {record['weight']} kg"
                )

                st.write(
                    f"Station: {record['station']}"
                )

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "Approve",
                        key=f"approve_{record['id']}"
                    ):

                        record["status"] = "Approved"
                        record["points"] = (
                            5 + int(record["weight"] * 2)
                        )

                        st.success(
                            "Contribution approved."
                        )
                        st.rerun()

                with col2:

                    if st.button(
                        "Reject",
                        key=f"reject_{record['id']}"
                    ):

                        record["status"] = "Rejected"
                        st.warning(
                            "Contribution rejected."
                        )
                        st.rerun()

# --------------------------------------------------
# LEADERBOARD
# --------------------------------------------------

elif page == "Leaderboard":

    st.title("EcoLoop Community Leaderboard")

    st.write(
        "Recognising participation in waste recovery."
    )

    if not st.session_state.users:

        st.info("No registered users yet.")

    else:

        ranking = []

        for user in st.session_state.users:

            ranking.append({
                "Participant": user["name"],
                "Account Type": user["type"],
                "Approved Waste (kg)": sum(
                    r["weight"]
                    for r in approved_records()
                    if r["user"] == user["name"]
                ),
                "EcoPoints": get_points(user["name"])
            })

        ranking_df = pd.DataFrame(ranking)

        ranking_df = ranking_df.sort_values(
            by="EcoPoints",
            ascending=False
        )

        st.dataframe(
            ranking_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "EcoPoints are demonstration points, "
            "not cash or financial rewards."
        )

# --------------------------------------------------
# COLLECTION MANAGEMENT
# --------------------------------------------------

elif page == "Collection Management":

    st.title("Waste Collection Management")

    approved = approved_records()

    uncollected = [
        r for r in approved
        if r["id"] not in st.session_state.collected
    ]

    st.metric(
        "Approved Waste Awaiting Collection",
        f"{sum(r['weight'] for r in uncollected):.1f} kg"
    )

    if not uncollected:

        st.info(
            "No approved waste is currently awaiting collection."
        )

    else:

        for station_id in STATIONS:

            station_records = [
                r for r in uncollected
                if r["station"] == station_id
            ]

            if station_records:

                st.subheader(
                    f"{station_id} — {STATIONS[station_id]}"
                )

                station_weight = sum(
                    r["weight"] for r in station_records
                )

                st.write(
                    f"Total awaiting collection: "
                    f"{station_weight:.1f} kg"
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

                        st.success(
                            "Collection status updated."
                        )
                        st.rerun()

# --------------------------------------------------
# ENVIRONMENTAL IMPACT
# --------------------------------------------------

elif page == "Environmental Impact":

    st.title("Environmental Impact Tracker")

    approved = approved_records()

    st.write(
        "Explore the amount and types of waste "
        "recorded through the EcoLoop demonstration."
    )

    total = total_weight()

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Approved Waste",
        f"{total:.1f} kg"
    )

    col2.metric(
        "Material Categories",
        len(set(r["material"] for r in approved))
    )

    if approved:

        impact_data = {}

        for record in approved:

            impact_data[record["material"]] = (
                impact_data.get(record["material"], 0)
                + record["weight"]
            )

        impact_df = pd.DataFrame(
            list(impact_data.items()),
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
            "Environmental data will appear when "
            "contributions are approved."
        )

    st.caption(
        "This tracker reports recorded waste quantities. "
        "It does not yet calculate verified carbon savings."
    )

# --------------------------------------------------
# ABOUT
# --------------------------------------------------

elif page == "About EcoLoop":

    st.title("About EcoLoop Node 2.0")

    st.markdown("""
    ### Rethinking Waste Management Through Technology

    EcoLoop Node 2.0 is an environmental technology
    initiative designed to improve waste separation,
    recycling participation and collection coordination.

    ### Our Mission

    To make waste management more accessible,
    organised and data-driven through affordable
    digital technology.

    ### Our Vision

    Communities where waste is recognised as a
    recoverable resource rather than simply a problem.

    ### Current Platform Features

    - Digital user registration
    - Waste contribution recording
    - QR-coded collection station identification
    - Contribution verification
    - Community recycling leaderboard
    - Collection monitoring
    - Environmental data tracking

    ### Future Development

    Future versions aim to explore:

    - ESP32-based smart collection stations
    - Ultrasonic waste-level monitoring
    - Weight sensors
    - AI-assisted waste classification
    - Real-time collection notifications
    - A shared database for multiple users
    - Integration with recycling organisations

    These are planned capabilities, not yet active features.
    """)

    st.divider()

    st.subheader("Developed by")

    st.markdown("**Munashe R. Mutopa**")

    st.write(
        "Designed and Developed by Munashe R. Mutopa"
    )

    st.write(
        "An initiative of Next Gen Impact Hub (NGIH)"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("""
<div class="eco-footer">
    <strong>EcoLoop Node 2.0</strong><br>
    Designed and Developed by Munashe R. Mutopa<br>
    An initiative of Next Gen Impact Hub (NGIH)<br>
    <span class="small-note">
        Building smarter and more sustainable communities.
    </span>
</div>
""", unsafe_allow_html=True)
