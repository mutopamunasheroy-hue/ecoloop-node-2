
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime

# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="EcoLoop Node 2.0",
    page_icon="♻️",
    layout="wide"
)

# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background-color: #f4f8f5;
}
h1, h2, h3 {
    color: #176b45;
}
[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #dce9df;
}
.stButton button {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------

MATERIALS = [
    "Plastic",
    "Paper",
    "Metal",
    "Glass",
    "Organic",
    "Electronic"
]

STATIONS = ["ECO001", "ECO002", "ECO003"]

if "users" not in st.session_state:
    st.session_state.users = []

if "records" not in st.session_state:
    st.session_state.records = []

if "collected" not in st.session_state:
    st.session_state.collected = []

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ---------------- HELPERS ----------------

def approved_records():
    return [
        r for r in st.session_state.records
        if r["status"] == "Approved"
    ]

def total_weight():
    return sum(r["weight"] for r in approved_records())

def make_qr(code):
    qr = qrcode.make(code)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return buffer.getvalue()

# ---------------- SIDEBAR ----------------

st.sidebar.title("♻️ EcoLoop Node")
st.sidebar.caption("Smart Waste Management Platform")

pages = [
    "Home",
    "Register",
    "Record Waste",
    "Verification",
    "Leaderboards",
    "Collection Management",
    "Environmental Impact",
    "About"
]

page = st.sidebar.radio("Navigation", pages)

st.sidebar.divider()

if st.session_state.users:
    names = [u["name"] for u in st.session_state.users]
    selected = st.sidebar.selectbox(
        "Select your profile",
        names
    )
    st.session_state.current_user = selected
else:
    st.sidebar.info("Register a profile to get started.")

# ---------------- HEADER ----------------

st.title("♻️ EcoLoop Node 2.0")
st.caption("Turning waste into opportunity through technology.")

# ---------------- HOME ----------------

if page == "Home":

    st.subheader("Community Recycling Dashboard")

    approved = approved_records()

    users_count = len(st.session_state.users)
    waste_count = len(approved)
    weight = total_weight()

    a, b, c = st.columns(3)

    a.metric("Registered Users", users_count)
    b.metric("Approved Contributions", waste_count)
    c.metric("Waste Recovered", f"{weight:.1f} kg")

    st.divider()

    st.subheader("Waste Categories")

    category_totals = {
        material: sum(
            r["weight"] for r in approved
            if r["material"] == material
        )
        for material in MATERIALS
    }

    df = pd.DataFrame(
        list(category_totals.items()),
        columns=["Material", "Weight (kg)"]
    )

    st.bar_chart(
        df.set_index("Material")
    )

    st.info(
        "This is an early demonstration. "
        "Figures are based on contributions recorded in this session."
    )

# ---------------- REGISTER ----------------

elif page == "Register":

    st.subheader("Create Your EcoLoop Profile")

    with st.form("registration_form"):

        name = st.text_input("Full name or organisation name")

        user_type = st.selectbox(
            "Account type",
            ["Individual", "School", "University", "Organisation"]
        )

        location = st.text_input(
            "Community or area (optional)"
        )

        submitted = st.form_submit_button("Register")

        if submitted:

            if not name.strip():
                st.error("Please enter a name.")

            elif any(
                u["name"].lower() == name.strip().lower()
                for u in st.session_state.users
            ):
                st.warning("This profile already exists.")

            else:
                st.session_state.users.append({
                    "name": name.strip(),
                    "type": user_type,
                    "location": location.strip(),
                    "points": 0
                })

                st.session_state.current_user = name.strip()

                st.success("Your EcoLoop profile has been created!")

# ---------------- RECORD WASTE ----------------

elif page == "Record Waste":

    st.subheader("Record a Waste Contribution")

    if not st.session_state.users:
        st.warning("Please register a profile first.")

    else:

        with st.form("waste_form"):

            material = st.selectbox(
                "Waste category",
                MATERIALS
            )

            weight = st.number_input(
                "Weight in kilograms",
                min_value=0.1,
                max_value=1000.0,
                value=1.0,
                step=0.1
            )

            station = st.selectbox(
                "Collection station",
                STATIONS
            )

            submitted = st.form_submit_button(
                "Submit Contribution"
            )

            if submitted:

                st.session_state.records.append({
                    "user": st.session_state.current_user,
                    "material": material,
                    "weight": float(weight),
                    "station": station,
                    "date": datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "status": "Pending"
                })

                st.success(
                    "Contribution submitted for verification."
                )

    st.divider()

    st.subheader("Station QR Codes")

    columns = st.columns(3)

    for i, station in enumerate(STATIONS):

        with columns[i]:

            st.markdown(f"**{station}**")

            st.image(
                make_qr(station),
                width=130
            )

            st.download_button(
                "Download QR",
                data=make_qr(station),
                file_name=f"{station}.png",
                mime="image/png",
                key=f"qr_{station}"
            )

# ---------------- VERIFICATION ----------------

elif page == "Verification":

    st.subheader("Contribution Verification")
    st.warning(
        "Demonstration coordinator area. "
        "This version does not have secure administrator access."
    )

    pending = [
        (i, r)
        for i, r in enumerate(st.session_state.records)
        if r["status"] == "Pending"
    ]

    if not pending:
        st.info("There are no pending contributions.")

    for index, record in pending:

        with st.container(border=True):

            st.write(f"**Contributor:** {record['user']}")
            st.write(f"**Material:** {record['material']}")
            st.write(f"**Weight:** {record['weight']} kg")
            st.write(f"**Station:** {record['station']}")
            st.write(f"**Date:** {record['date']}")

            col1, col2 = st.columns(2)

            if col1.button(
                "Approve",
                key=f"approve_{index}"
            ):

                record["status"] = "Approved"

                for user in st.session_state.users:
                    if user["name"] == record["user"]:
                        user["points"] += (
                            5 + int(record["weight"] * 2)
                        )

                st.rerun()

            if col2.button(
                "Reject",
                key=f"reject_{index}"
            ):

                record["status"] = "Rejected"
                st.rerun()

# ---------------- LEADERBOARDS ----------------

elif page == "Leaderboards":

    st.subheader("Community Impact Leaderboard")

    if st.session_state.users:

        ranking = sorted(
            st.session_state.users,
            key=lambda u: u["points"],
            reverse=True
        )

        leaderboard = pd.DataFrame([
            {
                "Position": i + 1,
                "Contributor": u["name"],
                "Category": u["type"],
                "Points": u["points"]
            }
            for i, u in enumerate(ranking)
        ])

        st.dataframe(
            leaderboard,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No registered contributors yet.")

# ---------------- COLLECTION MANAGEMENT ----------------

elif page == "Collection Management":

    st.subheader("Collection Station Management")

    approved = approved_records()

    for station in STATIONS:

        station_records = [
            r for r in approved
            if r["station"] == station
            and not r.get("collected", False)
        ]

        station_weight = sum(
            r["weight"] for r in station_records
        )

        with st.container(border=True):

            st.markdown(f"### {station}")

            st.metric(
                "Awaiting collection",
                f"{station_weight:.1f} kg"
            )

            if station_records:

                if st.button(
                    f"Mark {station} as collected",
                    key=f"collect_{station}"
                ):

                    for r in station_records:
                        r["collected"] = True

                    st.session_state.collected.append({
                        "station": station,
                        "weight": station_weight,
                        "date": datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                    })

                    st.success("Collection recorded.")
                    st.rerun()

            else:
                st.caption("No approved waste awaiting collection.")

    st.divider()

    st.subheader("Collection History")

    if st.session_state.collected:

        st.dataframe(
            pd.DataFrame(st.session_state.collected),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No collection history yet.")

# ---------------- ENVIRONMENTAL IMPACT ----------------

elif page == "Environmental Impact":

    st.subheader("Environmental Impact Tracker")

    approved = approved_records()

    total = sum(r["weight"] for r in approved)

    st.metric("Total approved waste", f"{total:.1f} kg")

    impact = {
        material: sum(
            r["weight"] for r in approved
            if r["material"] == material
        )
        for material in MATERIALS
    }

    df = pd.DataFrame(
        list(impact.items()),
        columns=["Material", "Weight (kg)"]
    )

    st.bar_chart(df.set_index("Material"))

    st.caption(
        "These figures show recorded waste weights. "
        "They are not yet estimates of carbon emissions avoided."
    )

    if approved:

        csv = pd.DataFrame(approved).to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download contribution report",
            data=csv,
            file_name="ecoloop_report.csv",
            mime="text/csv"
        )

    else:
        st.info("Approved contributions will appear here.")

# ---------------- ABOUT ----------------

elif page == "About":

    st.subheader("About EcoLoop Node")

    st.write("""
    EcoLoop Node is an initiative by Next Gen Impact Hub (NGIH).

    It aims to improve waste separation, recycling and collection
    coordination through accessible digital technology.

    The platform begins as a software demonstration, with future
    plans to explore sensor-based smart collection stations,
    artificial intelligence and real-world community pilots.
    """)

    st.markdown("### Our focus")

    st.write("""
    - Environmental sustainability
    - Community participation
    - Digital innovation
    - Responsible waste management
    - Youth-led development
    """)

    st.divider()

    st.caption("Developed by Next Gen Impact Hub (NGIH).")

# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "EcoLoop Node 2.0 | A Next Gen Impact Hub (NGIH) initiative"
)
